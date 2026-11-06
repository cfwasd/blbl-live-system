import urllib.parse
import re
from typing import Optional, Dict, Any, List
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

DEFAULT_ANIME_PLAYLIST_ID = 3778678  # 官方热门推荐歌单

def clean_song_query(query: str) -> str:
    """去除指令前缀与包裹符号，提取纯净歌曲名"""
    q = query.strip()
    # 移除前导符号如 #、! 等
    q = re.sub(r"^[#/!！]+", "", q)
    # 移除“点歌”、“点播”、“想听”、“来首”、“播放”等中文前缀
    q = re.sub(r"^(?:点一首歌|点首歌|点一首|点首|点播|点歌|想听|来一首|来首|放一下|放首|搜歌|播放|听)[\s:：]*", "", q, flags=re.I)
    # 移除首尾可能包含的书名号、引号、括号等包裹字符
    q = q.strip("《》\"'“”‘’【】[]()（） ")
    return q.strip()

def _normalize_text(text: str) -> str:
    return re.sub(r"[^\w一-龥a-zA-Z0-9]", "", text.lower())

def _is_title_relevant(candidate_title: str, query: str) -> bool:
    return _is_song_relevant(candidate_title, "", query)

def _is_song_relevant(candidate_title: str, candidate_artists: str, query: str) -> bool:
    t_norm = _normalize_text(candidate_title)
    c_norm = _normalize_text(candidate_title + " " + candidate_artists)
    q_norm = _normalize_text(query)
    if not t_norm or not q_norm:
        return False
    # 标题或标题+歌手完全匹配或子串包含
    if q_norm in t_norm or t_norm in q_norm or q_norm in c_norm or c_norm in q_norm:
        return True
    # 字符重合度计算（解决中日汉字互译及部分曲名偏差，如 千本樱 vs 千本桜）
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

async def search_netease_song(keyword: str) -> Optional[Dict[str, Any]]:
    """在线搜索网易云音乐单曲，优选可正常直链播放且标题强匹配的音轨，返回真实音频直链与专辑封面"""
    if not keyword or not keyword.strip():
        return None
    clean_name = clean_song_query(keyword)
    if not clean_name:
        return None
    query = urllib.parse.quote(clean_name)
    # 使用 cloudsearch/pc 接口，确保返回结构化 JSON 字典而非加密字符
    search_url = f"https://music.163.com/api/cloudsearch/pc?s={query}&type=1&offset=0&limit=12"

    try:
        async with httpx.AsyncClient(timeout=6.0, headers=NETEASE_HEADERS, follow_redirects=True) as client:
            resp = await client.get(search_url)
            if resp.status_code != 200:
                return {"error": "api_error", "title": clean_name, "message": "网易云音乐搜索接口请求异常"}
            data = resp.json()
            result_obj = data.get("result")
            if not isinstance(result_obj, dict):
                return {"error": "api_error", "title": clean_name, "message": "网易云搜索返回格式异常"}
            songs = result_obj.get("songs", [])
            if not songs:
                return {"error": "not_found", "title": clean_name, "message": f"未搜索到与“{clean_name}”相关的歌曲"}

            # 1. 过滤出标题及歌手具有相关性的候选歌曲，杜绝货不对板
            relevant_songs = []
            for s in songs:
                artists_str = " ".join(a.get("name", "") for a in s.get("ar", s.get("artists", [])))
                if _is_song_relevant(s.get("name", ""), artists_str, clean_name):
                    relevant_songs.append(s)

            if not relevant_songs:
                return {"error": "not_found", "title": clean_name, "message": f"未搜索到与“{clean_name}”相关的歌曲"}

            selected_song = None
            outer_url = None
            is_cover = False

            # 2. 遍历候选歌曲，挑选首个具有开放真实 MP3 音频流的音轨
            for s in relevant_songs:
                s_id = s.get("id")
                test_url = f"http://music.163.com/song/media/outer/url?id={s_id}.mp3"
                if await _is_outer_url_playable(client, test_url):
                    selected_song = s
                    outer_url = test_url
                    # 检测是否为伴奏/翻唱版本
                    s_name = s.get("name", "").lower()
                    if any(tag in s_name for tag in ["cover", "翻唱", "伴奏", "inst", "instrumental", "钢琴", "吉他", "原唱"]):
                        is_cover = True
                    break

            # 3. 若所有高匹配曲目均因 VIP/版权保护不可外链
            if not selected_song:
                top_song = relevant_songs[0]
                top_title = top_song.get("name", clean_name)
                artists_list = top_song.get("ar", top_song.get("artists", []))
                artists = " / ".join(a.get("name", "") for a in artists_list) or "原唱"
                return {
                    "error": "vip_protected",
                    "title": top_title,
                    "artist": artists,
                    "message": f"歌曲《{top_title}》受平台版权或VIP保护，暂无可用外链音轨"
                }

            song_id = selected_song.get("id")
            title = selected_song.get("name", clean_name)
            artists_list = selected_song.get("ar", selected_song.get("artists", []))
            artists = " / ".join(a.get("name", "") for a in artists_list) or "未知歌手"

            # 获取高清专辑封面
            cover = None
            try:
                al_obj = selected_song.get("al", selected_song.get("album", {}))
                cover = al_obj.get("picUrl")
                if not cover:
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
                cover = "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=140&auto=format&fit=crop&q=80"

            return {
                "id": song_id,
                "title": title,
                "artist": artists,
                "cover": cover,
                "url": outer_url,
                "is_cover": is_cover,
                "source": "netease",
                "error": None
            }
    except Exception as e:
        print(f"[NetEase Search Error]: {e}")
        return {"error": "network_error", "title": clean_name, "message": f"点歌请求网络异常: {e}"}

async def fetch_netease_playlist(playlist_id: int = DEFAULT_ANIME_PLAYLIST_ID) -> List[Dict[str, Any]]:
    """在线拉取指定网易云歌单的所有曲目列表"""
    url = f"https://music.163.com/api/playlist/detail?id={playlist_id}"
    results: List[Dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=8.0, headers=NETEASE_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                tracks = data.get("result", {}).get("tracks", [])
                for t in tracks:
                    artists_list = t.get("ar", t.get("artists", []))
                    artists = " / ".join(a.get("name", "") for a in artists_list) or "未知歌手"
                    al_obj = t.get("al", t.get("album", {}))
                    results.append({
                        "id": t.get("id"),
                        "title": t.get("name", "未知曲目"),
                        "artist": artists,
                        "cover": al_obj.get("picUrl") or "",
                        "url": f"http://music.163.com/song/media/outer/url?id={t.get('id')}.mp3",
                        "source": "netease"
                    })
    except Exception as e:
        print(f"[NetEase Playlist Error]: {e}")
    return results

async def fetch_netease_lyric(song_id: int) -> str:
    """获取单曲的原始 LRC 滚动歌词文本"""
    url = f"https://music.163.com/api/song/lyric?id={song_id}&lv=1&kv=1&tv=-1"
    try:
        async with httpx.AsyncClient(timeout=5.0, headers=NETEASE_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("lrc", {}).get("lyric", "")
    except Exception as e:
        print(f"[NetEase Lyric Error]: {e}")
    return ""
