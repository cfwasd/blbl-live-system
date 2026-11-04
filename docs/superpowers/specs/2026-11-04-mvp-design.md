# 虚拟AI人物直播弹幕驱动系统 (全功能 MVP) 架构与技术设计规范

| 属性 | 内容 |
| :--- | :--- |
| **文档名称** | 虚拟AI人物直播弹幕驱动系统 (全功能 MVP) 详细设计规范 |
| **版本** | v1.0.0 (MVP 规格) |
| **日期** | 2026-11-04 |
| **状态** | 设计完成 / 待实施 |
| **核心技术** | FastAPI, blivedm, pyahocorasick, Volcengine Doubao TTS (v3), OpenAI API, SSE, Vue 3, Pixi.js (v7), Live2D Cubism 4, OBS-WebSocket |

---

## 1. 项目愿景与 MVP 核心目标

本项目面向 B站（Bilibili）无人/半无人二次元虚拟主播直播间，通过纯自动化、低延迟、高韧性的全栈技术体系，实现观众弹幕驱动的交互直播。

### MVP 核心交付目标
1. **统一通信长连接**：后端与直播大屏之间收敛为**单一 HTTP SSE 流式通道 (`GET /api/stream`)**，全量事件（弹幕、SC、AI 语音、数据统计、BGM 指令、配置同步）均通过该连接推送，保障 0 冗余开销与 OBS CEF 内核的高度稳定性。
2. **直播展示大屏 (`/live`)**：
   - **Gemini 娘 Live2D 动态立绘**：内置蓝紫星芒风格化二次元 Live2D 预设，支持呼吸、眨眼、视线跟踪与 Web Audio 声波实时口型张合（`ParamMouthOpenY` LipSync）。
   - **科技感数据看板 (Data HUD)**：实时动态展示累计消耗 Token、活跃观众发言榜 Top 5、弹幕总计与拦截指标。
   - **沉浸式伴奏唱片机 (BGM Player)**：旋转黑胶唱片与音频动效，支持 AI 说话时音量平滑避让（Audio Ducking 至 8%）。
   - **拟态毛玻璃弹幕墙 & SC 置顶**：固定滑窗淘汰防 CEF 内存泄露，全透明通道推流。
3. **弹幕互动指令驱动 (Danmu Commands)**：观众通过发送 `切歌`、`点歌 <歌名>`、`暂停音乐`、`切背景` 等弹幕直接控制伴奏与画面，彻底摆脱 OBS 窗口对物理键盘的依赖。
4. **管理控制中枢 (`/admin`)**：
   - FastAPI 静态托管单文件 SPA（Vue 3 CDN + Tailwind CSS，免打包）。
   - 提供 OBS 推流一键遥控、AI Prompt 与 OpenAI 兼容模型配置、火山引擎豆包 V3 HTTP 语音参数配置与在线试听、违禁词在线维护、弹幕动效模拟器。
   - **管理端修改实时热同步 (Hot-Sync)**：管理端调参即时推送至大屏平滑生效，0 刷新、0 黑屏。

---

## 2. 总体逻辑架构与五层拓扑

