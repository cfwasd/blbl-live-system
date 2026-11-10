import ast
import json
import re
import urllib.parse
from typing import Optional, Dict, Any, List, Union
import httpx

NETEASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://music.163.com/",
    "Accept": "*/*",
    "Cookie": "os=pc; appver=2.9.7"
}

KUWO_HEADERS = {
    "User-Agent": "okhttp/3.10.0",
    "Accept": "*/*",
    "Connection": "keep-alive",
}

DEFAULT_ANIME_PLAYLIST_ID = 3778678  # 官方热门推荐歌单
DEFAULT_COVER = "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=300&auto=format&fit=crop&q=80"

# 内存歌词缓存 (song_id -> LRC 歌词文本)，保证不同音源拉取后立即可供大屏显示
_LYRIC_CACHE: Dict[str, str] = {}


def clean_song_query(query: str) -> str:
    """去除指令前缀与包裹符号，提取纯净歌曲名"""
    if not query:
        return ""
    q = query.strip()
    q = re.sub(r"^[#/!！]+", "", q)
    q = re.sub(
        r"^(?:点一首歌|点首歌|点一首|点首|点播|点歌|想听|来一首|来首|放一下|放首|搜歌|播放|听)[\s:：]*",
        "",
        q,
        flags=re.I,
    )
    q = q.strip("《》\"'“”‘’【】[]()（） ")
    return q.strip()


def _normalize_text(text: str) -> str:
    return re.sub(r"[^\w一-龥a-zA-Z0-9]", "", text.lower())


def _is_song_relevant(candidate_title: str, candidate_artists: str, query: str) -> bool:
    t_norm = _normalize_text(candidate_title)
    c_norm = _normalize_text(candidate_title + " " + candidate_artists)
    q_norm = _normalize_text(query)
    if not t_norm or not q_norm:
        return False
    if q_norm in t_norm or t_norm in q_norm or q_norm in c_norm or c_norm in q_norm:
        return True
    set_c = set(c_norm)
    set_q = set(q_norm)
    intersect = set_c & set_q
    if len(q_norm) <= 2:
        return len(intersect) == len(q_norm)
    overlap_ratio = len(intersect) / len(set_q)
    return len(intersect) >= 2 and overlap_ratio >= 0.5


async def _is_outer_url_playable(client: httpx.AsyncClient, url: str) -> bool:
    """预检音频直链是否真实可播（避免 VIP/版权拦截为 HTML 404 网页）"""
    try:
        r = await client.get(url, headers={"Range": "bytes=0-511"})
        if r.status_code in (200, 206):
            ctype = (r.headers.get("Content-Type") or "").lower()
            final_url = str(r.url).lower()
            if "404" in final_url or "html" in ctype:
                return False
            if "audio" in ctype or "mpeg" in ctype or "octet-stream" in ctype or "mp3" in final_url:
                return True
    except Exception:
        pass
    return False


async def _fetch_lyric_by_title_artist(client: httpx.AsyncClient, title: str, artist: str) -> str:
    """根据歌名与歌手向网易云检索标准 LRC 歌词"""
    query = urllib.parse.quote(f"{title} {artist}")
    search_url = f"https://music.163.com/api/search/get/web?s={query}&type=1&limit=3"
    try:
        resp = await client.get(search_url, headers=NETEASE_HEADERS, timeout=3.5)
        if resp.status_code == 200:
            songs = resp.json().get("result", {}).get("songs", [])
            if songs:
                s_id = songs[0].get("id")
                lrc_url = f"https://music.163.com/api/song/lyric?os=pc&id={s_id}&lv=-1&kv=-1&tv=-1"
                lrc_resp = await client.get(lrc_url, headers=NETEASE_HEADERS, timeout=3.5)
                if lrc_resp.status_code == 200:
                    return lrc_resp.json().get("lrc", {}).get("lyric", "")
    except Exception:
        pass
    return ""


