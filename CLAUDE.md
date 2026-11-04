# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述与技术栈

本项目为**虚拟 AI 人物直播弹幕驱动系统**（大肥鱼 AI 虚拟主播系统），专为 B 站（Bilibili）无人/半无人二次元虚拟主播直播间设计，采用“重核轻端、单向驱动”架构。

- **后端服务 (Admin / Core)**：Python 3.10+ / 3.11、FastAPI、Uvicorn、Asyncio
  - 弹幕接入：`blivedm`（B 站直播 WebSocket 协议逆向接入、长短房间号换算、心跳与指数退避重连）
  - 消息治理：`pyahocorasick`（多模式敏感词匹配）、UID 滑动窗口冷却（带 TTL 防内存膨胀）、动态优先级加权评分
  - 传输分发：SSE（Server-Sent Events，`text/event-stream`，单向推送、原生自动重连，对 OBS CEF 内核友好）
  - 推流管控：OBS-WebSocket（4455 端口远程遥控开播/停播与状态监测）
  - 管理后台：FastAPI 静态托管单文件 SPA（Vue 3 CDN + Tailwind CSS，免打包构建）
- **直播大屏 (Live Overlay `/live`)**：
  - 前端工程：Vue 3 (Composition API) + TypeScript + Vite
  - 渲染引擎：Pixi.js (v7) + `pixi-live2d-display` + Live2D Cubism 4 SDK（`live2dcubismcore.min.js`）
  - 音频与动效：Web Audio API 实时提取音频振幅映射口型（LipSync 到 `ParamMouthOpenY`）、BGM 智能避让（Audio Ducking）、拟态毛玻璃弹幕墙、SC 置顶卡片、全透明通道（Alpha Channel）
- **交付与部署**：Multi-Stage Dockerfile（Node 20 构建前端 + Python 3.11-slim 运行后端）、Docker Compose

## 常用开发与构建命令

### 后端 (Python / FastAPI)
- **启动开发服务器**：
  ```bash
  uvicorn admin.main:app --reload --host 0.0.0.0 --port 8000
  ```
- **安装依赖**：
  ```bash
  pip install -r requirements.txt
  ```
- **运行测试**：
  ```bash
  pytest
  # 运行单个测试文件
  pytest tests/test_pipeline.py
  # 运行指定测试用例
  pytest tests/test_pipeline.py::test_aho_corasick_filter
  ```

### 前端大屏 (Frontend / Vue 3)
- **进入前端目录**：`cd frontend`
- **安装依赖**：`npm install`
- **启动本地调试**：`npm run dev`
- **构建生产产物**（输出至 `admin/static/live`）：
  ```bash
  npm run build
  ```
- **类型检查与代码检查**：
  ```bash
  npm run lint
  vue-tsc --noEmit
  ```

### Docker 容器化构建与运行
- **构建 All-in-One 镜像**：
  ```bash
  docker build -t virtual-ai-live:v0.2 .
  ```
- **启动容器**（挂载配置与 Live2D 模型）：
  ```bash
  docker run -d --name ai-live -p 8000:8000 -v ${PWD}/configs:/app/configs -v ${PWD}/models:/app/models -e ROOM_ID=21452505 virtual-ai-live:v0.2
  ```
- **Docker Compose 启动**：
  ```bash
  docker compose up -d
  ```

### OBS 与推流上下播命令
- **远程一键开播**：`curl -s -X POST http://127.0.0.1:8000/api/live/start`
- **远程一键下播**：`curl -s -X POST http://127.0.0.1:8000/api/live/stop`
- **查询推流状态**：`curl -s http://127.0.0.1:8000/api/live/status`

## 核心系统架构与设计约定

### 1. 五层逻辑架构
1. **外部数据源 (External Source)**：B 站直播长连接集群（`live-open.bilibili.com`）。
2. **协议接入层 (Ingress Layer)**：`blivedm` 异步处理 WebSocket 拆包解压（Zlib/Brotli）、30s 心跳包及网络指数退避重连。
3. **消息治理管线 (Pipeline Layer - 责任链模式)**：
   `原始消息 -> 格式截断/清洗 -> Aho-Corasick多模敏感词风控 -> UID冷却限制 -> 动态优先级加权 -> 广播中心`
4. **传输分发层 (Transport Layer)**：广播中心采用“发布-订阅 + 客户端专属有界队列（`asyncio.Queue(maxsize=100)`）”。队列满载时实施背压丢弃策略（优先丢弃低权重普通弹幕，保留 SC 与礼物）。通过 SSE `/api/stream` 单向广播。
5. **视图渲染层 (View Layer)**：OBS 浏览器源（CEF 内核，1080P/720P，全透明通道），自底向上为：底层 Live2D 模型、中层粒子动效、顶层毛玻璃弹幕与 SC 置顶栏。

### 2. 核心端口与访问路径
- `http://localhost:8000/admin`：综合管理控制台（人设切换、Prompt 配置、TTS 试听、BGM 避让、推流遥控、敏感词在线维护）
- `http://localhost:8000/live`：OBS 浏览器源大屏（全透明通道、快捷键 `T` 切换场景背景、`M` 切换伴奏）
- `http://localhost:8000/api/stream`：SSE 事件流端点
- `ws://localhost:4455`：OBS 原生 WebSocket 控制端口

### 3. 工程规范与避坑原则
- **CEF 内存防护**：OBS 浏览器源 CEF 抗崩溃能力较弱，禁止在前端展示大屏堆积无限 DOM 节点，必须采用固定滑窗机制淘汰超额弹幕；展示端严禁承载复杂重计算，计算与状态全部收敛在 Python 后端。
- **SSE 响应头约束**：经过反向代理时需强制配置 `X-Accel-Buffering: no` 且禁用 `proxy_buffering`，避免弹幕被缓冲积压后批量爆发。
- **挂机宝/低配推流参数基线**：视频编码优先 NVENC 或 CPU `ultrafast`，必须锁定固定码率 `CBR`（2500~3000 Kbps）、固定关键帧间隔 2 秒、输出分辨率推荐 720P@30FPS，并务必在 OBS 中取消勾选【启用预览】以节省 GPU/CPU 算力。
- **平台合规**：必须在 B 站直播后台勾选“AI 生成合成内容”官方报备；无人值守需配置闲时主动暖场机制，防止长时间死寂画面被平台巡检切断。