系统严格遵循“**重核轻端、单向驱动**”的设计原则，将繁重的协议解析、风控过滤、大模型推理与音频分块合成全部收敛在 Python 后端中枢，前端大屏定位为纯净的只读渲染终端。

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   1. 外部数据源 (External Source)                       │
│  B站直播间弹幕广播网关 (live-open.bilibili.com / WebSocket 协议)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ WebSocket (blivedm)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 2. 协议接入层 (Ingress Layer)                          │
│  • 长短房间号自动换算 (Bilibili 官方 API)                                │
│  • blivedm 异步客户端：Zlib/Brotli 自动解包、30s 心跳保活与指数退避断线重连 │
│  • 模拟弹幕/SC/礼物生成器 (供开播前自检)                                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ 原始事件对象 (Event Object)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 3. 消息治理与指令管线 (Pipeline Layer)                  │
│  • 格式清洗与安全截断 (不可见字符过滤、防长文本爆框)                   │
│  • 弹幕指令解析器 (拦截 切歌 / 点歌 / 暂停 / 切背景 转换为系统动作)     │
│  • Aho-Corasick 多模式违禁词风控 (纳秒级匹配 banned_words.txt)         │
│  • UID 滑动窗口频控 (LRU + TTL 缓存，防刷屏并杜绝内存膨胀)              │
│  • 动态优先级加权评分 (普通:10 / 粉丝牌:30 / 礼物与SC:100)              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ 合规消息 / 优先入选队列
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 4. AI 智能与语音编排中枢 (AI Orchestrator)              │
│  • 统计追踪器：累加 Token 消耗数、统计观众发言 Top 5                   │
│  • OpenAI 兼容 LLM 客户端：搭载 Gemini 娘傲娇元气人设 Prompt           │
│  • 流式分句断句与触发器                                               │
│  • 火山引擎豆包 V3 HTTP 流式 TTS (seed-tts-2.0 / Base64 音频合成)       │
│  • 广播中心 (Broadcaster)：维护每个连入客户端的独立 asyncio.Queue       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ 单一 HTTP SSE 长连接 (/api/stream)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 5. 视图与推流宿主层 (View Layer)                        │
│  OBS Studio (4455 WebSocket 遥控推流 / CEF 浏览器源 Alpha 透明通道)      │
│  ├── /live 直播大屏：Live2D Gemini 立绘 + LipSync + HUD + BGM + 弹幕流 │
│  └── /admin 管理后台：SPA 全功能监控看板、调参热同步 (Hot-Sync)          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 工程目录与模块划分

```text
.
├── admin/                         # Python 后端主服务与管理端静态托管
│   ├── core/                      # 核心业务中枢
│   │   ├── ingress/               # 接入层：blivedm 适配器、长短号转换、模拟注入器
│   │   ├── pipeline/              # 消息治理：清洗器、指令解析器、Aho-Corasick 风控、UID 冷却
│   │   ├── ai/                    # AI 思考中枢：OpenAI 兼容 LLM 客户端、Prompt 管理、Token 统计
│   │   ├── tts/                   # 火山豆包 V3 HTTP 语音合成客户端 (seed-tts-2.0, chunked 解码)
│   │   ├── broadcast/             # SSE 广播中心 (多客户端隔离队列、背压丢弃)
│   │   └── obs/                   # OBS-WebSocket 4455 控制器 (连接、推流开播/停播)
│   ├── routers/                   # HTTP 接口路由
│   │   ├── api.py                 # RESTful 配置更新、房管插播、上下播控制、TTS 试听接口
│   │   └── stream.py              # 单一 SSE 端点 (/api/stream)
│   ├── static/                    # 静态托管资源目录
│   │   ├── admin/                 # 管理控制台 (Vue 3 CDN + Tailwind 单文件 SPA: index.html)
│   │   └── live/                  # 直播大屏由 frontend 编译生成的静态产物 (由 Vite build 产出)
│   ├── config.py                  # Pydantic 动态配置加载器 (读取/保存 configs/config.yaml)
│   └── main.py                    # FastAPI 启动入口与生命周期 (Lifespan)
├── frontend/                      # 直播大屏 Vue 3 工程 (专为 OBS CEF 打造)
│   ├── src/
│   │   ├── components/            # 核心视图组件
│   │   │   ├── Live2DStage.vue    # Pixi.js + pixi-live2d-display 舞台视口
│   │   │   ├── DataHUD.vue        # 科技感数据面板 (Token 计数、Top 5 观众榜、统计指标)
│   │   │   ├── BgmPlayer.vue      # 旋转黑胶唱片机、歌名滚动、音频律动条与自动避让
│   │   │   ├── DanmuList.vue      # 拟态毛玻璃弹幕流动墙 (滑窗淘汰限制防内存泄露)
│   │   │   └── SuperChat.vue      # SC 醒目留言与大额礼物置顶倒计时卡片
│   │   ├── composables/           # 逻辑复用
│   │   │   ├── useSSE.ts          # 单一 EventSource 长连接与自动重连
│   │   │   ├── useLive2D.ts       # 模型加载、动作/表情切换、视线跟踪
│   │   │   ├── useLipSync.ts      # Web Audio API 频域振幅提取与实时嘴型开合映射
│   │   │   └── useConfigSync.ts   # 后台配置热推同步 (主题切换、立绘缩放/位移等)
│   │   ├── App.vue                # 大屏主界面 (全透明背景、多组件层叠)
│   │   └── main.ts
│   ├── index.html                 # 引入 live2dcubismcore.min.js
│   ├── package.json
│   └── vite.config.ts
├── models/                        # Live2D 模型资源目录 (挂载外部资产)
│   └── gemini/                    # 内置 Gemini 娘 Live2D 演示模型包 (.model3.json)
├── configs/                       # 运行时持久化配置
│   ├── config.yaml                # 房间号、LLM 配置、火山 TTS 配置、OBS 端口密码
│   └── banned_words.txt           # 敏感词词库 (Aho-Corasick 在线更新并持久化)
├── tests/                         # 自动化测试用例
│   ├── test_pipeline.py           # 消息过滤责任链与敏感词测试
│   ├── test_commands.py           # 弹幕指令识别测试 (切歌/点歌等)
│   ├── test_ai_tts.py             # LLM 与火山豆包 TTS 协议契约测试
│   └── test_broadcaster.py        # 广播中心多客户端背压隔离测试
├── requirements.txt               # 后端 Python 依赖
└── Dockerfile                     # Multi-Stage 多阶段构建打包文件
```

