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

def test_parse_request_song():
    cmd = parse_danmu_command("点歌 恋爱循环")
    assert cmd is not None
    assert cmd.action == "request_song"
    assert cmd.payload == "恋爱循环"

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
