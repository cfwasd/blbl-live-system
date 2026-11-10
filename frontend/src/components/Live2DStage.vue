<template>
  <div class="live2d-viewport" ref="viewportRef">
    <!-- 头顶 AI 对话字幕气泡 (说话时呈现，自适应长文本) -->
    <div class="speech-bubble-wrapper" :class="{ 'speech-active': isSpeaking && speechText }">
      <div class="speech-bubble">
        <div class="speech-header">
          <span class="speech-name">✦ {{ currentCharacterName }}</span>
          <span class="speech-dot"></span>
        </div>
        <div class="speech-content" :class="contentSizeClass">
          {{ speechText }}<span v-if="isSpeaking" class="typing-cursor"></span>
        </div>
      </div>
      <div class="speech-pointer"></div>
    </div>

    <!-- 舞台全息投影地台 (仅在非透明主题下呈现) -->
    <div v-if="showStagePedestal" class="stage-pedestal-container">
      <div class="pedestal-outer-ring"></div>
      <div class="pedestal-inner-ring"></div>
      <div class="pedestal-core-glow"></div>
      <div class="pedestal-light-cone"></div>
    </div>

    <!-- LivLiv 2.5D 精美角色画布 (高保真 WebGL2 实时动画) -->
    <canvas
      v-show="hasLivLivModel"
      ref="livlivCanvasRef"
      class="livliv-stage-canvas"
      :style="{ transform: 'scale(' + (scale || 1.0) + ')' }"
    ></canvas>

    <!-- 用户专属透明通道立绘 (仅在无 3D/2.5D 模型时呈现) -->
    <div
      v-show="!hasLive2DModel && !hasLivLivModel"
      class="gemini-mascot"
      :style="{ transform: 'scale(' + (scale || 1.0) + ')' }"
    >
      <div
        class="character-wrapper"
        :class="{
          'is-speaking': isSpeaking,
          'is-tilting': isHeadTilting && !isSpeaking,
          'is-happy': isHappyEmotion,
          'is-thinking': isThinkingEmotion
        }"
      >
        <!-- 说话时的音符飘逸浮动动效 -->
        <div v-if="isSpeaking" class="floating-notes-container">
          <span class="music-note note-1">♪</span>
          <span class="music-note note-2">♫</span>
          <span class="music-note note-3">♬</span>
        </div>

        <!-- 角色背后赛博氛围光晕 -->
        <div class="art-glow" :class="{ 'glow-active': isSpeaking }"></div>

        <!-- 主体立绘容器 (将立绘与面部图层100%绑定) -->
        <div class="mascot-art-container">
          <img
            :src="mascotUrl"
            alt="Gemini娘"
            class="gemini-art-img"
          />

          <!-- 自然眨眼闭眼图层 (100% 精确锚定在立绘双眼位置) -->
          <div class="face-eye-overlay" :class="{ 'eye-blinking': isBlinking }">
            <div class="eyelid-curve eye-left"></div>
            <div class="eyelid-curve eye-right"></div>
          </div>

          <!-- 害羞/开心脸颊红晕层 (精确锚定在面颊两侧) -->
          <div class="blush-layer" :class="{ 'blush-active': isHappyEmotion || isSpeaking }">
            <div class="blush-cheek blush-left"></div>
            <div class="blush-cheek blush-right"></div>
          </div>

          <!-- 口型动态张合层 (精确锚定在立绘嘴部) -->
          <div
            v-if="isSpeaking"
            class="mouth-dynamic-wrapper"
            :style="{
              transform: 'scale(' + Math.max(0.7, Math.min(1.4, 0.7 + mouthOpenY * 1.2)) + ')',
              opacity: Math.max(0.6, Math.min(1.0, mouthOpenY * 1.5))
            }"
          >
            <div class="anime-mouth-opening"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import * as PIXI from 'pixi.js';
import { Player as LivLivPlayer } from '@livliv-dev/player';