---

## 4. 详细组件与流程设计

### 4.1 弹幕接入与指令解析 (Ingress & Command Dispatcher)
1. **真实长房间号换算**：启动时调用 `https://api.live.bilibili.com/room/v1/Room/room_init?id={input_id}` 换算真实 room_id。
2. **弹幕指令解析规则**：
   - 正则 `^(切歌|下一首)$`：触发 BGM 曲库顺跳，广播 `event: bgm_action`。
   - 正则 `^点歌\s+(.+)$`：提取指定歌名，在曲库匹配后广播 `event: bgm_action`。
   - 正则 `^(暂停音乐|恢复音乐)$`：广播伴奏启闭指令。
   - 正则 `^(切背景|透明)$`：切换大屏透明/场景背景。
   - 指令命中后，生成系统交互日志，可联动触发 Gemini 娘简短回复：“收到【观众】的点歌啦~”。

### 4.2 消息风控管线 (Pipeline Layer)
1. **格式清洗**：正则剔除全角空格刷屏、控制字符，截断正文至 50 字符以内。
2. **Aho-Corasick 算法**：利用 `pyahocorasick` 构建 Trie 树。单次扫描时间复杂度 $O(N)$，纳秒级过滤违禁词，命中直接丢弃并累加 `blocked_count`。
3. **UID 滑动窗口冷却**：同一用户发言触发 AI 回复后进入 N 秒（默认 10s）冷却期，基于 `cachetools.TTLCache` 自动淘汰过期 UID，防止内存膨胀。
4. **优先级打分**：
   - 普通弹幕：10 分；
   - 粉丝勋章 > 10 级：30 分；
   - 礼物打赏 / SuperChat：100 分。

### 4.3 AI 思考与火山豆包 V3 TTS 编排 (AI Orchestrator)
1. **LLM 异步思考**：
   - 接口格式：OpenAI 兼容 `/v1/chat/completions`。
   - 人设 System Prompt：
     > “你是 Gemini 娘，元气、呆萌、带有一点点傲娇科技感的二次元虚拟主播。回复观众弹幕要求：语言风格可爱自然，回答极度简练（严格限制在 30 字以内），富有情绪起伏。”
   - 统计累加：从响应中提取 `usage.total_tokens`，累加至全局实时指标。
