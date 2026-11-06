import re
from typing import Optional
from admin.core.ingress.event import CommandAction

_RE_SWITCH = re.compile(r"^[#/!！]?(?:切歌|下一首|下一曲|随机音乐|随机切歌|换首歌|换歌|换一首)$")
_RE_REQUEST = re.compile(
    r"^[#/!！]?(?:点一首歌|点首歌|点一首|点首|点播|点歌|想听|来一首|来首|放一下|放首|搜歌|播放)[\s:：]*(.+)$",
    re.IGNORECASE
)
_RE_PAUSE = re.compile(r"^[#/!！]?(?:暂停音乐|暂停伴奏|暂停播放)$")
_RE_RESUME = re.compile(r"^[#/!！]?(?:恢复音乐|继续播放|恢复播放)$")
_RE_THEME = re.compile(r"^[#/!！]?(?:切背景|切换背景|透明|换背景)$")

def parse_danmu_command(content: str) -> Optional[CommandAction]:
    content = content.strip()
    if _RE_SWITCH.match(content):
        return CommandAction(action="switch_song", payload="")
    match_req = _RE_REQUEST.match(content)
    if match_req:
        return CommandAction(action="request_song", payload=match_req.group(1).strip())
    if _RE_PAUSE.match(content):
        return CommandAction(action="pause_music", payload="")
    if _RE_RESUME.match(content):
        return CommandAction(action="resume_music", payload="")
    if _RE_THEME.match(content):
        return CommandAction(action="toggle_theme", payload="")
    return None