const props = withDefaults(defineProps<{
  mouthOpenY: number;
  scale?: number;
  isSpeaking?: boolean;
  speechText?: string;
  motion?: string;
  expression?: string;
  showStagePedestal?: boolean;
}>(), {
  scale: 1.0,
  isSpeaking: false,
  speechText: '',
  motion: '',
  expression: '',
  showStagePedestal: true
});

const viewportRef = ref<HTMLDivElement | null>(null);
const livlivCanvasRef = ref<HTMLCanvasElement | null>(null);
const hasLivLivModel = ref(false);
const livlivCharName = ref('奈奈 (Nana) · 2.5D 旗舰看板娘');
let livlivInstance: any = null;

const currentCharacterName = computed(() => {
  if (hasLivLivModel.value) return livlivCharName.value;
  if (hasLive2DModel.value) return '雫酱 (Shizuku)';
  return 'Gemini娘';
});

const hasLive2DModel = ref(false);
const mascotUrl = '/models/gemini/gemini_chan_model_pack/02_透明通道立绘_直播姬已接入.webp';
const MODEL_CANDIDATES = [
  '/models/shizuku/shizuku.model.json',
  '/models/haru/haru01.model.json',
  '/models/gemini/gemini.model3.json'
];

let app: any = null;
let currentModel: any = null;
let currentBaseScale = 0.24;

// 动作与微表情状态
const isBlinking = ref(false);
const isHeadTilting = ref(false);

const isHappyEmotion = computed(() => {
  return props.expression === 'smile' || props.motion === 'Happy' || props.motion === 'Wave';
});

const isThinkingEmotion = computed(() => {
  return props.expression === 'think' || props.motion === 'Think';
});

// 长文本自适应排版字号
const contentSizeClass = computed(() => {
  const len = props.speechText?.length || 0;
  if (len > 60) return 'text-dense';
  if (len > 30) return 'text-medium';
  return 'text-normal';
});

// 自然眨眼计时器 (每隔 3.5 ~ 6 秒随机眨眼 120ms)
let blinkTimer: any = null;
const scheduleNextBlink = () => {
  const nextInterval = 3200 + Math.random() * 2600;
  blinkTimer = setTimeout(() => {
    isBlinking.value = true;
    setTimeout(() => {
      isBlinking.value = false;
      scheduleNextBlink();
    }, 130);
  }, nextInterval);
};

// 闲时随机微歪头倾听 (每隔 15 ~ 22 秒歪头 2.5 秒)
let tiltTimer: any = null;
const scheduleNextTilt = () => {
  const nextInterval = 14000 + Math.random() * 8000;
  tiltTimer = setTimeout(() => {
    if (!props.isSpeaking) {
      isHeadTilting.value = true;
      setTimeout(() => {
        isHeadTilting.value = false;
        scheduleNextTilt();
      }, 2600);
    } else {
      scheduleNextTilt();
    }
  }, nextInterval);
};

async function modelExists(url: string): Promise<boolean> {
  try {
    const res = await fetch(url, { method: 'HEAD' });
    return res.ok;
  } catch {
    return false;
  }
}

