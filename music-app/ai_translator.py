#!/usr/bin/env python3
"""
ai_translator.py — AI 自动生成英文乐评+文化注释
支持 Gemini / DeepSeek 双 API

用法:
  # Gemini（Win10 上推荐）
  set GEMINI_KEY=你的key
  python ai_translator.py

  # DeepSeek
  set DEEPSEEK_KEY=sk-xxx
  python ai_translator.py --provider deepseek

  # 其他
  python ai_translator.py --dry-run         # 预览不保存
  python ai_translator.py --song "光年之外"  # 单首测试
  python ai_translator.py --limit 5         # 只处理5首
  python ai_translator.py --model gemini-2.0-flash  # 指定模型
"""

import json, os, sys, time, argparse, urllib.request, urllib.error

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


# ═══ Gemini API ═══

def call_gemini(prompt, model="gemini-2.0-flash", api_key=None):
    """Gemini 原生 API — 带智能限速重试"""
    key = api_key or os.environ.get("GEMINI_KEY", "")
    if not key:
        print("      ❌ 未设置 GEMINI_KEY")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = json.dumps({
        "systemInstruction": {
            "parts": [{"text": SYSTEM}]
        },
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2500
        }
    }).encode("utf-8")

    max_attempts = 6  # 更多重试
    for attempt in range(max_attempts):
        try:
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json"
            })
            resp = urllib.request.urlopen(req, timeout=60)
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            err = e.read().decode() if e.fp else str(e)
            code = e.code if hasattr(e, 'code') else 0
            if "429" in str(code) or "RESOURCE_EXHAUSTED" in err:
                # 指数退避: 15s, 30s, 60s, 90s...
                wait = min(15 * (2 ** attempt), 120)
                print(f"      ⏳ 限速，等{wait}s...", end="", flush=True)
                time.sleep(wait)
                continue
            if "403" in str(code) or "PERMISSION_DENIED" in err:
                print(f"\n      ❌ API Key 无效或权限不足")
                return None
            if attempt < max_attempts - 1:
                wait = (attempt + 1) * 5
                print(f"      ⚠️ HTTP {code}，{wait}s后重试...", end="", flush=True)
                time.sleep(wait)
            else:
                print(f"\n      ❌ HTTP {code}: {err[:150]}")
                return None
        except Exception as e:
            if attempt < max_attempts - 1:
                wait = (attempt + 1) * 5
                print(f"      ⚠️ 网络错误，{wait}s重试...", end="", flush=True)
                time.sleep(wait)
            else:
                print(f"\n      ❌ 最终失败: {e}")
                return None
    return None


# ═══ DeepSeek API ═══

def call_deepseek(prompt, model="deepseek-chat", api_key=None):
    """DeepSeek API（OpenAI 兼容）"""
    key = api_key or os.environ.get("DEEPSEEK_KEY", "")
    if not key:
        print("      ❌ 未设置 DEEPSEEK_KEY")
        return None

    url = "https://api.deepseek.com/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2500
    }).encode("utf-8")

    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}"
            })
            resp = urllib.request.urlopen(req, timeout=60)
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            err = e.read().decode() if e.fp else str(e)
            if "rate_limit" in err.lower() or "429" in str(e.code):
                wait = (attempt + 1) * 8
                print(f"      ⏳ 限速，等{wait}s...", end="", flush=True)
                time.sleep(wait)
                continue
            print(f"\n      ❌ HTTP {e.code}: {err[:200]}")
            return None
        except Exception as e:
            print(f"\n      ❌ 网络错误: {e}")
            return None
    return None


# ═══ 内容生成 ═══

