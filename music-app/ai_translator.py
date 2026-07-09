#!/usr/bin/env python3
"""
ai_translator.py — AI 批量翻译中文歌词、生成英文乐评
需要 DeepSeek API Key: https://platform.deepseek.com/

用法:
  set DEEPSEEK_KEY=sk-xxx              # 设置API Key
  python ai_translator.py              # 批量翻译所有缺歌词翻译的歌
  python ai_translator.py --dry-run    # 只预览不保存
  python ai_translator.py --song 光年之外  # 单首处理
  python ai_translator.py --review-only     # 只生成乐评，不动歌词

模型选择:
  默认 deepseek-chat (¥1/百万token，性价比高)
  --model deepseek-reasoner 精度更高但慢
"""

import json
import os
import sys
import time
import argparse
import urllib.request
import urllib.error

API_KEY = os.environ.get("DEEPSEEK_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
SONGS_FILE = os.path.join(os.path.dirname(__file__), "data", "songs.json")


def load_songs():
    with open(SONGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_songs(songs):
    with open(SONGS_FILE, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)


def call_deepseek(prompt, model=None):
    """调用 DeepSeek API，返回文本响应"""
    model = model or MODEL
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a bilingual Chinese-English music critic and translator. You create elegant, poetic English translations of Chinese song lyrics that preserve meaning, imagery, and emotional tone. You also write insightful English reviews that help foreigners understand the cultural context and artistic value of Chinese songs. Be concise but vivid."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 3000
    }).encode("utf-8")

    req = urllib.request.Request(API_URL, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    })

    for attempt in range(3):
        try:
            resp = urllib.request.urlopen(req, timeout=60)
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            if "rate_limit" in err.lower() or "429" in str(e.code):
                wait = (attempt + 1) * 10
                print(f"      ⏳ 限速，等{wait}秒…", end="", flush=True)
                time.sleep(wait)
                continue
            print(f"\n      ❌ API错误 {e.code}: {err[:150]}")
            return None
        except Exception as e:
            print(f"\n      ❌ 网络错误: {e}")
            return None
    return None


def translate_lyrics(title, artist, original_lyrics):
    """AI 翻译歌词"""
    prompt = f"""Translate these Chinese song lyrics into poetic, singable English.
Keep the line structure. Focus on emotional meaning over literal translation.

Song: {title} by {artist}

Chinese lyrics:
{original_lyrics}

Return ONLY the English translation, no explanations:"""

    result = call_deepseek(prompt)
    return result.strip() if result else None


def generate_review(title, artist, genre="", lyrics_en="", year=""):
    """AI 生成英文乐评"""
    prompt = f"""Write a 150-250 word English review of this Chinese song for foreigners discovering Chinese music.
Include: what makes it special, its place in Chinese music history, the artist's style, what emotions it conveys.
Write in natural, engaging English.

Song: {title} (Chinese: {title})
Artist: {artist}
Genre: {genre}
Year: {year}

Lyrics (English translation):
{lyrics_en[:500] if lyrics_en else "Not available"}

Return in this format:
REVIEW:[your English review]
CULTURE:[one-sentence cultural note explaining any uniquely Chinese elements]
TITLE_EN:[natural English title for the song]
TAGS:[tag1, tag2, tag3]"""

    result = call_deepseek(prompt)
    if not result:
        return None

    review = ""
    culture = ""
    title_en = ""
    tags = []

    for line in result.split("\n"):
        line = line.strip()
        if line.upper().startswith("REVIEW:"):
            review = line.split("REVIEW:", 1)[1].strip()
        elif line.upper().startswith("CULTURE:"):
            culture = line.split("CULTURE:", 1)[1].strip()
        elif line.upper().startswith("TITLE_EN:"):
            title_en = line.split("TITLE_EN:", 1)[1].strip()
        elif line.upper().startswith("TAGS:"):
            tags = [t.strip() for t in line.split("TAGS:", 1)[1].split(",") if t.strip()]

    return {
        "review_en": review,
        "cultural_note": culture,
        "title_en": title_en,
        "tags": tags
    }