async def _search_kuwo_source(client: httpx.AsyncClient, clean_name: str) -> Optional[Dict[str, Any]]:
    """酷我高品质音源解析引擎（覆盖周杰伦等 TME 全版权、热歌与伴奏）"""
    try:
        q = urllib.parse.quote(clean_name)
        search_url = (
            f"http://search.kuwo.cn/r.s?client=kt&all={q}&pn=0&rn=5"
            f"&uid=794761770&ver=kwplayer_ar_9.2.2.1&vipver=1&ft=music"
            f"&cluster=0&strategy=2012&encoding=utf8&rformat=json"
        )
        resp = await client.get(search_url, headers=KUWO_HEADERS, timeout=4.0)
        if resp.status_code != 200 or not resp.text:
            return None

        data = ast.literal_eval(resp.text)
        songs = data.get("abslist", [])
        if not songs:
            return None

        for item in songs[:3]:
            rid = item.get("MUSICRID", "")
            if not rid:
                continue
            rid_num = rid.replace("MUSIC_", "")
            title = item.get("SONGNAME", clean_name).replace("&nbsp;", " ")
            artist = item.get("ARTIST", "未知歌手").replace("&nbsp;", " ")

            # 强相关性校验
            if not _is_song_relevant(title, artist, clean_name):
                continue

            # 1. 获取 CDN 播放直链
            play_api = f"http://antiserver.kuwo.cn/anti.s?type=convert_url&rid={rid}&format=mp3|aac&response=url"
            play_resp = await client.get(play_api, headers=KUWO_HEADERS, timeout=3.5)
            audio_url = play_resp.text.strip()
            if not audio_url.startswith("http"):
                continue

            # 2. 异步提取歌词与封面
            cover = ""
            lrc_text = ""
            try:
                # 尝试从网易云获取高品质精确匹配的 LRC 歌词
                lrc_text = await _fetch_lyric_by_title_artist(client, title, artist)
            except Exception:
                pass

            if lrc_text:
                _LYRIC_CACHE[str(rid_num)] = lrc_text

            return {
                "id": str(rid_num),
                "title": title,
                "artist": artist,
                "cover": cover or DEFAULT_COVER,
                "url": audio_url,
                "source": "kuwo",
                "lyric": lrc_text,
                "is_cover": False,
            }
    except Exception:
        return None
    return None


async def _search_netease_source(client: httpx.AsyncClient, clean_name: str) -> Optional[Dict[str, Any]]:
    """网易云音源解析引擎（适合二次元、独立民谣等曲目）"""
    query = urllib.parse.quote(clean_name)
    search_url = f"https://music.163.com/api/cloudsearch/pc?s={query}&type=1&offset=0&limit=10"

    try:
        resp = await client.get(search_url, headers=NETEASE_HEADERS, timeout=5.0)
        if resp.status_code != 200:
            return None
        data = resp.json()
        songs = data.get("result", {}).get("songs", [])
        if not songs:
            return None

        # 筛选强相关性曲目
        relevant_songs = []
        for s in songs:
            artists_str = " ".join(a.get("name", "") for a in s.get("ar", s.get("artists", [])))
            if _is_song_relevant(s.get("name", ""), artists_str, clean_name):
                relevant_songs.append(s)

        if not relevant_songs:
            return None

        # 遍历前 3 首寻找开放直链
        for s in relevant_songs[:3]:
            s_id = s.get("id")
            test_url = f"http://music.163.com/song/media/outer/url?id={s_id}.mp3"
            if await _is_outer_url_playable(client, test_url):
                title = s.get("name", clean_name)
                artists_list = s.get("ar", s.get("artists", []))
                artists = " / ".join(a.get("name", "") for a in artists_list) or "未知歌手"
                al_obj = s.get("al", s.get("album", {}))
                cover = al_obj.get("picUrl") or DEFAULT_COVER

                # 尝试预加载歌词
                lrc = await fetch_netease_lyric(s_id)
                if lrc:
                    _LYRIC_CACHE[str(s_id)] = lrc

                s_name = title.lower()
                is_cover = any(tag in s_name for tag in ["cover", "翻唱", "伴奏", "inst", "instrumental"])

                return {
                    "id": str(s_id),
                    "title": title,
                    "artist": artists,
                    "cover": cover,
                    "url": test_url,
                    "source": "netease",
                    "lyric": lrc,
                    "is_cover": is_cover,
                }
    except Exception:
        return None
    return None


