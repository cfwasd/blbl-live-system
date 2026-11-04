# 虚拟AI人物直播系统 —— 前端高颜值渲染与 Live2D 架构设计

| 维度 | 设计选型 |
| :--- | :--- |
| **应用架构** | 双端分离：管理控制台（Admin） + 直播展示大屏（Live Overlay） |
| **管理端技术栈** | 方案 A（推荐）：FastAPI 托管轻量 SPA（Vue3 CDN / Alpine.js + Tailwind CSS，免构建零心智）<br>方案 B：Vue3 + Vite 独立极简管理面板 |
| **直播展示页技术栈**| **Vue 3 (Composition API) + Vite + TypeScript + Pixi.js (v7) + `pixi-live2d-display` + Live2D Cubism 4 SDK** |
| **渲染通道** | 全透明通道（Alpha Channel Transparent）、WebGL 2.0 硬件加速、60 FPS 平滑上屏 |

---

## 1. 双端视口职责划分

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. 主播/房管操作端 (Admin Dashboard)                                   │
│    URL: http://localhost:8000/admin                                    │
│    • 房间号在线热切换 / 连接状态指示                                   │
│    • 实时弹幕风控过滤词在线增删 (CRUD)                                  │
│    • 虚拟形象动作/表情手动触发测试 (Debug Trigger)                     │
│    • 一键闭麦/清屏/熔断开关                                            │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│ 2. OBS / 直播姬 视口大屏 (Live Overlay)                                │
│    URL: http://localhost:8000/live                                     │
│    • 完全透明背景，层叠渲染                                             │
│    • 【底层】Live2D 虚拟形象画布 (呼吸、眨眼、视线追踪、口型同步)      │
│    • 【中层】粒子动效 / 进场特效 / 礼物飘屏卡片                        │
│    • 【顶层】SC 醒目留言置顶栏 + 拟态毛玻璃弹幕互动流                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 直播展示大屏（Vue 3 + Pixi.js + Live2D）架构设计

### 2.1 分层渲染架构 (Layered Rendering)

在 OBS 中，页面通过多层 Canvas / DOM 混合堆叠，既保证 2D 模型的 WebGL 极致性能，又保留富文本弹幕的 CSS 动画灵活性：

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 顶层浮层 (HTML5 / CSS3 硬件加速图层, pointer-events: none)             │
│  ├─ SC 置顶卡片 (Super Chat Pinned Bar，倒计时进度条)                   │
│  ├─ 拟态弹幕列表 (毛玻璃 Glassmorphism、入场淡入淡出、粉丝牌高亮)       │
│  └─ 实时字幕与 AI 气泡对话框 (Speech Bubble)                           │
├────────────────────────────────────────────────────────────────────────┤
│ 中层特效 (Pixi.js Particle Container)                                 │
│  └─ 收到礼物时的粒子爆炸、爱心飘落、光效粒子                           │
├────────────────────────────────────────────────────────────────────────┤
│ 底层模型 (Pixi.js WebGL Viewport, transparent: true)                  │
│  └─ Live2D Model (Cubism 3/4)                                          │
│      ├─ 基础循环动画 (Idle、Breathing、Blinking)                       │
│      ├─ 口型开合 (LipSync: 由 Web Audio 频域 或 avatar_cue 指令驱动)   │
│      └─ 动态表情与动作 (Expression: happy/angry/shy; Motion: wave/nod) │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心依赖与选型
1. **渲染主引擎**：`pixi.js@^7.x`
   - 提供 2D WebGL 极致渲染性能，与 Live2D 结合极其成熟。
2. **Live2D 桥接层**：`pixi-live2d-display`
   - 开箱即用支持 Cubism 2.1、Cubism 3 与 Cubism 4 模型（`.model3.json`）。
   - 自动处理动作优先级队列、点击交互与视线跟随。
3. **Live2D 核心运行时**：
   - 需将 Live2D 官方底层库 `live2dcubismcore.min.js` 放置在静态资源目录中，在 HTML 头部直接引入。

### 2.3 Live2D 动态驱动管线

```text
SSE 接收事件 
  ├── event: danmu / gift ──▶ 触发气泡文字 / 触发中层粒子动效
  ├── event: avatar_cue   ──▶ 直接驱动模型触发动作 (如 model.motion("Wave"))
  └── event: tts_audio    ──▶ 音频流播放 + 口型同步
                                │
                                ├─ 方案A (前端频谱计算): Web Audio API 实时提取 RMS 音量 ──▶ 映射 ParamMouthOpenY
                                └─ 方案B (后端音素包): 解析 Viseme 序列精确对齐嘴型
```

#### 前端口型同步（LipSync）核心实现逻辑（方案 A）：
```typescript
// 利用 Web Audio API 实时提取音频振幅驱动 Live2D 嘴型开合
export function setupLipSync(audioElement: HTMLAudioElement, live2dModel: any) {
  const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 256;
  
  const source = audioCtx.createMediaElementSource(audioElement);
  source.connect(analyser);
  analyser.connect(audioCtx.destination);

  const dataArray = new Uint8Array(analyser.frequencyBinCount);

  function update() {
    requestAnimationFrame(update);
    if (audioElement.paused) {
      live2dModel.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', 0);
      return;
    }
    analyser.getByteFrequencyData(dataArray);
    // 计算中低频段的能量均值
    let sum = 0;
    for (let i = 0; i < 30; i++) sum += dataArray[i];
    const average = sum / 30;
    // 归一化为 0.0 ~ 1.0 的嘴型开合幅度
    const mouthOpen = Math.min(1.0, Math.max(0.0, average / 120));
    live2dModel.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', mouthOpen);
  }
  update();
}
```

---

## 3. 管理端（Admin Dashboard）轻量设计

管理端的目标是**好用、响应迅速、运维零心智负担**。

### 推荐方案：FastAPI + Vue 3 (CDN 单文件) + Tailwind CSS
* **优势**：
  - 无需额外安装 Node.js、Vite 构建，无需打包部署，直接放在 Python 后端的 `admin_static/index.html`。
  - 单个 HTML 引入 Vue 3 和 Tailwind CSS CDN，即具备现代化响应式数据绑定与清爽 UI。
  - 管理端与后端同一域名端口，完全**天然免除跨域 (CORS)** 困扰。
* **核心功能模块**：
  1. **房间状态卡片**：当前连接的 B站房间号、连接状态（绿色已连接/红色断开/重连中）、实时人气值。
  2. **风控规则控制**：在线动态添加/删除违禁词、正则黑名单，秒级生效。
  3. **实时监视流**：一个轻量级的表格显示当前处理后的弹幕历史，支持单条点击复制。
  4. **虚拟人手动测试区**：提供快捷按钮（如：“打招呼动作”、“害羞表情”、“测试弹幕上屏”），方便主播开播前自检。
