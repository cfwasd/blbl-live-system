<template>
  <div class="live2d-viewport" ref="viewportRef">
    <!-- 头顶 AI 对话字幕气泡 (说话时呈现，自适应长文本) -->
    <div class="speech-bubble-wrapper" :class="{ 'speech-active': isSpeaking && speechText }">
      <div class="speech-bubble">
        <div class="speech-header">
          <span class="speech-name">✦ Gemini 娘</span>
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

    <!-- 用户专属透明通道立绘 (带丰富多层微表情与动效) -->
    <div
      v-show="!hasLive2DModel"
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
const hasLive2DModel = ref(false);
const mascotUrl = '/models/gemini/gemini_chan_model_pack/02_透明通道立绘_直播姬已接入.webp';
const MODEL_URL = '/models/gemini/gemini.model3.json';
let app: any = null;
let currentModel: any = null;

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

  if (!(await modelExists(MODEL_URL))) {
    hasLive2DModel.value = false;
    return;
  }

  (window as any).PIXI = PIXI;
  try {
    app = new PIXI.Application({
      width: 600,
      height: 800,
      backgroundAlpha: 0
    });
    viewportRef.value.appendChild(app.view as HTMLCanvasElement);

    let Live2DModel: any = null;
    try {
      const cubism4Module = await import('pixi-live2d-display/cubism4');
      Live2DModel = cubism4Module.Live2DModel;
    } catch {
      const standardModule = await import('pixi-live2d-display');
      Live2DModel = standardModule.Live2DModel;
    }

    if (Live2DModel) {
      currentModel = await Live2DModel.from(MODEL_URL);
      currentModel.anchor.set(0.5, 0.5);
      currentModel.x = 260;
      currentModel.y = 350;
      currentModel.scale.set((props.scale || 1.0) * 0.16);
      app.stage.addChild(currentModel);
      hasLive2DModel.value = true;
    }
  } catch (err) {
    hasLive2DModel.value = false;
  }
});

onUnmounted(() => {
  if (blinkTimer) clearTimeout(blinkTimer);
  if (tiltTimer) clearTimeout(tiltTimer);
});

watch(() => props.scale, (s) => {
  if (currentModel) {
    currentModel.scale.set((s || 1.0) * 0.16);
  }
});

watch(() => props.mouthOpenY, (val) => {
  if (currentModel && currentModel.internalModel?.coreModel) {
    try {
      currentModel.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', val);
    } catch (e) {}
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