onMounted(async () => {
  scheduleNextBlink();
  scheduleNextTilt();

  if (!viewportRef.value) return;

  // 1. 优先尝试初始化 LivLiv 2.5D 精品模型（旗舰看板娘 Nana d03ft / 鲸鱼娘 p01）
  if (livlivCanvasRef.value && typeof LivLivPlayer.isSupported === 'function' && LivLivPlayer.isSupported()) {
    try {
      livlivInstance = new LivLivPlayer(livlivCanvasRef.value, {
        idle: true,
        followPointer: 'page',
        maxPixelRatio: 1.5,
        autoplay: true
      });
      // 加载官方精细版双马尾看板娘 Nana (带头部旋转关键帧与头发重力摇摆)
      await livlivInstance.load('/models/livliv/d03ft.livliv');
      hasLivLivModel.value = true;
      livlivCharName.value = '奈奈 (Nana) · 2.5D 旗舰看板娘';
    } catch (e) {
      console.warn('LivLiv 模型加载失败，降级 Live2D:', e);
      hasLivLivModel.value = false;
    }
  }

  // 2. 如果 LivLiv 未启动，降级寻找首个可用的 Live2D 模型
  if (!hasLivLivModel.value) {
    let chosenModelUrl = '';
    for (const url of MODEL_CANDIDATES) {
      if (await modelExists(url)) {
        chosenModelUrl = url;
        break;
      }
    }

    if (!chosenModelUrl) {
      hasLive2DModel.value = false;
      return;
    }

    (window as any).PIXI = PIXI;
    try {
      app = new PIXI.Application({
        width: 520,
        height: 680,
        backgroundAlpha: 0,
        resolution: window.devicePixelRatio || 1,
        autoDensity: true,
      });
      viewportRef.value.appendChild(app.view as HTMLCanvasElement);

      const { Live2DModel } = await import('pixi-live2d-display');
      Live2DModel.registerTicker(PIXI.Ticker);

      currentModel = await Live2DModel.from(chosenModelUrl);
      currentModel.anchor.set(0.5, 0.5);
      currentModel.x = 260;
      currentModel.y = 420;

      // 模型特异性比例校准
      if (chosenModelUrl.includes('haru')) {
        currentBaseScale = 0.18;
      } else if (chosenModelUrl.includes('shizuku')) {
        currentBaseScale = 0.24;
      } else {
        currentBaseScale = 0.20;
      }
      currentModel.scale.set((props.scale || 1.0) * currentBaseScale);

      currentModel.autoInteract = false;
      currentModel.interactive = true;
      currentModel.on('hit', (hitAreas: string[]) => {
        try {
          if (hitAreas.includes('body')) {
            currentModel.motion('tap_body');
          } else if (hitAreas.includes('head')) {
            currentModel.motion('flick_head');
          }
        } catch (e) {}
      });

      app.stage.addChild(currentModel);
      hasLive2DModel.value = true;

      try {
        currentModel.motion('idle');
      } catch (e) {}

      app.ticker.add(() => {
        if (currentModel && currentModel.internalModel) {
          const core = currentModel.internalModel.coreModel;
          if (core) {
            const mouthVal = Math.max(0, Math.min(1.0, (props.mouthOpenY || 0) * 1.5));
            if (typeof core.setParamFloat === 'function') {
              core.setParamFloat('PARAM_MOUTH_OPEN_Y', mouthVal);
            } else if (typeof core.setParameterValueById === 'function') {
              core.setParameterValueById('ParamMouthOpenY', mouthVal);
            }
          }
        }
      });
    } catch (err) {
      console.warn('Live2D 初始化异常，降级至拟态 2D 立绘模式:', err);
      hasLive2DModel.value = false;
    }
  }
});

onUnmounted(() => {
  if (blinkTimer) clearTimeout(blinkTimer);
  if (tiltTimer) clearTimeout(tiltTimer);
  if (livlivInstance) {
    try {
      livlivInstance.autoplay = false;
    } catch (e) {}
    livlivInstance = null;
  }
  if (app) {
    try {
      app.destroy(true, { children: true, texture: true, baseTexture: true });
    } catch (e) {}
  }
});

watch(() => props.mouthOpenY, (val) => {
  if (livlivInstance?.params) {
    livlivInstance.params.mouthOpen = Math.max(0, Math.min(1.0, (val || 0) * 1.5));
  }
});

watch(() => props.scale, (s) => {
  if (currentModel) {
    currentModel.scale.set((s || 1.0) * currentBaseScale);
  }
});

// 监听 AI 说话时传递的动作与微表情
watch(() => props.motion, (newMotion) => {
  if (livlivInstance) {
    try {
      if (newMotion === 'Happy' || newMotion === 'Wave') livlivInstance.act('nod');
      else if (newMotion === 'Shy' || newMotion === 'Shake') livlivInstance.act('shake');
      else if (newMotion === 'Think' || newMotion === 'Tilt') livlivInstance.act('tilt');
    } catch (e) {}
  }
  if (!currentModel) return;
  try {
    if (newMotion === 'Happy' || newMotion === 'Wave') {
      currentModel.motion('tap_body');
    } else if (newMotion === 'Shy') {
      currentModel.motion('shake');
    } else if (newMotion === 'Think') {
      currentModel.motion('flick_head');
    } else if (newMotion) {
      currentModel.motion(newMotion);
    }
  } catch (e) {}
});

