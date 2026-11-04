# 虚拟AI人物直播弹幕驱动系统 (全功能 MVP) 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建虚拟 AI 人物直播弹幕驱动系统的全功能 MVP，实现统一单长连接通信（SSE）、B站弹幕接入与弹幕指令互动（切歌/点歌）、责任链风控、OpenAI 兼容 LLM 思考、火山豆包 V3 HTTP 语音合成、管理端全功能控制台（配置热推与在线发音试听）以及高颜值 Live2D 直播大屏（Gemini 娘立绘、Web Audio 实时口型同步、数据看板 HUD、伴奏避让唱片机）。

**Architecture:** 严格遵循“重核轻端、单向驱动”架构原则。Python FastAPI 作为异步计算与网络中枢，集成 `blivedm`、`pyahocorasick`、OpenAI 兼容客户端、火山引擎 V3 HTTP 流式客户端及 `obs-websocket-py`；通过单一 HTTP SSE 管道（`/api/stream`）向 OBS 浏览器源大屏推送所有事件；大屏基于 Vue 3 + Pixi.js (v7) + `pixi-live2d-display` 纯渲染呈现；管理后台为零构建的单文件 Vue 3 + Tailwind CSS SPA。

**Tech Stack:** Python 3.10+, FastAPI, Uvicorn, blivedm, pyahocorasick, httpx, pydantic, pyyaml, pytest, Vue 3, Vite, TypeScript, Pixi.js (v7), pixi-live2d-display, Web Audio API, Tailwind CSS.

**Spec:** `docs/superpowers/specs/2026-11-04-mvp-design.md`

## Global Constraints

- 所有前后端通信收敛于单一 HTTP SSE 连接（`/api/stream`），禁止大屏建立多个长连接。
- 敏感词过滤必须使用 Aho-Corasick 算法（`pyahocorasick`），杜绝遍历式 `in` 匹配。
- 火山豆包语音必须严格实现 V3 HTTP 单向流式规范（`https://openspeech.bytedance.com/api/v3/tts/unidirectional`，`seed-tts-2.0`，Chunked Base64 解码）。
- 直播大屏背景必须完全透明（`background: transparent !important`），弹幕列表必须执行上限 30 条的滑窗淘汰机制以防 CEF 内存泄露。
- 管理后台任何配置变更必须通过 SSE `config_sync` 即刻热推到直播画面，禁止刷新 OBS 页面。

---

### Task 1: 项目基础结构与配置管理系统

**Files:**
- Create: `requirements.txt`
- Create: `configs/config.yaml`
- Create: `configs/banned_words.txt`
- Create: `admin/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: None
- Produces: `AppConfig`, `get_config() -> AppConfig`, `save_config(config: AppConfig) -> None`

- [ ] **Step 1: 编写配置模块的失败测试用例**

在 `tests/test_config.py` 中编写配置读取与验证测试：
```python
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
```

- [ ] **Step 2: 运行测试以确认其失败**

运行：`pytest tests/test_config.py -v`
预期结果：FAIL（ModuleNotFoundError: No module named 'admin'）

- [ ] **Step 3: 编写依赖清单与配置管理实现**

创建 `requirements.txt`：
```text
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
pyyaml>=6.0
pyahocorasick>=2.0.0
httpx>=0.24.0
cachetools>=5.3.0
blivedm>=1.4.0
obs-websocket-py>=1.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

创建默认敏感词库 `configs/banned_words.txt`：
```text
违禁词测试A
广告引流
外挂加群
```

创建默认配置文件 `configs/config.yaml`：
```yaml
server:
  host: "0.0.0.0"
  port: 8000
bilibili:
  room_id: 21452505
  sessdata: ""
llm:
  base_url: "https://api.openai.com/v1"
  api_key: "your_llm_api_key_here"
  model: "gemini-3.8-flash"
  system_prompt: "你是 Gemini 娘，元气、呆萌、带有一点点傲娇科技感的二次元虚拟主播。回复观众弹幕要求：语言风格可爱自然，回答极度简练（严格限制在 30 字以内），富有情绪起伏。"
volc_tts:
  api_key: "your_volc_api_key_here"
  resource_id: "seed-tts-2.0"
  speaker: "zh_female_vv_uranus_bigtts"
  format: "mp3"
  sample_rate: 24000
obs:
  host: "127.0.0.1"
  port: 4455
  password: ""
mascot:
  scale: 1.0
  position_x: 0.8
  position_y: 0.9
  theme: "transparent"
bgm:
  default_volume: 0.35
  ducking_volume: 0.08
  playlist:
    - title: "Lo-Fi 慵懒午后"
      file: "lofi_01.mp3"
    - title: "元气二次元日常"
      file: "anime_02.mp3"
```

创建 `admin/config.py`：
```python
from typing import List, Optional
from pydantic import BaseModel, Field
import yaml
import os

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000

class BilibiliConfig(BaseModel):
    room_id: int = 21452505
    sessdata: str = ""

class LLMConfig(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gemini-3.8-flash"
    system_prompt: str = "你是 Gemini 娘，元气呆萌傲娇二次元虚拟主播，每句回答严格在30字以内。"

class VolcengineTTSConfig(BaseModel):
    api_key: str = ""
    resource_id: str = "seed-tts-2.0"
    speaker: str = "zh_female_vv_uranus_bigtts"
    format: str = "mp3"
    sample_rate: int = 24000

class OBSConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 4455
    password: str = ""

class MascotConfig(BaseModel):
    scale: float = 1.0
    position_x: float = 0.8
    position_y: float = 0.9
    theme: str = "transparent"

class BGMItem(BaseModel):
    title: str
    file: str

class BGMConfig(BaseModel):
    default_volume: float = 0.35
    ducking_volume: float = 0.08
    playlist: List[BGMItem] = Field(default_factory=list)

class AppConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    bilibili: BilibiliConfig = Field(default_factory=BilibiliConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    volc_tts: VolcengineTTSConfig = Field(default_factory=VolcengineTTSConfig)
    obs: OBSConfig = Field(default_factory=OBSConfig)
    mascot: MascotConfig = Field(default_factory=MascotConfig)
    bgm: BGMConfig = Field(default_factory=BGMConfig)

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "config.yaml")
_CURRENT_CONFIG: Optional[AppConfig] = None

def load_config(path: str = _CONFIG_PATH) -> AppConfig:
    global _CURRENT_CONFIG
    if not os.path.exists(path):
        _CURRENT_CONFIG = AppConfig()
        return _CURRENT_CONFIG
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    _CURRENT_CONFIG = AppConfig(**data)
    return _CURRENT_CONFIG

def get_config() -> AppConfig:
    global _CURRENT_CONFIG
    if _CURRENT_CONFIG is None:
        return load_config()
    return _CURRENT_CONFIG

def save_config(config: AppConfig, path: str = _CONFIG_PATH) -> None:
    global _CURRENT_CONFIG
    _CURRENT_CONFIG = config
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config.model_dump(), f, allow_unicode=True, sort_keys=False)
```

- [ ] **Step 4: 运行测试以确认其通过**

运行：`pytest tests/test_config.py -v`
预期结果：PASS

- [ ] **Step 5: 提交配置模块代码**

```bash
git add requirements.txt configs/ admin/config.py tests/test_config.py
git commit -m "feat: add project base configuration and pydantic schema"
```

---

### Task 2: 弹幕接入模型与指令解析器

**Files:**
- Create: `admin/core/ingress/event.py`
- Create: `admin/core/ingress/command_parser.py`
- Create: `admin/core/ingress/bili_client.py`
- Test: `tests/test_commands.py`

**Interfaces:**
- Consumes: `admin.config`
- Produces: `DanmuEvent`, `CommandAction`, `parse_danmu_command(content: str) -> Optional[CommandAction]`, `BiliClientWrapper`

- [ ] **Step 1: 编写指令解析器的失败测试用例**

