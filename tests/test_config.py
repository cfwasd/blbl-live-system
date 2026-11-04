import os
import pytest
from admin.config import AppConfig, load_config, save_config

def test_load_default_config(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("""
server:
  host: "0.0.0.0"
  port: 8000
bilibili:
  room_id: 21452505
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-test"
  model: "gemini-3.8-flash"
volc_tts:
  api_key: "volc-key"
  resource_id: "seed-tts-2.0"
  speaker: "zh_female_vv_uranus_bigtts"
obs:
  host: "127.0.0.1"
  port: 4455
  password: ""
""", encoding="utf-8")

    cfg = load_config(str(config_path))
    assert cfg.server.port == 8000
    assert cfg.bilibili.room_id == 21452505
    assert cfg.llm.model == "gemini-3.8-flash"
    assert cfg.volc_tts.resource_id == "seed-tts-2.0"

def test_save_and_reload_config(tmp_path):
    config_path = tmp_path / "saved_config.yaml"
    cfg = AppConfig()
    cfg.bilibili.room_id = 99999
    cfg.llm.model = "gpt-4o"
    save_config(cfg, str(config_path))

    reloaded = load_config(str(config_path))
    assert reloaded.bilibili.room_id == 99999
    assert reloaded.llm.model == "gpt-4o"
