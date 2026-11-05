# 🐟 大肥鱼 AI 虚拟主播弹幕驱动系统 (Virtual AI Live System)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue.js-3.3+-4FC08D?style=flat-square&logo=vue.js&logoColor=white" alt="Vue 3">
  <img src="https://img.shields.io/badge/Pixi.js-v7-E72264?style=flat-square&logo=pixijs&logoColor=white" alt="Pixi.js">
  <img src="https://img.shields.io/badge/Live2D-Cubism%202%20%2F%204-00A3FF?style=flat-square" alt="Live2D">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
</p>

专为 **B 站（Bilibili）无人 / 半无人二次元虚拟主播直播间** 量身打造的高性能互动推流驱动系统。

采用**“重核轻端、单向驱动”**的前后端分离与流式下发架构：计算、LLM 推理、语音合成、敏感词风控与 B 站 WebSocket 长连接全部收敛在服务端，OBS 浏览器源轻量渲染，大幅降低推流宿主机负载与 CEF 内核崩溃风险。

---

## 🌟 核心特性一览

### 1. 🎭 拟真虚拟看板娘与实时口型同步 (LipSync)
- **多代 Live2D 引擎支持**：集成 Pixi.js v7 + `pixi-live2d-display`，开箱即用支持 Cubism 2.1 与 Cubism 4 SDK 骨骼动画。
- **高精度音频口型映射**：基于 Web Audio API 实时提取火山豆包 TTS 音频振幅，高频同步映射至 `ParamMouthOpenY`，告别机械式张嘴。
- **智能伴奏避让 (Audio Ducking)**：当 AI 看板娘开口说话时，背景音乐音量自动线性压低至避让阈值，语音结束后平滑回升。

### 2. 🎵 极光音乐播放器 (Aurora Player) & 弹幕互动点歌
- **网易云在线实时点歌**：观众在直播间发送 `点歌 歌名`，系统自动搜索网易云音乐曲库并实时下发高质音频直链。
- **动态卡拉 OK 歌词浮层**：毫秒级解析 LRC 歌词，随音乐旋律高亮动态滚动展示。
- **本地与在线混合歌单**：支持静态伴奏循环与观众点播无缝插播，支持 `切歌`、`暂停`、`继续` 等丰富弹幕指令。

### 3. 🛡️ 工业级弹幕治理责任链 (Pipeline)
- **Aho-Corasick 多模敏感词风控**：微秒级多模式字符串过滤，拦截任何涉政涉恐低俗违规词汇。
- **UID 滑动窗口防刷屏**：基于带有 TTL 淘汰机制的高性能缓存（Cachetools），防止单一用户恶意刷屏灌水。
- **动态优先级权重评分**：自动识别舰长、高粉丝牌、高频互动及 SC 醒目留言，优先转交 AI 大模型处理。

### 4. 📺 赛博朋克极简毛玻璃直播 HUD (Live Overlay)
- **原生全透明通道 (Alpha Channel)**：无缝叠加至 OBS 游戏画面或自定 3D 场景之上。
- **SC 醒目留言置顶卡片**：打赏弹幕专属渐变光效置顶，高亮倒计时倒流展示。
- **新观众动态迎宾横幅**：新进房观众自动弹出二次元欢迎横幅与入场音效。
- **交互小组件矩阵**：实时广播跑马灯、弹幕指令互动指南卡片、观众情绪心跳律动仪、动态倒计时时钟。
- **快捷键热控**：直播大屏页面按 `T` 键可即时切换场景背景风格，按 `M` 键可快速静音/切换伴奏。

### 5. 🎛️ 综合管理控制台 (Admin SPA)
- **开箱即用免构建**：单文件 Vue 3 + Tailwind CSS 架构，零 Node 构建依赖即可打开。
- **B 站直播长连接调试器**：输入任意房间号，一键直连 WebSocket 并展示长短房间号换算。
- **在线音色试听与配置热重载**：实时调配 DeepSeek / OpenAI 大模型 Prompt、切换火山豆包发音人音色，配置保存即刻热同步至大屏。
- **仿真弹幕注入与房管插播**：无需开播即可模拟各种弹幕与 SC 场景，支持房管随时下发人工台词与语音。
- **实时日志终端**：实时输出风控拦截、弹幕打分、大模型耗时与 TTS 生成日志。

---

## 🏗️ 系统架构图

