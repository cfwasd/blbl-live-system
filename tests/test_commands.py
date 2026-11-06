import pytest
from admin.core.ingress.command_parser import parse_danmu_command, CommandAction

def test_parse_switch_song():
    cmd = parse_danmu_command("切歌")
    assert cmd is not None
    assert cmd.action == "switch_song"
    assert cmd.payload == ""

    cmd2 = parse_danmu_command("下一首")
    assert cmd2 is not None
    assert cmd2.action == "switch_song"

    # 支持前导符号与更多口语化切歌表达
    assert parse_danmu_command("#切歌").action == "switch_song"
    assert parse_danmu_command("换一首").action == "switch_song"
    assert parse_danmu_command("换歌").action == "switch_song"

def test_parse_request_song():
    cmd = parse_danmu_command("点歌 恋爱循环")
    assert cmd is not None
    assert cmd.action == "request_song"
    assert cmd.payload == "恋爱循环"

    # 支持带 #、中文冒号、点首歌、放首等多样化弹幕表达
    cmd_hash = parse_danmu_command("#点歌 晴天")
    assert cmd_hash is not None
    assert cmd_hash.payload == "晴天"

    cmd_colon = parse_danmu_command("点歌：晴天")
    assert cmd_colon is not None
    assert cmd_colon.payload == "晴天"

    cmd_song = parse_danmu_command("点首歌 晴天")
    assert cmd_song is not None
    assert cmd_song.payload == "晴天"

    cmd_play = parse_danmu_command("放首 晴天")
    assert cmd_play is not None
    assert cmd_play.payload == "晴天"

def test_parse_pause_resume():
    cmd_pause = parse_danmu_command("暂停音乐")
    assert cmd_pause is not None
    assert cmd_pause.action == "pause_music"

    cmd_resume = parse_danmu_command("恢复音乐")
    assert cmd_resume is not None
    assert cmd_resume.action == "resume_music"

def test_parse_theme():
    cmd = parse_danmu_command("切背景")
    assert cmd is not None
    assert cmd.action == "toggle_theme"

    cmd_none = parse_danmu_command("主播今天真可爱")
    assert cmd_none is None

def test_netease_query_cleaning_and_relevance():
    from admin.core.music.netease import clean_song_query, _is_title_relevant

    assert clean_song_query("点歌 晴天") == "晴天"
    assert clean_song_query("点一首《恋爱循环》") == "恋爱循环"
    assert clean_song_query("#想听 告白气球") == "告白气球"
    assert clean_song_query("放首 孤勇者") == "孤勇者"

    # 强相关性校验
    assert _is_title_relevant("晴天", "晴天") is True
    assert _is_title_relevant("晴天 (Live版)", "晴天") is True
    assert _is_title_relevant("千本桜", "千本樱") is True
    # 不相关曲目直接拦截
    assert _is_title_relevant("恋爱循环", "孤勇者") is False
    assert _is_title_relevant("野狼disco", "夜曲") is False