2. **火山豆包 V3 HTTP 流式 TTS**：
   - **请求地址**：`https://openspeech.bytedance.com/api/v3/tts/unidirectional`
   - **HTTP Headers**：
     - `X-Api-Key`: 用户配置的 API Key
     - `X-Api-Resource-Id`: `seed-tts-2.0`（或用户指定模型）
     - `X-Api-Request-Id`: UUID 字符串
     - `Content-Type`: `application/json`
   - **Body 载荷**：
     ```json
     {
       "req_params": {
         "text": "回复文本",
         "speaker": "zh_female_vv_uranus_bigtts",
         "audio_params": {
           "format": "mp3",
           "sample_rate": 24000
         }
       }
     }
     ```
   - **分块处理**：使用 `httpx` 异步读取 HTTP Chunked 响应，按行提取 JSON 分块中的 `data`（Base64 音频），合并生成完整 Base64 音频 Payload。

### 4.4 广播中心 (Broadcaster)
- 采用 **发布-订阅 (Pub/Sub) + 客户端专属有界队列**。
- 为每个连入 `/api/stream` 的连接分配 `asyncio.Queue(maxsize=100)`。
- 广播时执行非阻塞 `put_nowait`，若队列满（CEF 渲染卡顿），丢弃队列头部最低权重的普通弹幕，保障 SC/礼物与 AI 音频包投递。

---

## 5. 前端大屏与管理后台实现

### 5.1 直播大屏 (`/live`) 视觉与交互
1. **全透明与分层渲染**：
   - `html, body { background: transparent !important; margin: 0; overflow: hidden; }`
   - 底层：WebGL Canvas，Pixi.js 挂载 Gemini Live2D 模型；
   - 中层：粒子效果；
   - 顶层：Vue 响应式 DOM 挂载数据 HUD、BGM 唱片机、弹幕流动墙。
2. **Web Audio 动态口型同步 (LipSync)**：
   - 收到 `ai_speech` 事件，通过 Web Audio API 将 Base64 解码为音频缓冲并发起播放；
   - 创建 `AnalyserNode`（FFT 采样），在 `requestAnimationFrame` 循环中提取实时 RMS 音频振幅（0.0 ~ 1.0）；
   - 将振幅动态写入 Live2D 模型的 `internalModel.coreModel.setParameterValueById('ParamMouthOpenY', amplitude)`，实现逼真的声波口型张合。
3. **BGM 智能避让 (Audio Ducking)**：
   - 平时正常音量 35%；
   - AI 开始发音时，Web Audio GainNode 在 200ms 内平滑淡出至 8%；发音结束在 500ms 内淡入恢复至 35%。
4. **CEF 内存防护**：弹幕列表使用固定滑窗机制（上限 30 条），超出自动移除 DOM。

### 5.2 管理控制台 (`/admin`) SPA
- 基于 Vue 3 CDN + Tailwind CSS 单文件构建，纯前端零打包。
- 八大核心功能板卡：
  1. **指挥看板**：OBS 推流状态、一键上下播、核心指标概要。
  2. **AI 人设与 LLM**：BaseURL、API Key、Model Name 在线修改保存。
  3. **火山 TTS 语音配置**：API Key、Resource ID、音色 Speaker 挑选与**在线真实发音试听**。
  4. **BGM 曲库管理**：曲目列表、切歌控制、音量测试。
  5. **舞台视觉调整**：立绘缩放 (Scale)、位置偏移 (X/Y)、场景切换，修改即刻热同步。
  6. **B站长连接管理**：房间号填报与连接状态指示灯。
  7. **敏感词风控**：Aho-Corasick 违禁词列表增删与一键保存。
  8. **调试与插播**：弹幕动效模拟器与房管紧急插播朗读。

---

## 6. 通信协议与数据契约

### 6.1 单一 SSE 通道事件契约 (`GET /api/stream`)