def process_song(song, dry_run=False, review_only=False):
    """处理单首歌"""
    title = song.get("title", "")
    artist = song.get("artist", "")
    genre = song.get("genre", "")
    year = song.get("year", "")
    original_lyrics = song.get("lyrics_original", "")

    print(f"\n  🎵 {artist} — {title}")

    # 如果需要歌词翻译
    if not review_only and original_lyrics and not song.get("lyrics_translation_en"):
        print("     → 翻译歌词…")
        translated = translate_lyrics(title, artist, original_lyrics)
        if translated:
            song["lyrics_translation_en"] = translated
            print(f"     ✅ 歌词翻译完成 ({len(translated)}字)")
        time.sleep(1)

    # 如果没有英文乐评
    if not song.get("review_en") or len(song.get("review_en", "")) < 60:
        lyrics_en = song.get("lyrics_translation_en", "")
        print("     → 生成乐评…")
        review = generate_review(title, artist, genre, lyrics_en, year)
        if review:
            song["review_en"] = review.get("review_en", "")
            if review.get("cultural_note"):
                song["cultural_note"] = review["cultural_note"]
            if review.get("title_en") and not song.get("title_en"):
                song["title_en"] = review["title_en"]
            if review.get("tags"):
                existing = set(song.get("tags", []))
                existing.update(review["tags"])
                song["tags"] = list(existing)
            print(f"     ✅ 乐评完成 ({len(song['review_en'])}字)")

    return song


def process_all(dry_run=False, review_only=False, limit=0):
    if not API_KEY:
        print("❌ 请先设置 DEEPSEEK_KEY 环境变量")
        print("   set DEEPSEEK_KEY=sk-xxx")
        print("   去 https://platform.deepseek.com/ 注册获取")
        return

    songs = load_songs()
    todo = []

    for s in songs:
        needs_lyrics = not review_only and s.get("lyrics_original") and not s.get("lyrics_translation_en")
        needs_review = not s.get("review_en") or len(s.get("review_en", "")) < 60
        if needs_lyrics or needs_review:
            todo.append(s)

    if not todo:
        print("✅ 所有歌曲都已有翻译和乐评")
        return

    if limit and limit < len(todo):
        todo = todo[:limit]

    print(f"共 {len(todo)} 首需要处理\n")

    for i, s in enumerate(todo):
        print(f"[{i+1}/{len(todo)}]", end="")
        process_song(s, dry_run, review_only)
        if not dry_run and (i + 1) % 3 == 0:
            save_songs(songs)
            print(f"  --- 已保存 ---")
        time.sleep(1.5)

    if not dry_run:
        save_songs(songs)
        print(f"\n🎉 全部完成并保存！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI 批量翻译中文歌词/生成英文乐评")
    parser.add_argument("--dry-run", action="store_true", help="只预览不保存")
    parser.add_argument("--review-only", action="store_true", help="只生成乐评不翻译歌词")
    parser.add_argument("--song", type=str, help="处理单首歌（在songs.json中存在的歌名）")
    parser.add_argument("--limit", type=int, default=0, help="限制处理数量（测试用）")
    parser.add_argument("--model", type=str, default="deepseek-chat")
    args = parser.parse_args()

    MODEL = args.model

    if not API_KEY:
        print("❌ 请先设置 DEEPSEEK_KEY: set DEEPSEEK_KEY=sk-xxx")
        print("   注册: https://platform.deepseek.com/")
        sys.exit(1)

    if args.song:
        songs = load_songs()
        s = next((x for x in songs if x["title"] == args.song), None)
        if not s:
            print(f"未找到歌曲: {args.song}")
            sys.exit(1)
        process_song(s, args.dry_run, args.review_only)
        if not args.dry_run:
            save_songs(songs)
            print("✅ 已保存")
    else:
        process_all(args.dry_run, args.review_only, args.limit)
