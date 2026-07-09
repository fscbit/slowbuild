#!/usr/bin/env python3
"""
ai_translator.py — AI 自动补全英文乐评+文化注释（歌词保持中文原文）
接 DeepSeek API: https://platform.deepseek.com/

用法:
  set DEEPSEEK_KEY=sk-xxx
  python ai_translator.py              # 批量补全缺少乐评的歌
  python ai_translator.py --dry-run    # 预览不保存
  python ai_translator.py --song "光年之外"  # 单首
"""

import json, os, sys, time, argparse, urllib.request, urllib.error

API_KEY = os.environ.get("DEEPSEEK_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"
SONGS_FILE = os.path.join(os.path.dirname(__file__), "data", "songs.json")

SYSTEM = """You are an English-language music critic specializing in Chinese music for a global audience.
Your readers are foreigners discovering Chinese songs. They see the original Chinese lyrics and need YOU to explain what the song means, why it matters, and what cultural context they're missing.

Rules:
- Write in natural, engaging English (150-250 words)
- Assume readers don't speak Chinese but ARE seeing the Chinese lyrics
- Explain metaphors, wordplay, cultural references
- Place the song in its era/genre context
- Keep cultural notes to 1-2 sentences
- NEVER translate the full lyrics — just reference key phrases
- Output format must be exact"""

def load():
    with open(SONGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save(songs):
    with open(SONGS_FILE, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)


def call_api(prompt, model="deepseek-chat"):
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7, "max_tokens": 2500
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
                wait = (attempt + 1) * 8
                print(f"      ⏳ 限速，等{wait}s...", end="", flush=True)
                time.sleep(wait)
                continue
            print(f"\n      ❌ HTTP {e.code}: {err[:120]}")
            return None
        except Exception as e:
            print(f"\n      ❌ 网络错误: {e}")
            return None
    return None


def generate(song):
    """为单首歌生成英文乐评+文化注释"""
    title = song.get("title", "")
    artist = song.get("artist", "")
    genre = song.get("genre", "")
    year = song.get("year", "")
    lang = song.get("language", "zh")
    lyrics = (song.get("lyrics_original") or "")[:300]
    existing = (song.get("review_en") or "")[:100]

    if lang == "en":
        # 英文歌 — 已经是英文内容
        prompt = f"""Write a 150-200 word English review of this English song for a global music discovery site.

Song: {title} by {artist}
Genre: {genre} | Year: {year}
First few lyrics:
{lyrics}

Return exactly:
REVIEW:[English review]
TAGS:[tag1, tag2, tag3]"""
    else:
        prompt = f"""Write a 150-250 word English review of this Chinese song. Explain what it means, why it matters culturally, and what non-Chinese speakers should listen for.

Song: {title} ({artist})
Genre: {genre} | Year: {year}
First few lyrics (Chinese):
{lyrics}

Return exactly:
REVIEW:[English review — 150-250 words, explain the song's meaning, emotional tone, and place in Chinese music]
CULTURE:[1-2 sentence cultural note explaining unique Chinese elements foreigners might miss]
TAGS:[tag1, tag2, tag3]"""

    result = call_api(prompt)
    if not result:
        return None

    review = culture = ""
    tags = []

    for line in result.split("\n"):
        line = line.strip()
        if line.upper().startswith("REVIEW:"):
            review = line.split("REVIEW:", 1)[1].strip()
        elif line.upper().startswith("CULTURE:"):
            culture = line.split("CULTURE:", 1)[1].strip()
        elif line.upper().startswith("TAGS:"):
            tags = [t.strip() for t in line.split("TAGS:", 1)[1].split(",")] if "TAGS:" in line.upper() else []
            tags = [t for t in tags if t]

    return {"review_en": review, "cultural_note": culture, "tags": tags}


def process_all(dry_run=False, limit=0):
    if not API_KEY:
        print("❌ set DEEPSEEK_KEY=sk-xxx")
        print("   注册: https://platform.deepseek.com/")
        return

    songs = load()
    todo = [s for s in songs if not s.get("review_en") or len(s.get("review_en", "")) < 60]

    if not todo:
        print("✅ 所有歌都有英文乐评")
        return

    if limit:
        todo = todo[:limit]

    print(f"📝 {len(todo)} 首缺乐评\n")
    done = 0

    for i, s in enumerate(todo):
        print(f"[{i+1}/{len(todo)}] {s['artist']} — {s['title']}")
        r = generate(s)
        if r:
            s["review_en"] = r["review_en"]
            if r.get("cultural_note"):
                s["cultural_note"] = r["cultural_note"]
            if r.get("tags"):
                existing = set(s.get("tags", []))
                existing.update(r["tags"])
                s["tags"] = list(existing)
            done += 1
            print(f"      ✅ {len(r['review_en'])}字乐评")
        else:
            print(f"      ❌ 失败")

        if (i + 1) % 3 == 0 and not dry_run:
            save(songs)
            print(f"  ═══ 已保存 ═══")
        time.sleep(1.5)

    if not dry_run:
        save(songs)
    print(f"\n🎉 完成: {done}/{len(todo)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="AI 生成英文乐评+文化注释")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--song", type=str)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--model", default="deepseek-chat")
    args = p.parse_args()

    if not API_KEY:
        print("❌ set DEEPSEEK_KEY=sk-xxx\n   https://platform.deepseek.com/")
        sys.exit(1)

    if args.song:
        songs = load()
        s = next((x for x in songs if x["title"] == args.song), None)
        if not s:
            print(f"未找到: {args.song}")
            sys.exit(1)
        r = generate(s)
        if r:
            s.update(r)
            if not args.dry_run:
                save(songs)
            print(f"\n乐评:\n{r['review_en']}")
            if r.get("cultural_note"):
                print(f"\n文化注释:\n{r['cultural_note']}")
        else:
            print("生成失败")
    else:
        process_all(args.dry_run, args.limit)