```
                ┌─────────────────────────────────────────────────────────┐
                │          Bilibili Live Cluster (WebSocket)              │
                └───────────────────────────┬─────────────────────────────┘
                                            │ blivedm 协议逆向接入
                                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     FastAPI 核心控制台 (Admin / Core)                     │
│                                                                         │
│  [原始消息] ──► [Aho-Corasick敏感词过滤] ──► [UID滑动窗口冷却]          │
│                                                   │                     │
│  [SSE 广播] ◄── [火山豆包 TTS / LLM] ◄── [动态权重评分打分管线]           │
└──────────────────┬───────────────────────────────────────┬──────────────┘
                   │ text/event-stream (单向广播)           │ 4455 WebSocket
                   ▼                                       ▼
┌──────────────────────────────────────┐  ┌───────────────────────────────┐
│       OBS 浏览器源 /live (大屏)       │  │        OBS Studio 推流端      │
│  - Live2D / Pixi.js 动画与 LipSync    │  │  - 一键远程开播 / 停播        │
│  - 极光播放器 (网易云搜歌 + 滚动歌词)   │  │  - 码率与渲染掉帧状态监测    │
│  - 毛玻璃弹幕墙 / SC卡片 / 迎宾横幅   │  └───────────────────────────────┘
└──────────────────────────────────────┘
```

---

## 🚀 极速部署指南

### 方式一：Docker Compose 一键部署（生产推荐）

这是在云服务器或挂机宝上最轻松、最稳定的部署方式。

#### 1. 克隆仓库
```bash
git clone https://github.com/cfwasd/blbl-live-system.git
cd blbl-live-system
```

#### 2. 配置环境密钥
```bash
# 复制脱敏模板
cp configs/config.example.yaml configs/config.yaml

# 编辑配置文件
nano configs/config.yaml
```
主要填写字段：
* `bilibili.room_id`: 您的 B 站直播间长/短号。
* `llm`: 大模型 `base_url`、`api_key`（兼容 OpenAI、DeepSeek、Gemini 等格式）和主播 Prompt。
* `volc_tts`: 火山引擎豆包语音合成的 `api_key` 与发音人 `speaker`。

#### 3. 启动容器
```bash
docker compose up -d --build
```

#### 4. 查看实时日志
```bash
docker compose logs -f
```

---

### 方式二：本地开发环境直接运行

#### 环境依赖
* Python 3.10+ 或 3.11
* Node.js 18+ (仅当修改前端源码时需要)

#### 1. 启动后端 Python 服务
```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 启动 FastAPI 服务
uvicorn admin.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. 前端大屏构建（可选，仓库已自带编译产物）
```bash
cd frontend
npm install
npm run build     # 产物自动注入 admin/static/live
```

---

## 🖥️ 核心访问路径

服务启动后，默认监听 `8000` 端口：

| 访问路径 | 用途说明 | 使用场景 |
| :--- | :--- | :--- |
| `http://localhost:8000/admin` | 综合管理后台 | 配置维护、音色试听、日志监测、弹幕模拟、点歌控制 |
| `http://localhost:8000/live` | OBS 专用大屏 | 填入 OBS 浏览器源，全透明通道展示 |
| `http://localhost:8000/api/stream` | SSE 数据流 | OBS 浏览器源或第三方客户端实时事件订阅 |

---

## 🎥 OBS Studio 接入与推流配置

1. 打开 **OBS Studio**，在来源面板中点击 `+` ➜ 选择 **【浏览器】**（Browser Source）。
2. 配置参数如下：
   * **URL**：`http://localhost:8000/live`（若部署在云端，替换为您的服务器 IP 或域名）。
   * **宽度**：`1920`
   * **高度**：`1080`
   * **自定义帧率**：勾选并设置为 `30` 或 `60` FPS。
   * **控制 OBS 音频**：建议**勾选【通过 OBS 控制音频】**，这样可以在 OBS 混音器中独立监听 BGM 与主播发音。
   * **刷新浏览器缓存**：勾选【在场景激活时刷新浏览器】。
3. **挂机宝 / 低配云主机推流优化基线**：
   * 编码器：优先硬件编码器（如 NVENC、QSV）或 CPU `ultrafast`。
   * 码率控制：必须锁定为 **CBR 固定码率**（2500 ~ 3000 Kbps），关键帧间隔设为 `2` 秒。
   * 关预览省算力：在 OBS 菜单中右键预览画面，**取消勾选【启用预览】**，可大幅降低 40% 以上的 GPU/CPU 占用。

