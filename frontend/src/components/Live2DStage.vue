<template>
  <div class="live2d-viewport" ref="viewportRef">
    <!-- AI 对话字幕气泡 (说话时头顶呈现) -->
    <div class="speech-bubble-wrapper" :class="{ 'speech-active': isSpeaking && speechText }">
      <div class="speech-bubble">
        <div class="speech-header">
          <span class="speech-name">✦ Gemini娘</span>
          <span class="speech-dot"></span>
        </div>
        <div class="speech-content">{{ speechText }}</div>
      </div>
      <div class="speech-pointer"></div>
    </div>

    <!-- 用户专属透明通道立绘 (带呼吸起伏与说话律动) -->
    <div v-show="!hasLive2DModel" class="gemini-mascot" :style="{ transform: 'scale(' + (scale || 1.0) + ')' }">
      <div class="character-wrapper" :class="{ 'is-speaking': isSpeaking }">
        <div class="art-glow" :class="{ 'glow-active': isSpeaking }"></div>
        <img
          :src="mascotUrl"
          alt="Gemini娘"
          class="gemini-art-img"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import * as PIXI from 'pixi.js';

const props = defineProps<{
  mouthOpenY: number;
  scale?: number;
  isSpeaking?: boolean;
  speechText?: string;
}>();

const viewportRef = ref<HTMLDivElement | null>(null);
const hasLive2DModel = ref(false);
const mascotUrl = '/models/gemini/gemini_chan_model_pack/02_透明通道立绘_直播姬已接入.webp';
const MODEL_URL = '/models/gemini/gemini.model3.json';
let app: any = null;
let currentModel: any = null;

async function modelExists(url: string): Promise<boolean> {
  try {
    const res = await fetch(url, { method: 'HEAD' });
    return res.ok;
  } catch {
    return false;
  }
}

onMounted(async () => {
  if (!viewportRef.value) return;

  // 仅当 models/ 下确实存在 .model3.json 时才启用 Live2D 渲染，避免无谓的 404 请求
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
    // 平滑启用用户在 models/ 下放置的透明通道立绘
    hasLive2DModel.value = false;
  }
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

/* 头顶 AI 对话字幕气泡 */
.speech-bubble-wrapper {
  position: absolute;
  top: 10px;
  right: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
  opacity: 0;
  transform: translateY(12px) scale(0.9);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 50;
}
.speech-active {
  opacity: 1;
  transform: translateY(0) scale(1);
}
.speech-bubble {
  background: rgba(11, 15, 25, 0.9);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(56, 189, 248, 0.45);
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.6), 0 0 15px rgba(56, 189, 248, 0.25);
  border-radius: 20px;
  padding: 12px 20px;
  max-width: 340px;
  color: #fff;
}
.speech-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
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
  animation: pulse 1s infinite;
}
.speech-content {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.45;
  color: #f1f5f9;
  text-shadow: 0 1px 2px rgba(0,0,0,0.4);
}
.speech-pointer {
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-top: 10px solid rgba(11, 15, 25, 0.9);
  margin-top: -1px;
}

/* 用户专属 Gemini 娘立绘 */
.gemini-mascot {
  position: relative;
  width: 440px;
  height: 580px;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  transform-origin: bottom center;
}

.character-wrapper {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  animation: artBreathe 3.8s ease-in-out infinite;
}

@keyframes artBreathe {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-10px) scale(1.008); }
}

.is-speaking {
  animation: speakSway 0.9s ease-in-out infinite;
}

@keyframes speakSway {
  0%, 100% { transform: translateY(-4px) rotate(-0.6deg) scale(1.004); }
  50% { transform: translateY(-12px) rotate(0.6deg) scale(1.012); }
}

.art-glow {
  position: absolute;
  bottom: 6%;
  left: 50%;
  transform: translateX(-50%);
  width: 78%;
  height: 16%;
  border-radius: 50%;
  background: radial-gradient(ellipse at center, rgba(56, 189, 248, 0.45) 0%, rgba(56, 189, 248, 0) 70%);
  filter: blur(14px);
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
  50% { opacity: 1; transform: translateX(-50%) scale(1.06); }
}

.gemini-art-img {
  position: relative;
  z-index: 1;
  max-width: 100%;
  max-height: 560px;
  object-fit: contain;
  filter: drop-shadow(0 15px 35px rgba(0, 0, 0, 0.5)) drop-shadow(0 0 15px rgba(56, 189, 248, 0.2));
}

/* 嘴唇张合 (与立绘面部精确对齐) */
</style>
