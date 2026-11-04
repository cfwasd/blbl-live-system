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

    <!-- 内置高保真二次元 Gemini 娘动态形象 (零白屏、开箱即用) -->
    <div v-show="!hasLive2DModel" class="gemini-mascot" :style="{ transform: 'scale(' + (scale || 1.0) + ')' }">
      <div class="character-wrapper">
        <!-- 头部装饰与呆毛 -->
        <div class="ahoge"></div>
        <div class="halo"></div>

        <!-- 飘逸双马尾 (深浅蓝紫渐变) -->
        <div class="twintail left-twintail">
          <div class="tail-layer inner-tail"></div>
        </div>
        <div class="twintail right-twintail">
          <div class="tail-layer inner-tail"></div>
        </div>

        <!-- 头部 -->
        <div class="head">
          <!-- 科技赛博发饰/耳机 -->
          <div class="headphone left-headphone"></div>
          <div class="headphone right-headphone"></div>

          <!-- 刘海发型 -->
          <div class="hair-front">
            <div class="bang bang-1"></div>
            <div class="bang bang-2"></div>
            <div class="bang bang-3"></div>
          </div>

          <!-- Gemini 黄金星芒发卡 -->
          <div class="gemini-star-clip">✦</div>

          <!-- 双眼 (深邃星空渐变 + 自然眨眼) -->
          <div class="eyes">
            <div class="eye left-eye">
              <div class="iris">
                <div class="glint-main"></div>
                <div class="glint-sub"></div>
              </div>
            </div>
            <div class="eye right-eye">
              <div class="iris">
                <div class="glint-main"></div>
                <div class="glint-sub"></div>
              </div>
            </div>
          </div>

          <!-- 腮红与高光 -->
          <div class="blush left-blush"></div>
          <div class="blush right-blush"></div>

          <!-- 真实声波口型 (LipSync) -->
          <div class="mouth" :style="{
            height: Math.max(5, mouthOpenY * 24) + 'px',
            width: (16 + mouthOpenY * 12) + 'px',
            borderRadius: mouthOpenY > 0.3 ? '8px 8px 18px 18px' : '4px 4px 10px 10px'
          }">
            <div class="teeth" v-show="mouthOpenY > 0.2"></div>
            <div class="tongue" v-show="mouthOpenY > 0.4"></div>
          </div>
        </div>

        <!-- 二次元服装与领结 -->
        <div class="body">
          <div class="sailor-collar"></div>
          <div class="star-brooch">★</div>
        </div>
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
let app: any = null;
let currentModel: any = null;

onMounted(async () => {
  if (!viewportRef.value) return;

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
      currentModel = await Live2DModel.from('/models/gemini/gemini.model3.json');
      currentModel.scale.set(props.scale || 0.25);
      currentModel.x = 100;
      currentModel.y = 150;
      app.stage.addChild(currentModel);
      hasLive2DModel.value = true;
    }
  } catch (err) {
    // 优雅无感兜底
    hasLive2DModel.value = false;
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

/* 头顶 AI 对话气泡 */
.speech-bubble-wrapper {
  position: absolute;
  top: 15px;
  right: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  opacity: 0;
  transform: translateY(12px) scale(0.9);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 40;
}
.speech-active {
  opacity: 1;
  transform: translateY(0) scale(1);
}
.speech-bubble {
  background: rgba(15, 23, 42, 0.88);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(56, 189, 248, 0.4);
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.5), 0 0 15px rgba(56, 189, 248, 0.2);
  border-radius: 20px;
  padding: 12px 18px;
  max-width: 320px;
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
  border-top: 10px solid rgba(15, 23, 42, 0.88);
  margin-top: -1px;
}

/* Gemini 娘立绘包装器 */
.gemini-mascot {
  position: relative;
  width: 380px;
  height: 520px;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  transform-origin: bottom center;
}

.character-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: idleFloat 4s ease-in-out infinite;
}
@keyframes idleFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

/* 呆毛与光环 */
.ahoge {
  position: absolute;
  top: -24px;
  left: 45%;
  width: 25px;
  height: 35px;
  border: 4px solid #38bdf8;
  border-color: #38bdf8 transparent transparent transparent;
  border-radius: 50%/20px 20px 0 0;
  transform: rotate(20deg);
  z-index: 10;
}
.halo {
  position: absolute;
  top: -18px;
  width: 140px;
  height: 25px;
  border: 2px solid rgba(168, 85, 247, 0.7);
  border-radius: 50%;
  box-shadow: 0 0 15px rgba(168, 85, 247, 0.5), inset 0 0 8px rgba(56, 189, 248, 0.4);
  transform: rotate(-5deg);
  animation: haloGlow 3s ease-in-out infinite alternate;
  z-index: 5;
}
@keyframes haloGlow {
  0% { opacity: 0.5; transform: rotate(-5deg) translateY(0); }
  100% { opacity: 0.9; transform: rotate(-5deg) translateY(-3px); }
}

/* 头部 */
.head {
  width: 190px;
  height: 180px;
  background: #fff5ee;
  border-radius: 100px 100px 90px 90px;
  position: relative;
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.35);
  z-index: 10;
}