---

## 💬 弹幕指令一览

直播间观众只需在公屏发送对应格式的弹幕，即可触发自动化互动：

| 指令格式 | 示例 | 触发动作 |
| :--- | :--- | :--- |
| `点歌 <歌名/歌手>` | `点歌 起风了`、`点歌 告白气球` | 在线解析网易云音频与歌词，实时切入伴奏播放 |
| `切歌` / `下一首` / `换首歌` | `切歌` | 随机/顺序切换当前播放曲目 |
| `暂停音乐` / `继续音乐` | `暂停音乐` | 暂停或继续播放伴奏 |
| `换个风格` / `换皮肤` | `换个风格` | 切换大屏的背景主题与色调 |
| 任意日常聊天弹幕 | `主播今天吃了什么呀？` | 触发责任链风控与大模型思考，生成台词与实时 TTS 语音 |
| 投喂 SC (醒目留言) | *(B站官方付费功能)* | 触发高权重优先插播答谢，并在大屏置顶专属发光打赏卡 |

---

## 📁 目录结构说明

```
.
├── admin/                      # 后端核心业务层 (Python / FastAPI)
│   ├── core/
│   │   ├── ai/                 # LLM 对话编排与 Prompt 组装 (OpenAI 兼容接口)
│   │   ├── broadcast/          # SSE 广播中心与有界背压事件队列
│   │   ├── ingress/            # B 站 WebSocket (blivedm) 逆向接入与指令解析
│   │   ├── music/              # 网易云在线音乐搜索、歌单解析与歌词拉取
│   │   ├── obs/                # OBS-WebSocket 远程遥控客户端
│   │   ├── pipeline/           # 弹幕治理管线 (Aho-Corasick 敏感词过滤/冷却/打分)
│   │   └── tts/                # 火山引擎豆包大模型语音合成 (Seed-TTS)
│   ├── routers/                # REST API 路由与 SSE /api/stream 端点
│   ├── static/
│   │   ├── admin/              # 管理后台 SPA (Vue 3 CDN 单文件)
│   │   └── live/               # 直播大屏生产产物 (由 Vite 编译输出)
│   ├── config.py               # Pydantic 全局配置模型定义与持久化
│   └── main.py                 # FastAPI 应用入口与生命周期管理
├── configs/                    # 运行时配置文件目录 (包含敏感词库与 yaml 配置)
│   ├── banned_words.txt        # 敏感词过滤词库
│   └── config.example.yaml     # 生产配置参考模板
├── frontend/                   # 直播大屏前端源码 (Vue 3 + Pixi.js + TypeScript)
│   ├── src/
│   │   ├── components/         # 极光播放器、Live2D舞台、弹幕墙、HUD 组件
│   │   ├── composables/        # SSE 连接器、Web Audio LipSync 口型同步驱动
│   │   └── App.vue             # 大屏顶层视图布局
├── models/                     # Live2D 外部模型存放目录
├── docker-compose.yml          # Docker Compose 生产编排文件
├── Dockerfile                  # 多阶段极轻量 Docker 构建文件
├── requirements.txt            # Python 核心依赖列表
└── README.md                   # 项目工程文档
```

---

## ⚖️ 平台合规与免责声明

1. **官方 AI 报备**：在 B 站进行虚拟 AI 主播直播时，请务必在 B 站直播间后台开启**【AI 生成合成内容】**官方报备，遵守《互联网信息服务深度合成管理规定》。
2. **敏感词过滤**：请根据直播所在分区的管理要求，持续在管理后台完善 `banned_words.txt` 违规敏感词库。
3. **免责声明**：本项目仅供技术学习、交流与授权安全测试使用。请勿用于违规营销、侵权传播或违反平台主播行为规范的场景。

---

## 🤝 鸣谢与生态支持

- [blivedm](https://github.com/xfgryujk/blivedm) - 优秀的 B 站直播 WebSocket 协议解析库
- [pixi-live2d-display](https://github.com/guansss/pixi-live2d-display) - Pixi.js 的 Live2D 跨版本集成渲染插件
- [FastAPI](https://fastapi.tiangolo.com/) - 现代、高性能的 Python Web 框架