watch(() => props.expression, (newExp) => {
  if (livlivInstance) {
    try {
      if (newExp === 'smile' || isHappyEmotion.value) {
        livlivInstance.setExpression('smile');
      } else if (newExp === 'blush' || newExp === 'shy') {
        livlivInstance.setExpression('shy');
      } else if (newExp === 'think' || isThinkingEmotion.value) {
        livlivInstance.act('tilt');
      } else {
        livlivInstance.setExpression(null);
      }
    } catch (e) {}
  }
  if (!currentModel) return;
  try {
    if (newExp === 'smile') {
      currentModel.expression('f01');
    } else if (newExp === 'blush' || newExp === 'shy') {
      currentModel.expression('f02');
    } else if (newExp === 'think') {
      currentModel.expression('f03');
    } else if (newExp) {
      currentModel.expression(newExp);
    }
  } catch (e) {}
});

watch(() => props.isSpeaking, (speaking) => {
  if (livlivInstance) {
    if (speaking) {
      livlivInstance.act('nod');
    } else {
      setTimeout(() => {
        try {
          livlivInstance?.setExpression(null);
        } catch (e) {}
      }, 1500);
    }
  }
  if (!speaking && currentModel) {
    setTimeout(() => {
      try {
        currentModel.expression('f01');
      } catch (e) {}
    }, 1500);
  }
});
</script>

<style scoped>
.live2d-viewport {
  width: 520px;
  height: 680px;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  pointer-events: none;
  user-select: none;
}

/* LivLiv 2.5D 精美角色画布 (WebGL2) */
.livliv-stage-canvas {
  position: absolute;
  bottom: 0px;
  left: 50%;
  transform-origin: bottom center;
  transform: translateX(-50%);
  width: 520px;
  height: 680px;
  z-index: 10;
  pointer-events: auto;
}

/* 全息投影舞台地台 (解决立绘悬空太空旷) */
.stage-pedestal-container {
  position: absolute;
  bottom: 0px;
  left: 50%;
  transform: translateX(-50%);
  width: 380px;
  height: 100px;
  pointer-events: none;
  z-index: 1;
}

.pedestal-outer-ring {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  width: 360px;
  height: 70px;
  border-radius: 50%;
  border: 2px dashed rgba(56, 189, 248, 0.45);
  box-shadow: 0 0 25px rgba(56, 189, 248, 0.35), inset 0 0 15px rgba(56, 189, 248, 0.2);
  animation: pedestalSpin 20s linear infinite;
}

@keyframes pedestalSpin {
  0% { transform: translateX(-50%) rotate(0deg); }
  100% { transform: translateX(-50%) rotate(360deg); }
}

.pedestal-inner-ring {
  position: absolute;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  width: 280px;
  height: 52px;
  border-radius: 50%;
  border: 1.5px solid rgba(192, 132, 252, 0.5);
  box-shadow: 0 0 18px rgba(192, 132, 252, 0.3);
  animation: pedestalPulse 3s ease-in-out infinite alternate;
}

@keyframes pedestalPulse {
  0% { transform: translateX(-50%) scale(0.96); opacity: 0.6; }
  100% { transform: translateX(-50%) scale(1.04); opacity: 1; }
}

.pedestal-core-glow {
  position: absolute;
  bottom: 15px;
  left: 50%;
  transform: translateX(-50%);
  width: 220px;
  height: 40px;
  border-radius: 50%;
  background: radial-gradient(ellipse at center, rgba(56, 189, 248, 0.6) 0%, rgba(99, 102, 241, 0.25) 50%, rgba(0,0,0,0) 80%);
  filter: blur(10px);
}