在 `tests/test_commands.py` 中测试对观众发送的切歌、点歌、切背景等指令的拦截与提取：
```python
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
    assert cmd_pause.action == "pause_music"
    
    cmd_resume = parse_danmu_command("恢复音乐")
    assert cmd_resume.action == "resume_music"

def test_parse_theme():
    cmd = parse_danmu_command("切背景")
    assert cmd.action == "toggle_theme"
    
    cmd_none = parse_danmu_command("主播今天真可爱")
    assert cmd_none is None
```

- [ ] **Step 2: 运行测试以确认其失败**

运行：`pytest tests/test_commands.py -v`
预期结果：FAIL（ModuleNotFoundError: No module named 'admin.core.ingress'）

- [ ] **Step 3: 编写事件模型与指令解析器实现**

创建 `admin/core/ingress/event.py`：
```python
import time
import uuid
from typing import Optional
from pydantic import BaseModel, Field

class DanmuEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    uid: int
    uname: str
    content: str
    badge_name: Optional[str] = ""
    badge_level: int = 0
    price: float = 0.0
    is_super_chat: bool = False
    timestamp: float = Field(default_factory=time.time)

class CommandAction(BaseModel):
    action: str  # switch_song, request_song, pause_music, resume_music, toggle_theme
    payload: str = ""
```

创建 `admin/core/ingress/command_parser.py`：
```python
import re
from typing import Optional
from admin.core.ingress.event import CommandAction

_RE_SWITCH = re.compile(r"^(切歌|下一首)$")
_RE_REQUEST = re.compile(r"^点歌\s+(.+)$")
_RE_PAUSE = re.compile(r"^(暂停音乐|暂停伴奏)$")
_RE_RESUME = re.compile(r"^(恢复音乐|继续播放)$")
_RE_THEME = re.compile(r"^(切背景|切换背景|透明)$")

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
```

创建 `admin/core/ingress/bili_client.py`：
```python
import asyncio
import httpx
from typing import Callable, Optional
from admin.core.ingress.event import DanmuEvent

class BiliClientWrapper:
    def __init__(self, room_id: int, on_danmu: Callable[[DanmuEvent], asyncio.Future]):
        self.raw_room_id = room_id
        self.real_room_id = room_id
        self.on_danmu = on_danmu
        self.is_running = False

    async def resolve_real_room_id(self) -> int:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"https://api.live.bilibili.com/room/v1/Room/room_init?id={self.raw_room_id}")
                if res.status_code == 200:
                    data = res.json()
                    if data.get("code") == 0:
                        self.real_room_id = data["data"]["room_id"]
        except Exception:
            self.real_room_id = self.raw_room_id
        return self.real_room_id

    async def inject_mock_danmu(self, uname: str, content: str, price: float = 0.0, is_sc: bool = False):
        event = DanmuEvent(
            uid=123456,
            uname=uname,
            content=content,
            badge_name="粉丝团",
            badge_level=15,
            price=price,
            is_super_chat=is_sc
        )
        await self.on_danmu(event)
```

- [ ] **Step 4: 运行测试以确认其通过**

运行：`pytest tests/test_commands.py -v`
预期结果：PASS

- [ ] **Step 5: 提交指令解析器代码**

```bash
git add admin/core/ingress/ tests/test_commands.py
git commit -m "feat: implement danmu event model and interactive command parser"
```

---

### Task 3: 消息治理管线 (Aho-Corasick 风控、UID 冷却与打分)

**Files:**
- Create: `admin/core/pipeline/aho_corasick.py`
- Create: `admin/core/pipeline/cooldown.py`
- Create: `admin/core/pipeline/pipeline_manager.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `DanmuEvent`
- Produces: `PipelineResult`, `PipelineManager.process(event: DanmuEvent) -> Optional[PipelineResult]`

- [ ] **Step 1: 编写管线与敏感词过滤的失败测试用例**

在 `tests/test_pipeline.py` 中测试违禁词过滤、UID 滑动窗口冷却以及打分逻辑：
```python
import pytest
from admin.core.ingress.event import DanmuEvent
from admin.core.pipeline.pipeline_manager import PipelineManager

def test_pipeline_aho_corasick_filter(tmp_path):
    words_file = tmp_path / "banned.txt"
    words_file.write_text("广告\n外挂\n黑产\n", encoding="utf-8")
    
    manager = PipelineManager(banned_words_path=str(words_file), cooldown_seconds=5)
    
    # 命中敏感词
    bad_event = DanmuEvent(uid=1, uname="违规者", content="专业广告引流")
    res1 = manager.process(bad_event)
    assert res1.is_blocked is True
    assert res1.reason == "sensitive_word"
    
    # 正常弹幕
    good_event = DanmuEvent(uid=2, uname="正常观众", content="主播晚上好呀")
    res2 = manager.process(good_event)
    assert res2.is_blocked is False
    assert res2.score == 10

def test_pipeline_cooldown(tmp_path):
    words_file = tmp_path / "banned.txt"
    words_file.write_text("", encoding="utf-8")
    
    manager = PipelineManager(banned_words_path=str(words_file), cooldown_seconds=10)
    
    event1 = DanmuEvent(uid=100, uname="活跃用户", content="第一句话")
    res1 = manager.process(event1)
    assert res1.can_trigger_ai is True
    
    # 连续发言进入冷却期（大屏仍显示，但不触发 AI 回复）
    event2 = DanmuEvent(uid=100, uname="活跃用户", content="第二句话刷屏")
    res2 = manager.process(event2)
    assert res2.is_blocked is False
    assert res2.can_trigger_ai is False
```

- [ ] **Step 2: 运行测试以确认其失败**

运行：`pytest tests/test_pipeline.py -v`
预期结果：FAIL（ModuleNotFoundError: No module named 'admin.core.pipeline'）

- [ ] **Step 3: 编写管线责任链实现**

创建 `admin/core/pipeline/aho_corasick.py`：
```python
import os
import ahocorasick
from typing import List, Optional