| 事件名称 (event) | 数据载荷 (JSON Schema) | 触发时机与作用 |
| :--- | :--- | :--- |
| **`danmu`** | `{"id": str, "uname": str, "content": str, "badge": str, "level": int}` | 观众发送合规普通弹幕 |
| **`super_chat`** | `{"id": str, "uname": str, "price": float, "content": str, "duration": int}` | 收到 B站 SuperChat 醒目留言 |
| **`ai_speech`** | `{"id": str, "text": str, "audio": str, "motion": str, "expression": str}` | AI 思考完成或房管插播，包含音频 Base64 与表情动作 |
| **`stats`** | `{"total_tokens": int, "danmu_count": int, "ai_reply_count": int, "blocked_count": int, "top_users": [{"rank": int, "uname": str, "count": int}]}` | 定期或随事件推送的直播全局数据指标 |
| **`bgm_action`** | `{"action": "play"\|"pause"\|"switch", "track": str, "title": str, "volume": float}` | 弹幕点歌/切歌指令或后台远程切歌控制 |
| **`config_sync`**| `{"theme": str, "mascot": {"scale": float, "x": float, "y": float}, "bgm": {"volume": float}}` | 管理端修改配置后向大屏广播的实时热推数据 |

### 6.2 管理端核心 REST API 契约

- **配置管理**：
  - `GET /api/config`：读取当前配置；
  - `POST /api/config`：在线更新配置，持久化至 `configs/config.yaml`，并下发 `config_sync`。
- **推流遥控**：
  - `POST /api/live/start`：发送 OBS-WebSocket 开播指令；
  - `POST /api/live/stop`：发送 OBS-WebSocket 下播指令；
  - `GET /api/live/status`：获取当前 OBS 连接状态与推流中状态。
- **房管插播**：
  - `POST /api/broadcast/speak`：`{"text": str}`，调用火山 TTS 生成并广播 `ai_speech`。
- **测试与试听**：
  - `POST /api/test/danmu`：`{"type": "danmu"|"gift"|"sc", ...}` 注入测试弹幕；
  - `POST /api/test/tts`：`{"text": str}` 真实请求火山接口，返回试听音频。
- **敏感词词库**：
  - `GET /api/banned-words`：获取敏感词列表；
  - `POST /api/banned-words`：`{"words": [str]}` 覆盖更新并持久化至 `banned_words.txt`。

---

## 7. 异常处理与低配挂机宝优化

1. **B站长连接断线自愈**：`blivedm` 发生断开或网络波动时，采用指数退避算法（1s -> 2s -> 4s -> 最大 30s）自动尝试静默重连，不影响大屏其它组件。
2. **外部 API 故障降级**：若 OpenAI LLM 或火山 TTS 鉴权失败或超时，后台弹出 Toast 告警，前端优雅降级为文字字幕或保持静默，主循环绝不崩溃。
3. **OBS 低配挂机宝推流参数基线**：
   - 编码器优先 NVENC，无独显选择 x264（预设必须为 `ultrafast`）；
   - 分辨率推荐 `1280x720` (720P) @ 30 FPS，码率必须选 `CBR` 固定在 2500 Kbps，关键帧间隔必须硬性设为 2 秒；
   - 在 OBS 中**取消勾选【启用预览】**，开销直接下降 50%。

---

## 8. 自动化测试规划

- **`tests/test_pipeline.py`**：
  - 测试 Aho-Corasick 算法对数万敏感词的纳秒级过滤效果；
  - 测试 UID 滑动窗口的冷却与 TTL 过期淘汰；
  - 测试优先级评分计算逻辑。
- **`tests/test_commands.py`**：
  - 测试弹幕正则指令解析（切歌、点歌、暂停、背景切换）。
- **`tests/test_ai_tts.py`**：
  - 测试 OpenAI 兼容 Payload 组装与 Token 解析；
  - 测试火山引擎 V3 HTTP 请求 Headers、Body 构造与 Chunked Base64 解码逻辑。
- **`tests/test_broadcaster.py`**：
  - 测试多客户端订阅、队列满载时的背压丢弃与隔离保障。
