#!/usr/bin/env python3
"""
music.slowbuild.top — 中国歌曲英文解读站（优化版）
端口 5003 | Flask + JSON 数据 | YouTube 播放

优化点（2026-08-20）：
1. load_songs 加内存缓存（文件 mtime 变化才重读），解决每次请求都读 200KB+ JSON 的问题
2. index() 补全 home.html 需要的分组变量（featured/global_hits/deep_cuts/genre_groups/genre_labels/others）
3. gzip 压缩响应（HTML/JSON/XML 传输体积大幅减小）
4. 修复 index() 里重复 load_songs 的问题
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from functools import wraps
import json, os, re, hashlib, gzip
from io import BytesIO
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
DATA_FILE = Path(__file__).parent / "data" / "songs.json"
ADMIN_PASSWORD = "slowbuild2026"
TEMPLATE_DIR = Path(__file__).parent / "templates"

# ═══════════════════════════════════════════
# 数据读写（带内存缓存）
# ═══════════════════════════════════════════

_cache = {"mtime": None, "songs": None}

def load_songs():
    """带缓存的歌曲加载：文件 mtime 没变就直接用内存数据，不再每次读盘 + 解析"""
    try:
        mtime = DATA_FILE.stat().st_mtime
    except OSError:
        return []
    if _cache["mtime"] == mtime and _cache["songs"] is not None:
        return _cache["songs"]
    try:
        songs = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        songs = []
    _cache["mtime"] = mtime
    _cache["songs"] = songs
    return songs

def save_songs(songs):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(songs, ensure_ascii=False, indent=2), encoding="utf-8")
    # 同步更新缓存，避免下次请求又读盘
    try:
        _cache["mtime"] = DATA_FILE.stat().st_mtime
    except OSError:
        pass
    _cache["songs"] = songs

def get_genres(songs):
    genres = set()
    for s in songs:
        g = s.get("genre", "").strip().lower()
        if g:
            genres.add(g)
    return sorted(genres)


# genre 英文标签（home.html 展示用）
GENRE_LABELS = {
    "pop": "Mandopop Essentials",
    "rock": "Rock & Roll",
    "folk": "Folk & Ballads",
    "indie": "Indie & Alternative",
    "hiphop": "Hip-Hop & Rap",
    "punk": "Punk",
    "electronic": "Electronic",
    "jazz": "Jazz",
    "rnb": "R&B",
    "ballad": "Ballads",
    "ost": "Soundtracks",
    "cantopop": "Cantopop",
}


# ═══════════════════════════════════════════
# 公开页面
# ═══════════════════════════════════════════

@app.route("/")
def index():
    songs = load_songs()
    genre = request.args.get("genre", "").strip().lower()

    # —— 分组（每首歌按优先级进入一个区块，避免首页重复）——
    featured = [s for s in songs if s.get("featured")]
    global_hits = [s for s in songs if s.get("global_tier") in (1, 2, 3)]
    global_hits.sort(key=lambda s: s.get("global_tier", 0))
    deep_cuts = [s for s in songs
                 if not s.get("featured") and s.get("global_tier") in (0, None)][:24]

    genre_groups = {}
    for s in songs:
        g = s.get("genre", "").strip().lower()
        if g:
            genre_groups.setdefault(g, []).append(s)
    for g in genre_groups:
        genre_groups[g].sort(key=lambda s: (s.get("featured", False), s.get("sort_order", 0)), reverse=True)

    others = [s for s in songs if not s.get("genre") and not s.get("featured")
              and s.get("global_tier") in (0, None)][:24]

    if genre:
        songs = [s for s in songs if s.get("genre", "").lower() == genre]

    genres = get_genres(load_songs())
    return render_template(
        "home.html",
        songs=songs, genres=genres, current_genre=genre,
        featured=featured, global_hits=global_hits, deep_cuts=deep_cuts,
        genre_groups=genre_groups, genre_labels=GENRE_LABELS, others=others,
    )


@app.route("/song/<song_id>")
def song_detail(song_id):
    songs = load_songs()
    song = next((s for s in songs if s.get("id") == song_id), None)
    if not song:
        return "Song not found", 404
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
# 管理员
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
    songs.sort(key=lambda s: (s.get("featured", False), s.get("sort_order", 0)), reverse=True)
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
    if any(s.get("id") == song_id for s in songs):
        song_id += "-" + str(len(songs))

    song = {
        "id": song_id,
        "title": title,
        "title_en": request.form.get("title_en", "").strip(),
        "artist": artist,
        "genre": request.form.get("genre", "").strip().lower(),
        "year": request.form.get("year", "").strip(),
        "cover": request.form.get("cover", "").strip(),
        "spotify_id": request.form.get("spotify_id", "").strip(),
        "youtube_id": request.form.get("youtube_id", "").strip(),
        "netease_id": request.form.get("netease_id", "").strip(),
        "direct_audio_url": request.form.get("direct_audio_url", "").strip(),
        "review_en": request.form.get("review_en", "").strip(),
        "review_cn": request.form.get("review_cn", "").strip(),
        "lyrics_original": request.form.get("lyrics_original", "").strip(),
        "lyrics_translation_en": request.form.get("lyrics_translation_en", "").strip(),
        "lyrics_translation_cn_note": request.form.get("lyrics_translation_cn_note", "").strip(),
        "cultural_note": request.form.get("cultural_note", "").strip(),
        "tags": [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()],
        "added": datetime.now().strftime("%Y-%m-%d"),
        "language": request.form.get("language", "zh").strip(),
        "featured": request.form.get("featured") == "true",
        "premium": request.form.get("premium") == "true",
        "sort_order": int(request.form.get("sort_order", "0") or "0"),
    }
    songs.append(song)
    save_songs(songs)
    return redirect(url_for("admin"))


@app.route("/admin/edit/<song_id>", methods=["POST"])
@admin_required
def admin_edit(song_id):
    editable = ["title","artist","title_en","genre","year","cover","spotify_id","youtube_id",
                "netease_id","direct_audio_url","review_en","review_cn",
                "lyrics_original","lyrics_translation_en","lyrics_translation_cn_note",
                "cultural_note","language"]
    songs = load_songs()
    for s in songs:
        if s.get("id") == song_id:
            for key in editable:
                if key in request.form:
                    s[key] = request.form.get(key, s.get(key,""))
            tags_val = request.form.get("tags", "")
            s["tags"] = [t.strip() for t in tags_val.split(",") if t.strip()] if tags_val else s.get("tags",[])
            s["featured"] = request.form.get("featured") == "true"
            s["premium"] = request.form.get("premium") == "true"
            s["sort_order"] = int(request.form.get("sort_order", "0") or "0")
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
# gzip 压缩（HTML/JSON/XML 传输体积大幅减小）
# ═══════════════════════════════════════════

COMPRESSIBLE = ("text/", "application/json", "application/xml", "application/javascript", "text/javascript")

@app.after_request
def compress_response(response):
    accept = request.headers.get("Accept-Encoding", "")
    ct = response.content_type or ""
    if response.status_code == 200 and "gzip" in accept.lower() and any(ct.startswith(c) for c in COMPRESSIBLE):
        if len(response.get_data()) > 500:  # 小响应不值得压
            buf = BytesIO()
            with gzip.GzipFile(mode="wb", fileobj=buf, compresslevel=6) as f:
                f.write(response.get_data())
            response.set_data(buf.getvalue())
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Content-Length"] = len(response.get_data())
            response.headers["Vary"] = "Accept-Encoding"
    return response


# ═══════════════════════════════════════════
# SEO & robots
# ═══════════════════════════════════════════

@app.route("/robots.txt")
def robots_txt():
    return """User-agent: *
Allow: /
Sitemap: https://music.slowbuild.top/sitemap.xml
""", 200, {"Content-Type": "text/plain"}


@app.route("/sitemap.xml")
def sitemap_xml():
    songs = load_songs()
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += '  <url><loc>https://music.slowbuild.top/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>\n'
    for s in songs:
        xml += f'  <url><loc>https://music.slowbuild.top/song/{s["id"]}</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>\n'
    xml += '</urlset>'
    return xml, 200, {"Content-Type": "application/xml"}


# ═══════════════════════════════════════════
# 启动
# ═══════════════════════════════════════════

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5003))
    print(f"🎵 music.slowbuild.top 启动（优化版）")
    print(f"   端口: {PORT}")
    print(f"   管理后台: /admin (密码: {ADMIN_PASSWORD})")
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
