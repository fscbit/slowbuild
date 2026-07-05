#!/usr/bin/env python3
"""
music.slowbuild.top — 中国歌曲英文解读站
端口 5003 | Flask + JSON 数据
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify
from functools import wraps
import json, os, re, hashlib
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
DATA_FILE = Path(__file__).parent / "data" / "songs.json"
ADMIN_PASSWORD = "slowbuild2026"  # 简单保护，改掉
TEMPLATE_DIR = Path(__file__).parent / "templates"

# ═══════════════════════════════════════════
# 数据读写
# ═══════════════════════════════════════════

def load_songs():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except:
        return []

def save_songs(songs):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(songs, ensure_ascii=False, indent=2), encoding="utf-8")

def get_genres(songs):
    genres = set()
    for s in songs:
        g = s.get("genre", "").strip().lower()
        if g:
            genres.add(g)
    return sorted(genres)

# ═══════════════════════════════════════════
# 公开页面
# ═══════════════════════════════════════════

@app.route("/")
def index():
    songs = load_songs()
    genre = request.args.get("genre", "").strip().lower()
    if genre:
        songs = [s for s in songs if s.get("genre", "").lower() == genre]
    # 最新在前
    songs.sort(key=lambda s: s.get("added", ""), reverse=True)
    genres = get_genres(load_songs())
    return render_template("home.html", songs=songs, genres=genres, current_genre=genre)

@app.route("/song/<song_id>")
def song_detail(song_id):
    songs = load_songs()
    song = next((s for s in songs if s.get("id") == song_id), None)
    if not song:
        return "Song not found", 404
    # 找相关歌曲（同类型或同艺人）
    related = [s for s in songs
               if s.get("id") != song_id
               and (s.get("genre") == song.get("genre") or s.get("artist") == song.get("artist"))
              ][:3]
    return render_template("song.html", song=song, related=related)

@app.route("/api/songs")
def api_songs():
    songs = load_songs()
    q = request.args.get("q", "").strip().lower()
    if q:
        songs = [s for s in songs if q in s.get("title","").lower()
                 or q in s.get("artist","").lower()
                 or q in s.get("review_en","").lower()]
    return jsonify(songs[:20])

# ═══════════════════════════════════════════
# 管理员（简单密码保护）
# ═══════════════════════════════════════════

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.cookies.get("music_admin")
        expected = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
        if auth != expected:
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            resp = redirect(url_for("admin"))
            resp.set_cookie("music_admin",
                           hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest(),
                           max_age=86400*30)
            return resp
        return render_template("login.html", error="Wrong password")
    return render_template("login.html")

@app.route("/admin")
@admin_required
def admin():
    songs = load_songs()
    songs.sort(key=lambda s: s.get("added", ""), reverse=True)
    return render_template("admin.html", songs=songs)

@app.route("/admin/add", methods=["POST"])
@admin_required
def admin_add():
    songs = load_songs()
    title = request.form.get("title", "").strip()
    artist = request.form.get("artist", "").strip()
    if not title or not artist:
        return redirect(url_for("admin"))
    
    song_id = "song-" + re.sub(r'[^a-z0-9-]', '', title.lower().replace(" ", "-"))[:30]
    # 去重
    if any(s.get("id") == song_id for s in songs):
        song_id += "-" + str(len(songs))
    
    song = {
        "id": song_id,
        "title": title,
        "artist": artist,
        "genre": request.form.get("genre", "").strip().lower(),
        "year": request.form.get("year", "").strip(),
        "cover": request.form.get("cover", "").strip(),
        "spotify_id": request.form.get("spotify_id", "").strip(),
        "youtube_id": request.form.get("youtube_id", "").strip(),
        "netease_id": request.form.get("netease_id", "").strip(),
        "review_en": request.form.get("review_en", "").strip(),
        "review_cn": request.form.get("review_cn", "").strip(),
        "lyrics_original": request.form.get("lyrics_original", "").strip(),
        "lyrics_translation_en": request.form.get("lyrics_translation_en", "").strip(),
        "lyrics_translation_cn_note": request.form.get("lyrics_translation_cn_note", "").strip(),
        "cultural_note": request.form.get("cultural_note", "").strip(),
        "tags": [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()],
        "added": datetime.now().strftime("%Y-%m-%d"),
        "language": request.form.get("language", "zh").strip(),
    }
    songs.append(song)
    save_songs(songs)
    return redirect(url_for("admin"))

@app.route("/admin/edit/<song_id>", methods=["POST"])
@admin_required
def admin_edit(song_id):
    songs = load_songs()
    for s in songs:
        if s.get("id") == song_id:
            s["title"] = request.form.get("title", s["title"])
            s["artist"] = request.form.get("artist", s["artist"])
            s["genre"] = request.form.get("genre", s.get("genre",""))
            s["year"] = request.form.get("year", s.get("year",""))
            s["cover"] = request.form.get("cover", s.get("cover",""))
            s["spotify_id"] = request.form.get("spotify_id", s.get("spotify_id",""))
            s["youtube_id"] = request.form.get("youtube_id", s.get("youtube_id",""))
            s["netease_id"] = request.form.get("netease_id", s.get("netease_id",""))
            s["review_en"] = request.form.get("review_en", s.get("review_en",""))
            s["review_cn"] = request.form.get("review_cn", s.get("review_cn",""))
            s["lyrics_original"] = request.form.get("lyrics_original", s.get("lyrics_original",""))
            s["lyrics_translation_en"] = request.form.get("lyrics_translation_en", s.get("lyrics_translation_en",""))
            s["cultural_note"] = request.form.get("cultural_note", s.get("cultural_note",""))
            s["tags"] = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
            s["language"] = request.form.get("language", s.get("language",""))
            break
    save_songs(songs)
    return redirect(url_for("admin"))

@app.route("/admin/delete/<song_id>", methods=["POST"])
@admin_required
def admin_delete(song_id):
    songs = load_songs()
    songs = [s for s in songs if s.get("id") != song_id]
    save_songs(songs)
    return redirect(url_for("admin"))

# ═══════════════════════════════════════════
# 启动
# ═══════════════════════════════════════════

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5003))
    print(f"🎵 music.slowbuild.top 启动")
    print(f"   端口: {PORT}")
    print(f"   管理后台: /admin (密码: {ADMIN_PASSWORD})")
    app.run(host="0.0.0.0", port=PORT, debug=False)