async def search_netease_song(keyword: str) -> Optional[Dict[str, Any]]:
    """
    全网高保真音乐搜索主入口：
    优先请求酷我（覆盖周杰伦等 TME 独家版权与热门华语歌），无缝降级至网易云
    """
    if not keyword or not keyword.strip():
        return None
    clean_name = clean_song_query(keyword)
    if not clean_name:
        return None

    async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
        # 1. 优先尝试酷我全版权引擎（突破周杰伦/TME VIP限制）
        song = await _search_kuwo_source(client, clean_name)
        if song and song.get("url"):
            return song

        # 2. 降级尝试网易云引擎
        song = await _search_netease_source(client, clean_name)
        if song and song.get("url"):
            return song

    # 均未命中
    return {
        "error": "not_found",
        "title": clean_name,
        "message": f"全网未检索到与“{clean_name}”匹配的可播放音源",
    }


async def fetch_netease_playlist(playlist_id: int = DEFAULT_ANIME_PLAYLIST_ID) -> List[Dict[str, Any]]:
    """在线拉取指定网易云歌单的所有曲目列表"""
    url = f"https://music.163.com/api/playlist/detail?id={playlist_id}"
    results: List[Dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=8.0, headers=NETEASE_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return []
            data = resp.json()
            tracks = data.get("result", {}).get("tracks", [])
            for t in tracks[:30]:  # 精选前 30 首
                s_id = t.get("id")
                title = t.get("name", "")
                artists = " / ".join(a.get("name", "") for a in t.get("artists", [])) or "群星"
                cover = t.get("album", {}).get("picUrl") or DEFAULT_COVER
                outer_url = f"http://music.163.com/song/media/outer/url?id={s_id}.mp3"
                results.append({
                    "id": str(s_id),
                    "title": title,
                    "artist": artists,
                    "cover": cover,
                    "url": outer_url,
                    "source": "netease",
                })
    except Exception as e:
        print(f"[Playlist Error]: {e}")
    return results


async def fetch_netease_lyric(song_id: Union[int, str]) -> str:
    """在线获取单曲的标准 LRC 格式歌词（支持网易云与酷我跨平台双源）"""
    if not song_id:
        return ""
    sid_str = str(song_id)

    # 1. 优先从内存缓存中获取
    if sid_str in _LYRIC_CACHE:
        return _LYRIC_CACHE[sid_str]

    # 2. 尝试从酷我拉取
    try:
        async with httpx.AsyncClient(timeout=4.0, headers=KUWO_HEADERS) as client:
            info_url = f"http://m.kuwo.cn/newh5/singles/songinfoandlrc?musicId={sid_str}&httpsStatus=1"
            resp = await client.get(info_url)
            if resp.status_code == 200:
                info_json = resp.json().get("data", {})
                lrclist = info_json.get("lrclist", [])
                if lrclist:
                    lines = []
                    for item in lrclist:
                        t = float(item.get("time", 0))
                        mins, secs = divmod(int(t), 60)
                        ms = int((t - int(t)) * 100)
                        line_lyric = item.get("lineLyric", "").strip()
                        if line_lyric:
                            lines.append(f"[{mins:02d}:{secs:02d}.{ms:02d}]{line_lyric}")
                    lrc = "\n".join(lines)
                    _LYRIC_CACHE[sid_str] = lrc
                    return lrc
    except Exception:
        pass

    # 3. 尝试从网易云拉取
    try:
        async with httpx.AsyncClient(timeout=4.0, headers=NETEASE_HEADERS) as client:
            url = f"https://music.163.com/api/song/lyric?os=pc&id={sid_str}&lv=-1&kv=-1&tv=-1"
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                lrc = data.get("lrc", {}).get("lyric", "")
                if lrc:
                    _LYRIC_CACHE[sid_str] = lrc
                    return lrc
    except Exception:
        pass

    return ""