def generate(song, provider="gemini", model=None, api_key=None):
    """为单首歌生成英文乐评+文化注释"""
    title = song.get("title", "")
    artist = song.get("artist", "")
    genre = song.get("genre", "")
    year = song.get("year", "")
    lang = song.get("language", "zh")
    lyrics = (song.get("lyrics_original") or "")[:300]

    if lang == "en":
        prompt = f"""Write a 150-200 word English review of this English song for a global music discovery site.

Song: {title} by {artist}
Genre: {genre} | Year: {year}
First few lyrics:
{lyrics}

Return exactly:
REVIEW:[English review]
TAGS:[tag1, tag2, tag3]"""
    else:
        prompt = f"""Write a 150-250 word English review of this Chinese song for a global audience. Explain what it means, why it matters culturally, and what non-Chinese speakers should listen for.

Song: {title} ({artist})
Genre: {genre} | Year: {year}
First few lyrics (Chinese):
{lyrics}

Return exactly:
REVIEW:[English review — 150-250 words, explain meaning, emotional tone, place in Chinese music]
CULTURE:[1-2 sentence cultural note explaining unique Chinese elements foreigners might miss]
TAGS:[tag1, tag2, tag3]"""

    # 调用 API
    if provider == "gemini":
        result = call_gemini(prompt, model=model or "gemini-2.0-flash", api_key=api_key)
    else:
        result = call_deepseek(prompt, model=model or "deepseek-chat", api_key=api_key)

    if not result:
        return None

    review = culture = ""
    tags = []
    current_section = None
    lines = result.split("\n")

    for line in lines:
        stripped = line.strip()
        upper = stripped.upper()

        # 检测新的section标题
        if upper.startswith("REVIEW"):
            current_section = "review"
            # 取冒号后的内容（可能在这行也可能在下一行）
            after = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            if after:
                review = after
            continue
        elif upper.startswith("CULTURE"):
            current_section = "culture"
            after = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            if after:
                culture = after
            continue
        elif upper.startswith("TAGS"):
            current_section = "tags"
            after = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            if after:
                tags = [t.strip() for t in after.split(",") if t.strip()]
            continue

        # 追加到当前section
        if current_section == "review":
            review += (" " + stripped) if review else stripped
        elif current_section == "culture":
            culture += (" " + stripped) if culture else stripped
        elif current_section == "tags" and stripped:
            tags.extend([t.strip() for t in stripped.replace("，", ",").split(",") if t.strip()])

    return {"review_en": review, "cultural_note": culture, "tags": tags}


# ═══ 批量处理 ═══

def process_all(provider="gemini", model=None, dry_run=False, limit=0, api_key=None):
    songs = load()
    todo = [s for s in songs if not s.get("review_en") or len(s.get("review_en", "")) < 60]

    if not todo:
        print("✅ 所有歌都有英文乐评")
        return

    if limit:
        todo = todo[:limit]

    provider_name = {"gemini": "Gemini", "deepseek": "DeepSeek"}.get(provider, provider)
    print(f"📝 {len(todo)} 首缺乐评 → {provider_name}\n")

    done = 0
    t0 = time.time()

    for i, s in enumerate(todo):
        print(f"[{i+1}/{len(todo)}] {s['artist']} — {s['title']}")
        r = generate(s, provider=provider, model=model, api_key=api_key)
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
            print(f"      ❌ 失败，跳过（不影响后续）")

        # 每首立即保存，防止中断丢失
        if not dry_run:
            save(songs)

        # Gemini 免费版限速很严：15 RPM = 1首/4秒，但实际经常429
        # 用更保守的间隔：7秒/首 ≈ 8-9 RPM
        if provider == "gemini":
            wait = 7
            print(f"      💤 等{wait}s（防止限速）...")
            time.sleep(wait)
        else:
            time.sleep(1.5)

    if not dry_run:
        save(songs)

    elapsed = int(time.time() - t0)
    print(f"\n🎉 完成 ({elapsed}s): {done}/{len(todo)}")


# ═══ 主入口 ═══

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="AI 生成英文乐评+文化注释")
    p.add_argument("--provider", choices=["gemini", "deepseek"], default="deepseek",
                   help="API 提供商 (默认 gemini)")
    p.add_argument("--model", help="模型名 (默认 gemini-2.0-flash / deepseek-chat)")
    p.add_argument("--key", help="API key（也可用环境变量 GEMINI_KEY / DEEPSEEK_KEY）")
    p.add_argument("--dry-run", action="store_true", help="预览不保存")
    p.add_argument("--song", type=str, help="单首测试")
    p.add_argument("--limit", type=int, default=0, help="限制处理数量")
    args = p.parse_args()

    # 自动检测可用的 API key（命令行 > 环境变量 > 内置key）
    api_key = args.key
    if not api_key:
        if args.provider == "gemini":
            api_key = os.environ.get("GEMINI_KEY", "")
        else:
            api_key = os.environ.get("DEEPSEEK_KEY", "")

    if not api_key:
        if args.provider == "gemini":
            print("❌ 未设置 GEMINI_KEY")
        else:
            print("❌ 未设置 DEEPSEEK_KEY\n   注册: https://platform.deepseek.com/")
        sys.exit(1)

    if args.song:
        songs = load()
        s = next((x for x in songs if args.song in x.get("title", "")), None)
        if not s:
            print(f"未找到: {args.song}")
            sys.exit(1)
        r = generate(s, provider=args.provider, model=args.model, api_key=api_key)
        if r:
            s.update(r)
            if not args.dry_run:
                save(songs)
            print(f"\n🎵 {s['artist']} — {s['title']}")
            print(f"\n📝 乐评:\n{r['review_en']}")
            if r.get("cultural_note"):
                print(f"\n🏮 文化注释:\n{r['cultural_note']}")
            if r.get("tags"):
                print(f"\n🏷️ 标签: {', '.join(r['tags'])}")
        else:
            print("❌ 生成失败")
    else:
        process_all(provider=args.provider, model=args.model,
                    dry_run=args.dry_run, limit=args.limit, api_key=api_key)