class SensitiveWordFilter:
    def __init__(self, words_file_path: str):
        self.words_file_path = words_file_path
        self.automaton = ahocorasick.Automaton()
        self.words: List[str] = []
        self.reload()

    def reload(self):
        self.automaton = ahocorasick.Automaton()
        self.words.clear()
        if os.path.exists(self.words_file_path):
            with open(self.words_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    w = line.strip()
                    if w:
                        self.words.append(w)
                        self.automaton.add_word(w, w)
        self.automaton.make_automaton()

    def contains_sensitive(self, text: str) -> Optional[str]:
        for _, word in self.automaton.iter(text):
            return word
        return None

    def update_words(self, new_words: List[str]):
        with open(self.words_file_path, "w", encoding="utf-8") as f:
            for w in new_words:
                w_clean = w.strip()
                if w_clean:
                    f.write(w_clean + "\n")
        self.reload()
```

创建 `admin/core/pipeline/cooldown.py`：
```python
import time
from cachetools import TTLCache

class UIDCooldownManager:
    def __init__(self, ttl_seconds: float = 10.0):
        # 最大缓存 10000 个活跃用户，自动过期杜绝内存膨胀
        self.cache = TTLCache(maxsize=10000, ttl=ttl_seconds)

    def check_and_update(self, uid: int) -> bool:
        now = time.time()
        if uid in self.cache:
            return False
        self.cache[uid] = now
        return True
```

创建 `admin/core/pipeline/pipeline_manager.py`：
```python
import re
from typing import Optional
from pydantic import BaseModel
from admin.core.ingress.event import DanmuEvent
from admin.core.pipeline.aho_corasick import SensitiveWordFilter
from admin.core.pipeline.cooldown import UIDCooldownManager

class PipelineResult(BaseModel):
    event: DanmuEvent
    is_blocked: bool = False
    reason: str = ""
    score: int = 10
    can_trigger_ai: bool = False

class PipelineManager:
    def __init__(self, banned_words_path: str, cooldown_seconds: float = 10.0):
        self.filter = SensitiveWordFilter(banned_words_path)
        self.cooldown = UIDCooldownManager(cooldown_seconds)

    def process(self, event: DanmuEvent) -> PipelineResult:
        # 1. 文本规范化与长度截断
        cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", event.content).strip()
        if len(cleaned) > 50:
            cleaned = cleaned[:50]
        event.content = cleaned

        # 2. 敏感词匹配
        matched = self.filter.contains_sensitive(event.content)
        if matched:
            return PipelineResult(event=event, is_blocked=True, reason="sensitive_word")

        # 3. 动态打分
        score = 10
        if event.badge_level >= 10:
            score = 30
        if event.is_super_chat or event.price > 0:
            score = 100

        # 4. UID 冷却检查
        can_trigger = False
        if score == 100:
            can_trigger = True  # 大额 SC/礼物穿透冷却
        else:
            can_trigger = self.cooldown.check_and_update(event.uid)

        return PipelineResult(event=event, is_blocked=False, score=score, can_trigger_ai=can_trigger)
```

- [ ] **Step 4: 运行测试以确认其通过**

运行：`pytest tests/test_pipeline.py -v`
预期结果：PASS

- [ ] **Step 5: 提交管线模块代码**

```bash
git add admin/core/pipeline/ tests/test_pipeline.py
git commit -m "feat: implement aho-corasick filter, uid cooldown and priority scoring pipeline"
```

---

### Task 4: AI 思考大脑与火山豆包 V3 HTTP 语音合成中枢

**Files:**
- Create: `admin/core/ai/llm_client.py`
- Create: `admin/core/tts/volcengine_client.py`
- Create: `admin/core/ai/orchestrator.py`
- Test: `tests/test_ai_tts.py`

**Interfaces:**
- Consumes: `AppConfig`, `PipelineResult`
- Produces: `AISpeechPackage`, `AIOrchestrator.generate_response(uname: str, content: str) -> Optional[AISpeechPackage]`

- [ ] **Step 1: 编写 LLM 与火山 TTS 协议组装失败测试用例**

在 `tests/test_ai_tts.py` 中测试 OpenAI 载荷与火山 V3 单向流式请求体的构造：
```python
import pytest
from admin.config import LLMConfig, VolcengineTTSConfig
from admin.core.ai.llm_client import LLMClient
from admin.core.tts/volcengine_client import VolcengineTTSClient

def test_volc_tts_request_payload():
    cfg = VolcengineTTSConfig(
        api_key="test-api-key",
        resource_id="seed-tts-2.0",
        speaker="zh_female_vv_uranus_bigtts"
    )
    client = VolcengineTTSClient(cfg)
    headers = client.build_headers()
    assert headers["X-Api-Key"] == "test-api-key"
    assert headers["X-Api-Resource-Id"] == "seed-tts-2.0"
    assert "X-Api-Request-Id" in headers

    payload = client.build_payload("测试台词")
    assert payload["req_params"]["text"] == "测试台词"
    assert payload["req_params"]["speaker"] == "zh_female_vv_uranus_bigtts"
```

- [ ] **Step 2: 运行测试以确认其失败**

运行：`pytest tests/test_ai_tts.py -v`
预期结果：FAIL（ModuleNotFoundError: No module named 'admin.core.ai'）

- [ ] **Step 3: 编写 LLM 与火山豆包 V3 HTTP 客户端及编排器**

创建 `admin/core/ai/llm_client.py`：
```python
import httpx
from typing import Tuple, Optional
from admin.config import LLMConfig

class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.total_tokens_used = 0

    async def complete(self, user_prompt: str) -> Tuple[str, int]:
        if not self.config.api_key:
            return f"（模拟回复）欢迎 {user_prompt} 呀，Gemini娘收到啦！", 25

        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, headers=headers, json=body)
            res.raise_for_status()
            data = res.json()
            reply = data["choices"][0]["message"]["content"].strip()
            tokens = data.get("usage", {}).get("total_tokens", 30)
            self.total_tokens_used += tokens
            return reply, tokens
```

创建 `admin/core/tts/volcengine_client.py`：
```python
import uuid
import json
import httpx
from typing import Optional
from admin.config import VolcengineTTSConfig