.pedestal-light-cone {
  position: absolute;
  bottom: 25px;
  left: 50%;
  transform: translateX(-50%);
  width: 260px;
  height: 180px;
  background: linear-gradient(to top, rgba(56, 189, 248, 0.15) 0%, rgba(129, 140, 248, 0.05) 50%, transparent 100%);
  clip-path: polygon(15% 100%, 85% 100%, 100% 0%, 0% 0%);
  filter: blur(12px);
  pointer-events: none;
}

/* 头顶 AI 对话字幕气泡 (向左偏斜展开，尖角朝向人物头部，绝对不挡脸) */
.speech-bubble-wrapper {
  position: absolute;
  top: 15px;
  right: 60%;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  opacity: 0;
  transform: translateY(14px) scale(0.92);
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 50;
  pointer-events: none;
}
.speech-active {
  opacity: 1;
  transform: translateY(0) scale(1);
}
.speech-bubble {
  background: rgba(11, 15, 25, 0.94);
  backdrop-filter: blur(24px);
  border: 1.5px solid rgba(56, 189, 248, 0.55);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7), 0 0 20px rgba(56, 189, 248, 0.3);
  border-radius: 20px 20px 4px 20px;
  padding: 12px 18px;
  min-width: 240px;
  max-width: 420px;
  max-height: 220px;
  overflow-y: auto;
  scrollbar-width: none;
  color: #fff;
}
.speech-bubble::-webkit-scrollbar {
  display: none;
}
.speech-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
  width: 100%;
}
.speech-name {
  font-size: 11px;
  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 0.5px;
}
.speech-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 8px #38bdf8;
  animation: pulseDot 1s infinite;
}
@keyframes pulseDot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.3; transform: scale(0.8); }
}

.speech-content {
  font-weight: 600;
  color: #f1f5f9;
  text-shadow: 0 1px 2px rgba(0,0,0,0.4);
  word-break: break-all;
  width: 100%;
}
.text-normal {
  font-size: 15px;
  line-height: 1.5;
}
.text-medium {
  font-size: 13.5px;
  line-height: 1.45;
}
.text-dense {
  font-size: 12px;
  line-height: 1.4;
}

.typing-cursor {
  display: inline-block;
  width: 2.5px;
  height: 14px;
  background: #38bdf8;
  margin-left: 3px;
  vertical-align: -1px;
  border-radius: 1px;
  box-shadow: 0 0 6px #38bdf8;
  animation: cursorBlink 0.7s infinite;
}
@keyframes cursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.speech-pointer {
  width: 0;
  height: 0;
  border-left: 14px solid transparent;
  border-right: 2px solid transparent;
  border-top: 12px solid rgba(11, 15, 25, 0.94);
  margin-top: -1px;
  margin-right: 22px;
}

/* 用户专属 Gemini 娘立绘容器 */
.gemini-mascot {
  position: relative;
  width: 440px;
  height: 600px;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  transform-origin: bottom center;
  z-index: 10;
}

.character-wrapper {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  animation: artBreathe 4s ease-in-out infinite;
  transition: transform 0.4s ease;
}

@keyframes artBreathe {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-8px) scale(1.008); }
}

/* 闲时微歪头 */
.is-tilting {
  transform: rotate(2.2deg) translateY(-4px) !important;
}

/* 说话时更生动的点头与微晃动效 */
.is-speaking {
  animation: speakDynamics 0.85s ease-in-out infinite !important;
}

@keyframes speakDynamics {
  0%, 100% { transform: translateY(-4px) rotate(-1.2deg) scale(1.006); }
  50% { transform: translateY(-14px) rotate(1.2deg) scale(1.018); }
}

/* 开心情绪律动 (收到SC/礼物) */
.is-happy {
  animation: happyBounce 0.6s ease-in-out 3 !important;
}
@keyframes happyBounce {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-16px) scale(1.025); }
}

/* 角色背后发光 */
.art-glow {
  position: absolute;
  bottom: 6%;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  height: 18%;
  border-radius: 50%;
  background: radial-gradient(ellipse at center, rgba(56, 189, 248, 0.5) 0%, rgba(56, 189, 248, 0) 70%);
  filter: blur(16px);
  opacity: 0.35;
  transition: opacity 0.4s ease;
  z-index: 0;
}
.glow-active {
  opacity: 0.95;
  animation: glowPulse 1.1s ease-in-out infinite;
}
@keyframes glowPulse {
  0%, 100% { opacity: 0.55; transform: translateX(-50%) scale(0.96); }
  50% { opacity: 1; transform: translateX(-50%) scale(1.08); }
}

