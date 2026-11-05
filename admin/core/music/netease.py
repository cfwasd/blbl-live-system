import httpx
import re
import urllib.parse
from typing import Optional, Dict, Any, List

NETEASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://music.163.com/",
    "Accept": "application/json, text/plain, */*",
}

DEFAULT_ANIME_PLAYLIST_ID = 3778678  # 官方热门推荐歌单

def clean_song_query(query: str) -> str:
    """去除指令前缀与包裹符号，提取纯净歌曲名"""
    q = query.strip()
    # 移除“点歌”、“想听”、“来首”、“播放”等中文前缀
    q = re.sub(r"^(?:点歌|想听|来一首|来首|播放|听)[\s:：]*", "", q, flags=re.I)
    # 移除首尾可能包含的书名号、引号、括号等包裹字符
    q = q.strip("《》\"'“”‘’【】[]()（） ")
    return q.strip()

async def _is_outer_url_playable(client: httpx.AsyncClient, url: str) -> bool:
    """预检音频直链是否真实可播（避免 VIP/版权拦截为 HTML 网页）"""
    try:
        r = await client.get(url, headers={"Range": "bytes=0-511"})
        if r.status_code in (200, 206):
            ctype = (r.headers.get("Content-Type") or "").lower()
            if "audio" in ctype or "mpeg" in ctype or "octet-stream" in ctype:
                return True
    except Exception:
        pass
    return False

async def search_netease_song(keyword: str) -> Optional[Dict[str, Any]]:
    """在线搜索网易云音乐单曲，优选可正常直链播放的音轨，返回真实音频直链与专辑封面"""
    if not keyword or not keyword.strip():
        return None
    clean_name = clean_song_query(keyword)
    if not clean_name:
        return None
    query = urllib.parse.quote(clean_name)
    search_url = f"https://music.163.com/api/search/get/web?s={query}&type=1&offset=0&total=true&limit=8"

    try:
        async with httpx.AsyncClient(timeout=6.0, headers=NETEASE_HEADERS, follow_redirects=True) as client:
            resp = await client.get(search_url)
            if resp.status_code != 200:
                return None
            data = resp.json()
            songs = data.get("result", {}).get("songs", [])
            if not songs:
                return None

            selected_song = None
            outer_url = None

            # 遍历前 8 首候选歌曲，挑选首个具有开放真实 MP3 音频流的音轨
            for s in songs:
                s_id = s.get("id")
                test_url = f"http://music.163.com/song/media/outer/url?id={s_id}.mp3"
                if await _is_outer_url_playable(client, test_url):
                    selected_song = s
                    outer_url = test_url
                    break

            # 若前 8 首候选均有 VIP 保护，兜底选第 1 首
            if not selected_song:
                selected_song = songs[0]
                outer_url = f"http://music.163.com/song/media/outer/url?id={selected_song.get('id')}.mp3"

            song_id = selected_song.get("id")
            title = selected_song.get("name", clean_name)
            artists = " / ".join(a.get("name", "") for a in selected_song.get("artists", [])) or "未知歌手"

            # 获取高清专辑封面
            cover = None
            try:
                detail_url = f"https://music.163.com/api/song/detail/?id={song_id}&ids=%5B{song_id}%5D"
                detail_resp = await client.get(detail_url)
                if detail_resp.status_code == 200:
                    detail_data = detail_resp.json()
                    detail_songs = detail_data.get("songs", [])
                    if detail_songs:
                        cover = detail_songs[0].get("album", {}).get("picUrl")
            except Exception:
                pass

            if not cover:
                cover = (
                    selected_song.get("album", {}).get("picUrl") or
                    "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=140&auto=format&fit=crop&q=80"
                )

            return {
                "id": song_id,
                "title": title,
                "artist": artists,
                "cover": cover,
                "url": outer_url,
                "source": "netease"
            }
    except Exception as e:
        print(f"[NetEase Search Error]: {e}")
        return None

async def fetch_netease_playlist(playlist_id: int = DEFAULT_ANIME_PLAYLIST_ID) -> List[Dict[str, Any]]:
    """在线拉取指定网易云歌单的所有曲目列表"""
    url = f"https://music.163.com/api/playlist/detail?id={playlist_id}"
    results: List[Dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=8.0, headers=NETEASE_HEADERS) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            data = resp.json()
            tracks = data.get("result", {}).get("tracks", [])
            for t in tracks[:30]:  # 精选前 30 首
                s_id = t.get("id")
                title = t.get("name", "")
                artists = " / ".join(a.get("name", "") for a in t.get("artists", [])) or "群星"
                cover = t.get("album", {}).get("picUrl") or "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=140&auto=format&fit=crop&q=80"
                outer_url = f"http://music.163.com/song/media/outer/url?id={s_id}.mp3"
                results.append({
                    "id": s_id,
                    "title": title,
                    "artist": artists,
                    "cover": cover,
                    "url": outer_url,
                    "source": "netease"
                })
    except Exception as e:
        print(f"[NetEase Playlist Error]: {e}")
    return results

async def fetch_netease_lyric(song_id: int) -> str:
    """在线获取单曲的标准 LRC 格式歌词"""
    if not song_id:
        return ""
    url = f"https://music.163.com/api/song/lyric?os=pc&id={song_id}&lv=-1&kv=-1&tv=-1"
    try:
        async with httpx.AsyncClient(timeout=5.0, headers=NETEASE_HEADERS) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("lrc", {}).get("lyric", "")
    except Exception as e:
        print(f"[NetEase Lyric Error]: {e}")
    return ""