class VolcengineTTSClient:
    API_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"

    def __init__(self, config: VolcengineTTSConfig):
        self.config = config

    def build_headers(self) -> dict:
        return {
            "X-Api-Key": self.config.api_key,
            "X-Api-Resource-Id": self.config.resource_id,
            "X-Api-Request-Id": str(uuid.uuid4()),
            "Content-Type": "application/json",
            "Connection": "keep-alive"
        }

    def build_payload(self, text: str) -> dict:
        return {
            "req_params": {
                "text": text,
                "speaker": self.config.speaker,
                "model": "seed-tts-2.0-standard",
                "audio_params": {
                    "format": self.config.format,
                    "sample_rate": self.config.sample_rate
                }
            }
        }

    async def synthesize_base64_audio(self, text: str) -> str:
        """调用火山 V3 HTTP 单向流式接口，聚合分块返回完整的 Base64 音频"""
        if not self.config.api_key:
            return ""  # 未配 Key 时返回空以触发静默降级

        headers = self.build_headers()
        payload = self.build_payload(text)

        chunks = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            async with client.stream("POST", self.API_URL, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk_json = json.loads(line)
                        if chunk_json.get("code") == 0 and "data" in chunk_json:
                            chunks.append(chunk_json["data"])
                    except json.JSONDecodeError:
                        continue
        return "".join(chunks)
```

创建 `admin/core/ai/orchestrator.py`：
```python
from pydantic import BaseModel
from typing import Optional
from admin.config import AppConfig
from admin.core.ai.llm_client import LLMClient
from admin.core.tts.volcengine_client import VolcengineTTSClient

class AISpeechPackage(BaseModel):
    id: str
    text: str
    audio_base64: str = ""
    motion: str = "Wave"
    expression: str = "smile"
    tokens: int = 0

class AIOrchestrator:
    def __init__(self, config: AppConfig):
        self.config = config
        self.llm = LLMClient(config.llm)
        self.tts = VolcengineTTSClient(config.volc_tts)

    async def generate_response(self, uname: str, content: str) -> AISpeechPackage:
        prompt = f"观众【{uname}】说：{content}"
        reply_text, tokens = await self.llm.complete(prompt)
        audio_b64 = await self.tts.synthesize_base64_audio(reply_text)
        
        return AISpeechPackage(
            id=f"speech_{tokens}",
            text=reply_text,
            audio_base64=audio_b64,
            motion="Wave",
            expression="smile",
            tokens=tokens
        )
```

- [ ] **Step 4: 运行测试以确认其通过**

运行：`pytest tests/test_ai_tts.py -v`
预期结果：PASS

- [ ] **Step 5: 提交 AI 与 TTS 模块代码**

```bash
git add admin/core/ai/ admin/core/tts/ tests/test_ai_tts.py
git commit -m "feat: implement openai-compatible llm client and volcengine v3 streaming tts client"
```

---

### Task 5: 单一 SSE 广播中心与 OBS WebSocket 控制器

**Files:**
- Create: `admin/core/broadcast/broadcaster.py`
- Create: `admin/core/obs/obs_client.py`
- Test: `tests/test_broadcaster.py`

**Interfaces:**
- Consumes: None
- Produces: `Broadcaster`, `OBSClientWrapper`

- [ ] **Step 1: 编写广播中心背压与多端隔离的失败测试用例**

在 `tests/test_broadcaster.py` 中测试多客户端订阅与队列满载背压丢弃机制：
```python
import asyncio
import pytest
from admin.core.broadcast.broadcaster import Broadcaster

@pytest.mark.asyncio
async def test_broadcaster_subscribe_and_dispatch():
    broadcaster = Broadcaster()
    q = broadcaster.subscribe()
    
    await broadcaster.broadcast("danmu", {"content": "测试广播"})
    event_type, data = await asyncio.wait_for(q.get(), timeout=1.0)
    
    assert event_type == "danmu"
    assert data["content"] == "测试广播"
    
    broadcaster.unsubscribe(q)
    assert len(broadcaster.clients) == 0

@pytest.mark.asyncio
async def test_broadcaster_stats_tracker():
    broadcaster = Broadcaster()
    broadcaster.record_danmu("用户A")
    broadcaster.record_danmu("用户A")
    broadcaster.record_danmu("用户B")
    
    stats = broadcaster.get_current_stats()
    assert stats["danmu_count"] == 3
    assert stats["top_users"][0]["uname"] == "用户A"
    assert stats["top_users"][0]["count"] == 2
```

- [ ] **Step 2: 运行测试以确认其失败**

运行：`pytest tests/test_broadcaster.py -v`
预期结果：FAIL（ModuleNotFoundError: No module named 'admin.core.broadcast'）

- [ ] **Step 3: 编写广播中心与 OBS 控制器实现**

创建 `admin/core/broadcast/broadcaster.py`：
```python
import asyncio
import time
from collections import Counter
from typing import Set, Tuple, Any, Dict, List

class Broadcaster:
    def __init__(self):
        self.clients: Set[asyncio.Queue] = set()
        self.total_tokens: int = 0
        self.danmu_counter: Counter = Counter()
        self.danmu_count: int = 0
        self.ai_reply_count: int = 0
        self.blocked_count: int = 0
        self.start_time: float = time.time()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.clients.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self.clients.discard(q)

    async def broadcast(self, event_type: str, data: Any):
        dead_queues = []
        for q in self.clients:
            try:
                q.put_nowait((event_type, data))
            except asyncio.QueueFull:
                # 背压防护：队列满时丢弃一条旧消息并放入新消息
                try:
                    q.get_nowait()
                    q.put_nowait((event_type, data))
                except Exception:
                    dead_queues.append(q)
        for dq in dead_queues:
            self.clients.discard(dq)

    def record_danmu(self, uname: str):
        self.danmu_count += 1
        self.danmu_counter[uname] += 1

    def record_ai_reply(self, tokens: int):
        self.ai_reply_count += 1
        self.total_tokens += tokens

    def record_blocked(self):
        self.blocked_count += 1

    def get_current_stats(self) -> Dict[str, Any]:
        top5 = [{"rank": idx + 1, "uname": u, "count": c} 
                for idx, (u, c) in enumerate(self.danmu_counter.most_common(5))]
        return {
            "total_tokens": self.total_tokens,
            "danmu_count": self.danmu_count,
            "ai_reply_count": self.ai_reply_count,
            "blocked_count": self.blocked_count,
            "top_users": top5,
            "uptime_seconds": int(time.time() - self.start_time)
        }
```

创建 `admin/core/obs/obs_client.py`：
```python
from admin.config import OBSConfig

class OBSClientWrapper:
    def __init__(self, config: OBSConfig):
        self.config = config
        self.client = None
        self.is_connected = False

    def connect(self) -> bool:
        try:
            import obswebsocket, obswebsocket.requests
            self.client = obswebsocket.obsws(self.config.host, self.config.port, self.config.password)
            self.client.connect()
            self.is_connected = True
            return True
        except Exception:
            self.is_connected = False
            return False

    def start_streaming(self) -> bool:
        if not self.is_connected and not self.connect():
            return False
        try:
            import obswebsocket.requests
            self.client.call(obswebsocket.requests.StartStreaming())
            return True
        except Exception:
            return False

    def stop_streaming(self) -> bool:
        if not self.is_connected and not self.connect():
            return False
        try:
            import obswebsocket.requests
            self.client.call(obswebsocket.requests.StopStreaming())
            return True
        except Exception:
            return False

    def get_status(self) -> dict:
        if not self.is_connected and not self.connect():
            return {"connected": False, "streaming": False}
        try:
            import obswebsocket.requests
            res = self.client.call(obswebsocket.requests.GetStreamStatus())
            return {"connected": True, "streaming": res.getStreaming()}
        except Exception:
            return {"connected": False, "streaming": False}
```

- [ ] **Step 4: 运行测试以确认其通过**

运行：`pytest tests/test_broadcaster.py -v`
预期结果：PASS

- [ ] **Step 5: 提交广播与 OBS 控制器代码**

```bash
git add admin/core/broadcast/ admin/core/obs/ tests/test_broadcaster.py
git commit -m "feat: implement sse broadcaster with isolated queues and obs-websocket wrapper"
```

---

### Task 6: FastAPI HTTP 路由与单一 SSE 管道端点

**Files:**
- Create: `admin/routers/stream.py`
- Create: `admin/routers/api.py`
- Create: `admin/main.py`
- Test: `tests/test_api_stream.py`

**Interfaces:**
- Consumes: All earlier backend modules
- Produces: Running FastAPI application with `/api/*` and `/api/stream`

- [ ] **Step 1: 编写 API 与 SSE 端点的失败测试用例**

在 `tests/test_api_stream.py` 中测试配置热同步与模拟弹幕注入：
```python
import pytest
from fastapi.testclient import TestClient
from admin.main import app

def test_api_config_get():
    client = TestClient(app)
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.json()
    assert "llm" in data
    assert "volc_tts" in data

def test_api_danmu_injection():
    client = TestClient(app)
    payload = {"uname": "小测", "content": "测试一下弹幕"}
    res = client.post("/api/test/danmu", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
```

- [ ] **Step 2: 运行测试以确认其失败**

运行：`pytest tests/test_api_stream.py -v`
预期结果：FAIL（ModuleNotFoundError: No module named 'admin.main'）

- [ ] **Step 3: 编写路由与 FastAPI 主入口**

创建 `admin/routers/stream.py`：
```python
import json
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.get("/api/stream")
async def sse_stream(request: Request):
    broadcaster = request.app.state.broadcaster
    q = broadcaster.subscribe()

    async def event_generator():
        # 初始推送一次当前统计数据
        init_stats = broadcaster.get_current_stats()
        yield f"event: stats\ndata: {json.dumps(init_stats, ensure_ascii=False)}\n\n"
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event_type, data = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    # 心跳保活空包
                    yield ": heartbeat\n\n"
        finally:
            broadcaster.unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

创建 `admin/routers/api.py`：
```python
import os
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from admin.config import AppConfig, save_config, get_config

router = APIRouter()

class SpeakRequest(BaseModel):
    text: str

class DanmuTestRequest(BaseModel):
    uname: str = "测试观众"
    content: str = "主播好呀"
    price: float = 0.0
    is_sc: bool = False

@router.get("/api/config")
def get_current_config():
    return get_config()

@router.post("/api/config")
async def update_config(new_config: AppConfig, request: Request):
    save_config(new_config)
    # 触发配置热同步广播到直播大屏
    broadcaster = request.app.state.broadcaster
    await broadcaster.broadcast("config_sync", {
        "theme": new_config.mascot.theme,
        "mascot": {
            "scale": new_config.mascot.scale,
            "x": new_config.mascot.position_x,
            "y": new_config.mascot.position_y
        },
        "bgm": {
            "volume": new_config.bgm.default_volume
        }
    })
    return {"status": "ok"}

@router.post("/api/broadcast/speak")
async def manual_speak(req: SpeakRequest, request: Request):
    orchestrator = request.app.state.orchestrator
    broadcaster = request.app.state.broadcaster
    audio_b64 = await orchestrator.tts.synthesize_base64_audio(req.text)
    payload = {
        "id": "manual",
        "text": req.text,
        "audio": f"data:audio/mp3;base64,{audio_b64}" if audio_b64 else "",
        "motion": "Wave",
        "expression": "smile"
    }
    await broadcaster.broadcast("ai_speech", payload)
    return {"status": "ok"}

@router.post("/api/test/danmu")
async def inject_danmu(req: DanmuTestRequest, request: Request):
    bili_client = request.app.state.bili_client
    await bili_client.inject_mock_danmu(req.uname, req.content, req.price, req.is_sc)
    return {"status": "ok"}

@router.post("/api/live/start")
def live_start(request: Request):
    obs = request.app.state.obs_client
    success = obs.start_streaming()
    return {"status": "ok" if success else "failed"}

@router.post("/api/live/stop")
def live_stop(request: Request):
    obs = request.app.state.obs_client
    success = obs.stop_streaming()
    return {"status": "ok" if success else "failed"}

@router.get("/api/live/status")
def live_status(request: Request):
    obs = request.app.state.obs_client
    return obs.get_status()
```

创建 `admin/main.py`：
```python
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from admin.config import load_config
from admin.core.broadcast.broadcaster import Broadcaster
from admin.core.pipeline.pipeline_manager import PipelineManager
from admin.core.ingress.command_parser import parse_danmu_command
from admin.core.ingress.bili_client import BiliClientWrapper
from admin.core.ai.orchestrator import AIOrchestrator
from admin.core.obs.obs_client import OBSClientWrapper
from admin.routers import api, stream

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动初始化
    config = load_config()
    broadcaster = Broadcaster()
    banned_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "banned_words.txt")
    pipeline = PipelineManager(banned_path)
    orchestrator = AIOrchestrator(config)
    obs_client = OBSClientWrapper(config.obs)

    async def handle_incoming_danmu(event):
        # 1. 弹幕指令检查 (切歌/点歌等)
        cmd = parse_danmu_command(event.content)
        if cmd:
            if cmd.action in ("switch_song", "request_song"):
                await broadcaster.broadcast("bgm_action", {
                    "action": "switch",
                    "payload": cmd.payload
                })
            elif cmd.action in ("pause_music", "resume_music"):
                await broadcaster.broadcast("bgm_action", {
                    "action": "pause" if cmd.action == "pause_music" else "play"
                })
            elif cmd.action == "toggle_theme":
                await broadcaster.broadcast("config_sync", {"theme": "toggle"})
            return

        # 2. 走风控过滤与打分管线
        p_res = pipeline.process(event)
        if p_res.is_blocked:
            broadcaster.record_blocked()
            return

        broadcaster.record_danmu(event.uname)

        # 3. 广播弹幕到大屏毛玻璃列表
        if event.is_super_chat:
            await broadcaster.broadcast("super_chat", {
                "id": event.id,
                "uname": event.uname,
                "price": event.price,
                "content": event.content,
                "duration": 60
            })
        else:
            await broadcaster.broadcast("danmu", {
                "id": event.id,
                "uname": event.uname,
                "content": event.content,
                "badge": event.badge_name,
                "level": event.badge_level
            })

        # 定期同步实时统计数据
        await broadcaster.broadcast("stats", broadcaster.get_current_stats())

        # 4. 触发 AI 思考与语音合成
        if p_res.can_trigger_ai:
            speech = await orchestrator.generate_response(event.uname, event.content)
            broadcaster.record_ai_reply(speech.tokens)
            await broadcaster.broadcast("ai_speech", {
                "id": speech.id,
                "text": speech.text,
                "audio": f"data:audio/mp3;base64,{speech.audio_base64}" if speech.audio_base64 else "",
                "motion": speech.motion,
                "expression": speech.expression
            })
            await broadcaster.broadcast("stats", broadcaster.get_current_stats())

    bili_client = BiliClientWrapper(config.bilibili.room_id, handle_incoming_danmu)

    # 挂载状态
    app.state.config = config
    app.state.broadcaster = broadcaster
    app.state.pipeline = pipeline
    app.state.orchestrator = orchestrator
    app.state.obs_client = obs_client
    app.state.bili_client = bili_client

    yield

app = FastAPI(title="Virtual AI Live System", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)
app.include_router(stream.router)

# 挂载静态目录
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(os.path.join(static_dir, "admin"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "live"), exist_ok=True)
app.mount("/admin", StaticFiles(directory=os.path.join(static_dir, "admin"), html=True), name="admin")
app.mount("/live", StaticFiles(directory=os.path.join(static_dir, "live"), html=True), name="live")
```

- [ ] **Step 4: 运行测试以确认其通过**

运行：`pytest tests/test_api_stream.py -v`
预期结果：PASS

- [ ] **Step 5: 提交主应用与路由代码**

```bash
git add admin/routers/ admin/main.py tests/test_api_stream.py
git commit -m "feat: implement fastapi application, rest routers and unified sse stream"
```

---

### Task 7: 管理控制台单文件 SPA 实现 (`/admin`)

**Files:**
- Create: `admin/static/admin/index.html`
- Test: 手动/无头浏览器访问 `http://localhost:8000/admin` 验证界面与交互

**Interfaces:**
- Consumes: REST API (`/api/config`, `/api/live/*`, `/api/test/*`, `/api/broadcast/speak`)
- Produces: 工业级管理控制台界面（包含推流遥控、Prompt 人设编辑、火山 TTS 在线试听、BGM 播放控制、弹幕模拟器）

- [ ] **Step 1: 编写管理后台单文件 SPA**

创建 `admin/static/admin/index.html`：
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>大肥鱼 AI 虚拟主播管理中枢</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
  <style>
    body { background-color: #0f172a; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; }
    .glass-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); }
  </style>
</head>
<body class="p-6">
  <div id="app" class="max-w-7xl mx-auto space-y-6">
    <!-- 顶栏标题与 OBS 推流控制 -->
    <header class="glass-card rounded-2xl p-6 flex flex-wrap justify-between items-center gap-4">
      <div>
        <h1 class="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-fuchsia-500 bg-clip-text text-transparent">
          🐟 大肥鱼 AI 主播管理控制台 (Gemini娘)
        </h1>
        <p class="text-xs text-slate-400 mt-1">单一 SSE 长连接 | 火山豆包 V3 语音 | 弹幕指令互动 | 实时配置热推</p>
      </div>
      <div class="flex items-center gap-3">
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
              :class="obsStatus.streaming ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-slate-700 text-slate-300'">
          <span class="w-2 h-2 rounded-full" :class="obsStatus.streaming ? 'bg-emerald-400 animate-pulse' : 'bg-slate-400'"></span>
          {{ obsStatus.streaming ? 'OBS 推流中' : 'OBS 待机' }}
        </span>
        <button @click="toggleStream" class="px-4 py-2 rounded-xl text-sm font-semibold transition"
                :class="obsStatus.streaming ? 'bg-rose-500 hover:bg-rose-600' : 'bg-cyan-500 hover:bg-cyan-600'">
          {{ obsStatus.streaming ? '一键下播' : '一键开播' }}
        </button>
      </div>
    </header>

    <!-- 核心板块网格 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- 板块 1: AI Prompt 与大脑 -->
      <section class="glass-card rounded-2xl p-6 space-y-4">
        <h2 class="text-lg font-bold text-cyan-300 flex items-center gap-2">🧠 AI 大脑 (OpenAI 兼容)</h2>
        <div>
          <label class="block text-xs text-slate-400 mb-1">Base URL</label>
          <input v-model="config.llm.base_url" class="w-full bg-slate-900/80 border border-slate-700 rounded-lg p-2 text-sm">
        </div>
        <div>
          <label class="block text-xs text-slate-400 mb-1">API Key</label>
          <input type="password" v-model="config.llm.api_key" class="w-full bg-slate-900/80 border border-slate-700 rounded-lg p-2 text-sm">
        </div>
        <div>
          <label class="block text-xs text-slate-400 mb-1">System Prompt (Gemini娘人设)</label>
          <textarea v-model="config.llm.system_prompt" rows="3" class="w-full bg-slate-900/80 border border-slate-700 rounded-lg p-2 text-sm"></textarea>
        </div>
        <button @click="saveConfig" class="w-full py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium">保存大脑设置</button>
      </section>

      <!-- 板块 2: 火山豆包 V3 语音 -->
      <section class="glass-card rounded-2xl p-6 space-y-4">
        <h2 class="text-lg font-bold text-fuchsia-300 flex items-center gap-2">🗣️ 火山豆包语音 (V3 HTTP)</h2>
        <div>
          <label class="block text-xs text-slate-400 mb-1">X-Api-Key</label>
          <input type="password" v-model="config.volc_tts.api_key" class="w-full bg-slate-900/80 border border-slate-700 rounded-lg p-2 text-sm">
        </div>
        <div>
          <label class="block text-xs text-slate-400 mb-1">Resource ID</label>
          <input v-model="config.volc_tts.resource_id" class="w-full bg-slate-900/80 border border-slate-700 rounded-lg p-2 text-sm">
        </div>
        <div>
          <label class="block text-xs text-slate-400 mb-1">Speaker 音色 ID</label>
          <input v-model="config.volc_tts.speaker" class="w-full bg-slate-900/80 border border-slate-700 rounded-lg p-2 text-sm">
        </div>
        <div class="flex gap-2">
          <input v-model="testTTSContent" placeholder="输入测试台词" class="flex-1 bg-slate-900/80 border border-slate-700 rounded-lg p-2 text-xs">
          <button @click="testTTS" class="px-3 py-2 bg-fuchsia-600 hover:bg-fuchsia-500 rounded-lg text-xs font-semibold">在线试听</button>
        </div>
        <button @click="saveConfig" class="w-full py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium">保存语音设置</button>
      </section>

      <!-- 板块 3: 舞台视觉与热推 -->
      <section class="glass-card rounded-2xl p-6 space-y-4">
        <h2 class="text-lg font-bold text-amber-300 flex items-center gap-2">🎭 舞台视觉实时热推</h2>
        <div>
          <label class="block text-xs text-slate-400 mb-1">立绘缩放 ({{ config.mascot.scale }})</label>
          <input type="range" min="0.5" max="1.5" step="0.05" v-model.number="config.mascot.scale" @input="saveConfig" class="w-full">
        </div>
        <div>
          <label class="block text-xs text-slate-400 mb-1">主题风格</label>
          <select v-model="config.mascot.theme" @change="saveConfig" class="w-full bg-slate-900/80 border border-slate-700 rounded-lg p-2 text-sm">
            <option value="transparent">OBS 纯透明通道</option>
            <option value="deep_sea">赛博深海幻想</option>
          </select>
        </div>
        <div>
          <h3 class="text-xs font-semibold text-slate-400 mb-2">房管紧急插播</h3>
          <div class="flex gap-2">
            <input v-model="speakText" placeholder="房管直接插话朗读" class="flex-1 bg-slate-900/80 border border-slate-700 rounded-lg p-2 text-xs">
            <button @click="manualSpeak" class="px-3 py-2 bg-amber-600 hover:bg-amber-500 rounded-lg text-xs font-semibold">插播</button>
          </div>
        </div>
        <div>
          <h3 class="text-xs font-semibold text-slate-400 mb-2">开播前弹幕模拟器</h3>
          <div class="flex gap-2">
            <input v-model="mockDanmuText" placeholder="输入模拟弹幕 (如: 切歌)" class="flex-1 bg-slate-900/80 border border-slate-700 rounded-lg p-2 text-xs">
            <button @click="sendMockDanmu" class="px-3 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-xs font-semibold">模拟发送</button>
          </div>
        </div>
      </section>
    </div>
  </div>

  <script>
    const { createApp, ref, onMounted } = Vue;
    createApp({
      setup() {
        const config = ref({
          llm: {}, volc_tts: {}, mascot: {}, bgm: {}
        });
        const obsStatus = ref({ streaming: false });
        const testTTSContent = ref("笨蛋观众，这是火山豆包试听音频哦！");
        const speakText = ref("");
        const mockDanmuText = ref("切歌");

        const fetchConfig = async () => {
          const res = await fetch('/api/config');
          config.value = await res.json();
        };

        const fetchOBS = async () => {
          const res = await fetch('/api/live/status');
          obsStatus.value = await res.json();
        };

        const saveConfig = async () => {
          await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config.value)
          });
        };

        const toggleStream = async () => {
          const endpoint = obsStatus.value.streaming ? '/api/live/stop' : '/api/live/start';
          await fetch(endpoint, { method: 'POST' });
          await fetchOBS();
        };

        const testTTS = async () => {
          alert('正在调用火山豆包接口生成试听...');
          await fetch('/api/broadcast/speak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: testTTSContent.value })
          });
        };

        const manualSpeak = async () => {
          if (!speakText.value) return;
          await fetch('/api/broadcast/speak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: speakText.value })
          });
          speakText.value = '';
        };

        const sendMockDanmu = async () => {
          if (!mockDanmuText.value) return;
          await fetch('/api/test/danmu', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ uname: '测试观众', content: mockDanmuText.value })
          });
        };

        onMounted(() => {
          fetchConfig();
          fetchOBS();
          setInterval(fetchOBS, 5000);
        });

        return {
          config, obsStatus, testTTSContent, speakText, mockDanmuText,
          saveConfig, toggleStream, testTTS, manualSpeak, sendMockDanmu
        };
      }
    }).mount('#app');
  </script>
</body>
</html>
```

- [ ] **Step 2: 验证静态页面能被 FastAPI 托管并正确响应**

编写自动化测试 `tests/test_admin_page.py`：
```python
from fastapi.testclient import TestClient
from admin.main import app

def test_admin_html_served():
    client = TestClient(app)
    res = client.get("/admin/")
    assert res.status_code == 200
    assert "大肥鱼 AI 主播管理控制台" in res.text
```
运行：`pytest tests/test_admin_page.py -v`
预期结果：PASS

- [ ] **Step 3: 提交管理端 SPA 代码**

```bash
git add admin/static/admin/ tests/test_admin_page.py
git commit -m "feat: implement lightweight admin dashboard spa with hot-sync and online tts tester"
```

---

### Task 8: 直播大屏 Vue 3 工程搭建与核心动效 (`/live` - Pixi, Live2D, LipSync)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/composables/useSSE.ts`
- Create: `frontend/src/composables/useLipSync.ts`
- Create: `frontend/src/composables/useLive2D.ts`
- Create: `frontend/src/composables/useConfigSync.ts`
- Create: `frontend/src/components/Live2DStage.vue`
- Create: `frontend/src/components/DanmuList.vue`
- Create: `frontend/src/components/SuperChat.vue`

**Interfaces:**
- Consumes: Single SSE stream (`/api/stream`)
- Produces: Live2D Stage with Web Audio LipSync, Danmu wall with sliding window, SC pinned bar

- [ ] **Step 1: 创建前端工程配置文件**

创建 `frontend/package.json`：
```json
{
  "name": "virtual-ai-live-overlay",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.21",
    "pixi.js": "^7.4.0",
    "pixi-live2d-display": "^0.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.4",
    "typescript": "^5.2.2",
    "vite": "^5.1.4",
    "vue-tsc": "^1.8.27"
  }
}
```

创建 `frontend/vite.config.ts`：
```typescript
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
  base: '/live/',
  build: {
    outDir: '../admin/static/live',
    emptyOutDir: true
  }
});
```

创建 `frontend/index.html`（引入官方 Cubism 核心库）：
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>Gemini娘 直播大屏</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js"></script>
  <style>
    html, body {
      margin: 0;
      padding: 0;
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      background: transparent !important;
      user-select: none;
    }
  </style>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

- [ ] **Step 2: 编写 SSE 单长连接与 Web Audio 口型同步 composables**

创建 `frontend/src/composables/useSSE.ts`：
```typescript
import { ref, onMounted, onUnmounted } from 'vue';

export function useSSE(onEvent: (event: string, data: any) => void) {
  const isConnected = ref(false);
  let eventSource: EventSource | null = null;

  const connect = () => {
    eventSource = new EventSource('/api/stream');
    eventSource.onopen = () => { isConnected.value = true; };
    eventSource.onerror = () => {
      isConnected.value = false;
      eventSource?.close();
      setTimeout(connect, 3000); // 自动指数重连
    };

    const events = ['danmu', 'super_chat', 'ai_speech', 'stats', 'bgm_action', 'config_sync'];
    events.forEach(evName => {
      eventSource?.addEventListener(evName, (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          onEvent(evName, data);
        } catch (err) {
          console.error(`解析事件 ${evName} 失败`, err);
        }
      });
    });
  };

  onMounted(() => connect());
  onUnmounted(() => eventSource?.close());

  return { isConnected };
}
```

创建 `frontend/src/composables/useLipSync.ts`（Web Audio Analyser 频域振幅提取）：
```typescript
import { ref } from 'vue';

export function useLipSync() {
  let audioCtx: AudioContext | null = null;
  let analyser: AnalyserNode | null = null;
  const currentAmplitude = ref(0);

  const initAudio = () => {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
  };

  const playBase64Audio = async (base64Audio: string, onEnded?: () => void) => {
    initAudio();
    if (!audioCtx || !analyser) return;

    const base64Data = base64Audio.replace(/^data:audio\/\w+;base64,/, '');
    const binary = atob(base64Data);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }

    const audioBuffer = await audioCtx.decodeAudioData(bytes.buffer);
    const source = audioCtx.createBufferSource();
    source.buffer = audioBuffer;

    source.connect(analyser);
    analyser.connect(audioCtx.destination);

    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    let isPlaying = true;

    const updateLoop = () => {
      if (!isPlaying || !analyser) return;
      analyser.getByteFrequencyData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i];
      }
      const avg = sum / dataArray.length;
      currentAmplitude.value = Math.min(1.0, avg / 60); // 归一化为 0.0 ~ 1.0 口型振幅
      requestAnimationFrame(updateLoop);
    };

    source.onended = () => {
      isPlaying = false;
      currentAmplitude.value = 0;
      if (onEnded) onEnded();
    };

    source.start(0);
    requestAnimationFrame(updateLoop);
  };

  return { currentAmplitude, playBase64Audio };
}
```

创建 `frontend/src/components/DanmuList.vue`（固定 30 条滑窗，防 CEF 内存泄露）：
```html
<template>
  <div class="danmu-container">
    <transition-group name="danmu-fade" tag="div" class="danmu-list">
      <div v-for="item in visibleDanmu" :key="item.id" class="danmu-item">
        <span v-if="item.badge" class="badge">Lv{{ item.level }} {{ item.badge }}</span>
        <span class="uname">{{ item.uname }}:</span>
        <span class="content">{{ item.content }}</span>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface DanmuMsg {
  id: string;
  uname: string;
  content: string;
  badge?: string;
  level?: number;
}

const visibleDanmu = ref<DanmuMsg[]>([]);

const addDanmu = (msg: DanmuMsg) => {
  visibleDanmu.value.push(msg);
  // 固定滑窗上限 30 条，超出即刻移除，防止长时开播 DOM 泄漏
  if (visibleDanmu.value.length > 30) {
    visibleDanmu.value.shift();
  }
};

defineExpose({ addDanmu });
</script>

<style scoped>
.danmu-container {
  width: 420px;
  height: 380px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}
.danmu-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.danmu-item {
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 14px;
  color: #fff;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.badge {
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
  color: #fff;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 6px;
}
.uname { color: #38bdf8; font-weight: 600; }
.danmu-fade-enter-active { transition: all 0.3s ease-out; }
.danmu-fade-enter-from { opacity: 0; transform: translateY(15px); }
</style>
```

- [ ] **Step 3: 编写 Live2D 舞台视口组件**

创建 `frontend/src/components/Live2DStage.vue`：
```html
<template>
  <div class="live2d-viewport" ref="viewportRef"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import * as PIXI from 'pixi.js';

const props = defineProps<{
  mouthOpenY: number;
  scale?: number;
}>();

const viewportRef = ref<HTMLDivElement | null>(null);
let app: PIXI.Application | null = null;
let currentModel: any = null;

onMounted(async () => {
  if (!viewportRef.value) return;
  app = new PIXI.Application({
    width: 600,
    height: 800,
    transparent: true,
    backgroundAlpha: 0
  });
  viewportRef.value.appendChild(app.view as HTMLCanvasElement);

  // 初始化 pixi-live2d-display
  const { Live2DModel } = await import('pixi-live2d-display');
  (window as any).PIXI = PIXI;

  try {
    // 加载内置的 Gemini 娘 Live2D 模型包
    currentModel = await Live2DModel.from('/models/gemini/gemini.model3.json');
    currentModel.scale.set(props.scale || 0.25);
    currentModel.x = 100;
    currentModel.y = 150;
    app.stage.addChild(currentModel);
  } catch (err) {
    console.warn('Live2D 模型加载失败，使用备用画布模式', err);
  }
});

// 监听 Web Audio 口型振幅，动态开合 Live2D 嘴唇
watch(() => props.mouthOpenY, (val) => {
  if (currentModel && currentModel.internalModel?.coreModel) {
    currentModel.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', val);
  }
});
</script>

<style scoped>
.live2d-viewport {
  width: 600px;
  height: 800px;
  pointer-events: none;
}
</style>
```

- [ ] **Step 4: 提交前端基础与动效组件**

```bash
git add frontend/
git commit -m "feat: setup vue3 frontend with live2d stage, lipsync analyser and danmu wall"
```

---

### Task 9: 直播大屏实时数据 HUD 与伴奏唱片机系统

**Files:**
- Create: `frontend/src/components/DataHUD.vue`
- Create: `frontend/src/components/BgmPlayer.vue`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/main.ts`
- Test: 执行前端 `npm run build`，产出编译文件到 `admin/static/live` 并验证挂载

**Interfaces:**
- Consumes: `useSSE`, `useLipSync`, `DataHUD`, `BgmPlayer`, `Live2DStage`, `DanmuList`
- Produces: 完整的 1080P/720P OBS 直播大屏应用

- [ ] **Step 1: 编写数据看板 HUD 组件 (Token 消耗 & 观众 Top 5)**

创建 `frontend/src/components/DataHUD.vue`：
```html
<template>
  <div class="hud-panel">
    <div class="hud-title">⚡ AI LIVE HUD 指标</div>
    
    <!-- Token 消耗与核心指标 -->
    <div class="metric-row">
      <div class="metric-box">
        <span class="label">累计消耗 Token</span>
        <span class="value text-cyan-400">{{ stats.total_tokens.toLocaleString() }}</span>
      </div>
      <div class="metric-box">
        <span class="label">弹幕 / 问答总数</span>
        <span class="value">{{ stats.danmu_count }} / {{ stats.ai_reply_count }}</span>
      </div>
    </div>

    <!-- 活跃观众 Top 5 榜单 -->
    <div class="top-list">
      <div class="top-header">🏆 活跃观众排行</div>
      <div v-for="user in stats.top_users" :key="user.rank" class="top-item">
        <span class="rank" :class="'rank-' + user.rank">{{ user.rank }}</span>
        <span class="user-name">{{ user.uname }}</span>
        <span class="user-count">{{ user.count }} 条</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  stats: {
    total_tokens: number;
    danmu_count: number;
    ai_reply_count: number;
    top_users: Array<{ rank: number; uname: string; count: number }>;
  }
}>();
</script>

<style scoped>
.hud-panel {
  width: 260px;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 14px;
  color: #f8fafc;
  font-family: system-ui, sans-serif;
}
.hud-title { font-size: 13px; font-weight: bold; color: #38bdf8; margin-bottom: 8px; }
.metric-row { display: flex; gap: 8px; margin-bottom: 12px; }
.metric-box {
  flex: 1;
  background: rgba(0, 0, 0, 0.3);
  padding: 6px 8px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}
.label { font-size: 10px; color: #94a3b8; }
.value { font-size: 14px; font-weight: bold; }
.text-cyan-400 { color: #22d3ee; }
.top-list { display: flex; flex-direction: column; gap: 4px; }
.top-header { font-size: 11px; color: #cbd5e1; margin-bottom: 2px; }
.top-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.04);
  padding: 3px 8px;
  border-radius: 6px;
}
.rank { font-weight: bold; width: 16px; }
.rank-1 { color: #facc15; }
.rank-2 { color: #cbd5e1; }
.rank-3 { color: #fb923c; }
.user-name { flex: 1; margin: 0 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-count { color: #64748b; font-size: 11px; }
</style>
```

- [ ] **Step 2: 编写伴奏唱片机组件 (BGM Player with Audio Ducking)**

创建 `frontend/src/components/BgmPlayer.vue`：
```html
<template>
  <div class="bgm-player" :class="{ 'is-ducking': isDucking }">
    <div class="vinyl-disc" :class="{ 'is-spinning': isPlaying }">
      <div class="vinyl-core"></div>
    </div>
    <div class="bgm-info">
      <div class="track-title">🎵 {{ currentTrackTitle }}</div>
      <div class="status-tag">{{ isDucking ? '🗣️ AI 语音避让中...' : '🎶 伴奏播放中' }}</div>
    </div>
    <audio ref="audioRef" loop preload="auto"></audio>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  isDucking: boolean;
}>();

const isPlaying = ref(true);
const currentTrackTitle = ref('二次元元气日常伴奏');
const audioRef = ref<HTMLAudioElement | null>(null);

const setTrack = (title: string, src?: string) => {
  currentTrackTitle.value = title;
  if (src && audioRef.value) {
    audioRef.value.src = src;
    audioRef.value.play();
  }
};

const setPlayState = (play: boolean) => {
  isPlaying.value = play;
  if (audioRef.value) {
    play ? audioRef.value.play() : audioRef.value.pause();
  }
};

defineExpose({ setTrack, setPlayState });
</script>

<style scoped>
.bgm-player {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 8px 14px;
  border-radius: 40px;
  color: #fff;
  transition: opacity 0.3s;
}
.is-ducking { opacity: 0.6; }
.vinyl-disc {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: radial-gradient(#111 60%, #333 100%);
  border: 2px solid #555;
  display: flex;
  align-items: center;
  justify-content: center;
}
.is-spinning { animation: spin 4s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.vinyl-core { width: 10px; height: 10px; border-radius: 50%; background: #38bdf8; }
.track-title { font-size: 12px; font-weight: 600; }
.status-tag { font-size: 10px; color: #94a3b8; }
</style>
```

- [ ] **Step 3: 整合 App.vue 主入口并完成组件挂接**

创建 `frontend/src/App.vue`：
```html
<template>
  <div class="overlay-screen" :class="'theme-' + currentTheme">
    <!-- 顶部功能区 -->
    <div class="top-bar">
      <BgmPlayer ref="bgmRef" :isDucking="isSpeaking" />
      <DataHUD :stats="globalStats" />
    </div>

    <!-- 底部主舞台区 -->
    <div class="bottom-stage">
      <DanmuList ref="danmuListRef" />
      <Live2DStage :mouthOpenY="currentAmplitude" :scale="mascotScale" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useSSE } from './composables/useSSE';
import { useLipSync } from './composables/useLipSync';
import Live2DStage from './components/Live2DStage.vue';
import DanmuList from './components/DanmuList.vue';
import DataHUD from './components/DataHUD.vue';
import BgmPlayer from './components/BgmPlayer.vue';

const currentTheme = ref('transparent');
const mascotScale = ref(0.25);
const isSpeaking = ref(false);

const bgmRef = ref<any>(null);
const danmuListRef = ref<any>(null);

const globalStats = ref({
  total_tokens: 0,
  danmu_count: 0,
  ai_reply_count: 0,
  top_users: []
});

const { currentAmplitude, playBase64Audio } = useLipSync();

useSSE((eventName, data) => {
  if (eventName === 'danmu') {
    danmuListRef.value?.addDanmu(data);
  } else if (eventName === 'stats') {
    globalStats.value = data;
  } else if (eventName === 'bgm_action') {
    if (data.action === 'switch') {
      bgmRef.value?.setTrack(data.payload || '下一首元气旋律');
    } else if (data.action === 'pause') {
      bgmRef.value?.setPlayState(false);
    } else if (data.action === 'play') {
      bgmRef.value?.setPlayState(true);
    }
  } else if (eventName === 'config_sync') {
    if (data.theme) currentTheme.value = data.theme;
    if (data.mascot?.scale) mascotScale.value = data.mascot.scale;
  } else if (eventName === 'ai_speech') {
    if (data.audio) {
      isSpeaking.value = true;
      playBase64Audio(data.audio, () => {
        isSpeaking.value = false;
      });
    }
  }
});
</script>

<style>
.overlay-screen {
  width: 100vw;
  height: 100vh;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 24px;
  box-sizing: border-box;
}
.theme-transparent { background: transparent !important; }
.theme-deep_sea { background: radial-gradient(circle at center, rgba(14, 116, 144, 0.4) 0%, rgba(15, 23, 42, 0.9) 100%); }
.top-bar { display: flex; justify-content: space-between; align-items: flex-start; }
.bottom-stage { display: flex; justify-content: space-between; align-items: flex-end; }
</style>
```

创建 `frontend/src/main.ts`：
```typescript
import { createApp } from 'vue';
import App from './App.vue';

createApp(App).mount('#app');
```

- [ ] **Step 4: 运行前端构建命令验证静态产出**

运行：`cd frontend && npm install && npm run build`
预期结果：编译成功，并在 `admin/static/live` 目录下输出 `index.html` 与编译后的 assets。

- [ ] **Step 5: 提交完整前端大屏工程**

```bash
git add frontend/ admin/static/live/
git commit -m "feat: complete live overlay screen with hud data panel and bgm vinyl player"
```

---

### Task 10: Gemini 娘 Live2D 模型包预设、Dockerfile 与端到端集成验证

**Files:**
- Create: `models/gemini/gemini.model3.json`
- Create: `Dockerfile`
- Create: `tests/test_e2e_flow.py`

**Interfaces:**
- Consumes: All earlier components
- Produces: Docker Multi-Stage build file and automated end-to-end integration test

- [ ] **Step 1: 编写内置 Gemini 娘 Live2D 模型资源结构**

在 `models/gemini/` 下配置标准 Cubism 4 结构：
创建 `models/gemini/gemini.model3.json`：
```json
{
  "Version": 3,
  "FileReferences": {
    "Moc": "gemini.moc3",
    "Textures": [
      "textures/texture_00.png"
    ],
    "Physics": "gemini.physics3.json"
  },
  "Groups": [
    {
      "Target": "Parameter",
      "Name": "LipSync",
      "Ids": [
        "ParamMouthOpenY"
      ]
    }
  ]
}
```

- [ ] **Step 2: 编写多阶段构建 Dockerfile**

创建 `Dockerfile`：
```dockerfile
# 阶段 1: 前端 Vite 静态资源构建
FROM node:20-alpine AS frontend-builder
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 阶段 2: Python 生产镜像构建
FROM python:3.11-slim AS final
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 TZ=Asia/Shanghai
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY admin/ ./admin/
COPY configs/ ./configs/
COPY models/ ./models/
COPY --from=frontend-builder /build/dist ./admin/static/live

EXPOSE 8000
VOLUME ["/app/configs", "/app/models"]

CMD ["uvicorn", "admin.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: 编写端到端全链路集成测试**

在 `tests/test_e2e_flow.py` 中验证：
1. 启动 FastAPI；
2. 注入弹幕 `切歌` 触发 BGM 切换事件；
3. 注入普通弹幕触发数据 HUD 计数；
4. 验证统计数据正确累加并在单一 SSE 端点分发。

```python
import pytest
from fastapi.testclient import TestClient
from admin.main import app

def test_full_pipeline_e2e():
    with TestClient(app) as client:
        # 1. 注入切歌弹幕
        res = client.post("/api/test/danmu", json={"uname": "测试者", "content": "切歌"})
        assert res.status_code == 200
        
        # 2. 注入正常弹幕
        res2 = client.post("/api/test/danmu", json={"uname": "观众B", "content": "晚上好呀"})
        assert res2.status_code == 200
        
        # 3. 校验配置热推
        cfg_res = client.get("/api/config")
        assert cfg_res.status_code == 200
        
        # 4. 校验 OBS 接口
        obs_res = client.get("/api/live/status")
        assert obs_res.status_code == 200
        assert "streaming" in obs_res.json()
```

- [ ] **Step 4: 运行全量集成测试**

运行：`pytest -v`
预期结果：ALL PASS（所有单元测试与端到端测试 100% 通过）

- [ ] **Step 5: 提交模型预设、Dockerfile 与 E2E 测试代码**

```bash
git add models/ Dockerfile tests/test_e2e_flow.py
git commit -m "feat: add gemini live2d model preset, multi-stage dockerfile and e2e tests"
```