.mascot-art-container {
  position: relative;
  display: inline-block;
  line-height: 0;
}

.gemini-art-img {
  position: relative;
  z-index: 2;
  display: block;
  max-width: 100%;
  max-height: 560px;
  object-fit: contain;
  filter: drop-shadow(0 15px 35px rgba(0, 0, 0, 0.55)) drop-shadow(0 0 16px rgba(56, 189, 248, 0.22));
}

/* 自然眨眼闭眼图层 (100% 相对立绘原画精确定位) */
.face-eye-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.08s ease;
  z-index: 10;
}
.eye-blinking {
  opacity: 1 !important;
}
.eyelid-curve {
  position: absolute;
  width: 26px;
  height: 7px;
  border-top: 3.5px solid #2e1d44;
  border-radius: 50% 50% 0 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.45);
}
.eye-left {
  left: 45.4%;
  top: 17.5%;
  transform: translate(-50%, -50%) rotate(3deg);
}
.eye-right {
  left: 54.9%;
  top: 16.3%;
  transform: translate(-50%, -50%) rotate(4deg);
}

/* 害羞/开心红晕光泽 (精确锚定在面颊两侧) */
.blush-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  z-index: 8;
  transition: opacity 0.4s ease;
  pointer-events: none;
}
.blush-active {
  opacity: 0.85;
}
.blush-cheek {
  position: absolute;
  width: 26px;
  height: 12px;
  border-radius: 50%;
  background: radial-gradient(ellipse at center, rgba(251, 113, 133, 0.7) 0%, rgba(251, 113, 133, 0) 75%);
  filter: blur(2px);
}
.blush-left {
  left: 42%;
  top: 21%;
  transform: translate(-50%, -50%);
}
.blush-right {
  left: 58%;
  top: 20%;
  transform: translate(-50%, -50%);
}

/* 说话时口型开合层 (精确锚定在立绘嘴部) */
.mouth-dynamic-wrapper {
  position: absolute;
  left: 51.5%;
  top: 22.8%;
  transform-origin: center center;
  z-index: 9;
  pointer-events: none;
  transition: transform 0.06s ease, opacity 0.06s ease;
}
.anime-mouth-opening {
  width: 13px;
  height: 8px;
  transform: translate(-50%, -50%);
  background: radial-gradient(ellipse at center, rgba(160, 40, 60, 0.95) 0%, rgba(220, 80, 100, 0.9) 60%, rgba(240, 140, 150, 0.7) 100%);
  border-radius: 40% 40% 50% 50%;
  border: 1px solid rgba(120, 30, 50, 0.8);
  box-shadow: 0 0 4px rgba(220, 80, 100, 0.4);
}

/* 飘逸音符 */
.floating-notes-container {
  position: absolute;
  top: 10%;
  right: 15%;
  z-index: 25;
  pointer-events: none;
}
.music-note {
  position: absolute;
  font-size: 16px;
  font-weight: 800;
  color: #38bdf8;
  opacity: 0;
  text-shadow: 0 0 10px rgba(56, 189, 248, 0.8);
}
.note-1 {
  animation: floatNote 1.8s ease-in-out infinite;
  animation-delay: 0.1s;
}
.note-2 {
  animation: floatNote 2.1s ease-in-out infinite;
  animation-delay: 0.7s;
  right: -20px;
  color: #c084fc;
}
.note-3 {
  animation: floatNote 1.9s ease-in-out infinite;
  animation-delay: 1.3s;
  right: 15px;
  color: #f472b6;
}

@keyframes floatNote {
  0% { transform: translate(0, 0) scale(0.6); opacity: 0; }
  30% { opacity: 0.9; }
  100% { transform: translate(-25px, -60px) scale(1.1); opacity: 0; }
}
</style>