/* 蓝紫双马尾 */
.twintail {
  position: absolute;
  top: 35px;
  width: 95px;
  height: 270px;
  background: linear-gradient(165deg, #38bdf8 0%, #6366f1 50%, #c084fc 100%);
  border-radius: 60% 60% 70% 30% / 70% 70% 30% 30%;
  z-index: 2;
  box-shadow: 0 12px 30px rgba(99, 102, 241, 0.35);
}
.left-twintail {
  left: -65px;
  transform-origin: top right;
  animation: tailSwayLeft 4.5s ease-in-out infinite;
}
.right-twintail {
  right: -65px;
  transform-origin: top left;
  animation: tailSwayRight 4.5s ease-in-out infinite;
}
@keyframes tailSwayLeft {
  0%, 100% { transform: rotate(-8deg); }
  50% { transform: rotate(-18deg) skewX(3deg); }
}
@keyframes tailSwayRight {
  0%, 100% { transform: rotate(8deg); }
  50% { transform: rotate(18deg) skewX(-3deg); }
}

/* 刘海 */
.hair-front {
  position: absolute;
  top: -8px;
  left: 0;
  width: 100%;
  height: 90px;
  z-index: 12;
  display: flex;
  justify-content: center;
}
.bang {
  background: linear-gradient(180deg, #38bdf8 0%, #818cf8 100%);
  border-radius: 0 0 25px 25px;
}
.bang-1 { width: 55px; height: 80px; margin-right: -10px; transform: rotate(-5deg); }
.bang-2 { width: 65px; height: 90px; z-index: 2; border-radius: 0 0 30px 30px; }
.bang-3 { width: 55px; height: 78px; margin-left: -10px; transform: rotate(5deg); }

.gemini-star-clip {
  position: absolute;
  top: 25px;
  right: 22px;
  color: #facc15;
  font-size: 30px;
  z-index: 15;
  filter: drop-shadow(0 0 8px rgba(250, 204, 21, 0.9));
  animation: starPulse 2.5s ease-in-out infinite alternate;
}
@keyframes starPulse {
  0% { transform: scale(1) rotate(0); }
  100% { transform: scale(1.15) rotate(15deg); }
}

/* 动漫眼瞳 */
.eyes {
  position: absolute;
  top: 85px;
  width: 100%;
  display: flex;
  justify-content: space-around;
  padding: 0 28px;
  box-sizing: border-box;
  z-index: 11;
}
.eye {
  width: 32px;
  height: 44px;
  background: #1e1b4b;
  border-radius: 50%;
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 3px 6px rgba(0, 0, 0, 0.6);
  animation: eyeBlink 4.5s infinite;
}
@keyframes eyeBlink {
  0%, 95%, 100% { transform: scaleY(1); }
  97.5% { transform: scaleY(0.08); }
}
.iris {
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, #1e1b4b 0%, #4338ca 45%, #38bdf8 100%);
  position: relative;
}
.glint-main {
  width: 12px;
  height: 12px;
  background: #ffffff;
  border-radius: 50%;
  position: absolute;
  top: 6px;
  left: 6px;
  box-shadow: 0 0 6px #fff;
}
.glint-sub {
  width: 6px;
  height: 6px;
  background: #ffffff;
  border-radius: 50%;
  position: absolute;
  bottom: 8px;
  right: 6px;
  opacity: 0.8;
}

/* 腮红 */
.blush {
  position: absolute;
  top: 120px;
  width: 30px;
  height: 14px;
  background: rgba(244, 63, 94, 0.45);
  border-radius: 50%;
  filter: blur(3px);
  z-index: 11;
}
.left-blush { left: 16px; }
.right-blush { right: 16px; }

/* 声波口型 */
.mouth {
  position: absolute;
  bottom: 22px;
  left: 50%;
  transform: translateX(-50%);
  background: #be123c;
  border: 2px solid #881337;
  overflow: hidden;
  transition: height 0.08s ease-out, width 0.08s ease-out, border-radius 0.08s;
  z-index: 11;
}
.teeth {
  width: 100%;
  height: 4px;
  background: #fff;
  border-radius: 0 0 4px 4px;
}
.tongue {
  position: absolute;
  bottom: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 14px;
  height: 10px;
  background: #fb7185;
  border-radius: 50%;
}

/* 服装 */
.body {
  width: 130px;
  height: 150px;
  background: linear-gradient(180deg, #f8fafc 0%, #cbd5e1 100%);
  border-radius: 35px 35px 20px 20px;
  position: relative;
  margin-top: -25px;
  z-index: 8;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25);
}
.sailor-collar {
  position: absolute;
  top: 0;
  width: 100%;
  height: 42px;
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  clip-path: polygon(0 0, 100% 0, 85% 100%, 15% 100%);
}
.star-brooch {
  position: absolute;
  top: 28px;
  left: 50%;
  transform: translateX(-50%);
  color: #facc15;
  font-size: 22px;
  filter: drop-shadow(0 0 6px rgba(250, 204, 21, 0.7));
}
</style>
