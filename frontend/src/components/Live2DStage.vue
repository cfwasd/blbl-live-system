<template>
  <div class="live2d-viewport" ref="viewportRef">
    <!-- 当外部 Live2D 模型未挂载或加载中时，展示 Gemini 娘动态萌系形象 (呼吸、眨眼、声波口型) -->
    <div v-show="!hasLive2DModel" class="gemini-mascot" :style="{ transform: 'scale(' + (scale || 1.0) + ')' }">
      <!-- 头部与装饰 -->
      <div class="character-wrapper">
        <!-- 蓝紫渐变双马尾 (左/右) -->
        <div class="twintail left-twintail"></div>
        <div class="twintail right-twintail"></div>

        <!-- 角色头部 -->
        <div class="head">
          <!-- 头发刘海 -->
          <div class="bangs"></div>
          <!-- Gemini 标志性星芒发卡 -->
          <div class="star-clip">✦</div>

          <!-- 脸蛋与腮红 -->
          <div class="blush left-blush"></div>
          <div class="blush right-blush"></div>

          <!-- 双眼 (带自动眨眼动画) -->
          <div class="eyes">
            <div class="eye left-eye">
              <div class="pupil"></div>
              <div class="sparkle"></div>
            </div>
            <div class="eye right-eye">
              <div class="pupil"></div>
              <div class="sparkle"></div>
            </div>
          </div>

          <!-- 动态嘴型：随 Web Audio 振幅实时张合 (ParamMouthOpenY LipSync) -->
          <div class="mouth" :style="{
            height: Math.max(4, mouthOpenY * 22) + 'px',
            borderRadius: mouthOpenY > 0.2 ? '10px 10px 20px 20px' : '2px 2px 8px 8px'
          }"></div>
        </div>

        <!-- 科技感二次元水手服身体 (呼吸律动) -->
        <div class="body">
          <div class="collar"></div>
          <div class="ribbon">★</div>
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

    // 优先尝试导入 Cubism 4 独立模块
    let Live2DModel: any = null;
    try {
      const cubism4Module = await import('pixi-live2d-display/cubism4');
      Live2DModel = cubism4Module.Live2DModel;
    } catch {
      const standardModule = await import('pixi-live2d-display');
      Live2DModel = standardModule.Live2DModel;
    }

    if (Live2DModel) {
      // 尝试加载 models/gemini/ 下的模型
      currentModel = await Live2DModel.from('/models/gemini/gemini.model3.json');
      currentModel.scale.set(props.scale || 0.25);
      currentModel.x = 100;
      currentModel.y = 150;
      app.stage.addChild(currentModel);
      hasLive2DModel.value = true;
    }
  } catch (err) {
    console.warn('Live2D 资产尚未就绪，已平滑无感启用内置 Gemini 娘动态高保真立绘', err);
    hasLive2DModel.value = false;
  }
});

// 监听 Web Audio 口型振幅，动态更新 Live2D 参数
watch(() => props.mouthOpenY, (val) => {
  if (currentModel && currentModel.internalModel?.coreModel) {
    try {
      currentModel.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', val);
    } catch (e) {
      // 容错处理
    }
  }
});
</script>

<style scoped>
.live2d-viewport {
  width: 480px;
  height: 620px;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  pointer-events: none;
}

/* 内置 Gemini 娘动态矢量形象 */
.gemini-mascot {
  position: absolute;
  bottom: 20px;
  width: 320px;
  height: 480px;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  transform-origin: bottom center;
  transition: transform 0.2s ease-out;
}

.character-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: breathe 3.6s ease-in-out infinite;
}

@keyframes breathe {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

/* 头部 */
.head {
  width: 170px;
  height: 160px;
  background: #fff3ec;
  border-radius: 90px 90px 85px 85px;
  position: relative;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  z-index: 2;
}

/* 蓝紫星芒渐变双马尾 */
.twintail {
  position: absolute;
  top: 30px;
  width: 80px;
  height: 240px;
  background: linear-gradient(170deg, #38bdf8 0%, #818cf8 40%, #c084fc 100%);
  border-radius: 50% 50% 70% 30% / 60% 60% 40% 40%;
  z-index: 1;
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.35);
}
.left-twintail {
  left: -55px;
  transform-origin: top right;
  animation: swayLeft 4s ease-in-out infinite;
}
.right-twintail {
  right: -55px;
  transform-origin: top left;
  animation: swayRight 4s ease-in-out infinite;
}

@keyframes swayLeft {
  0%, 100% { transform: rotate(-8deg); }
  50% { transform: rotate(-18deg); }
}
@keyframes swayRight {
  0%, 100% { transform: rotate(8deg); }
  50% { transform: rotate(18deg); }
}

/* 刘海发型 */
.bangs {
  position: absolute;
  top: -6px;
  left: 10px;
  width: 150px;
  height: 70px;
  background: linear-gradient(135deg, #38bdf8, #818cf8);
  border-radius: 40px 40px 30px 30px;
  z-index: 4;
}

/* 发卡 */
.star-clip {
  position: absolute;
  top: 18px;
  right: 18px;
  color: #facc15;
  font-size: 26px;
  z-index: 5;
  filter: drop-shadow(0 0 6px rgba(250, 204, 21, 0.8));
}

/* 双眼与眨眼动效 */
.eyes {
  position: absolute;
  top: 75px;
  width: 100%;
  display: flex;
  justify-content: space-around;
  padding: 0 25px;
  box-sizing: border-box;
  z-index: 3;
}
.eye {
  width: 26px;
  height: 38px;
  background: linear-gradient(180deg, #1e1b4b 0%, #4338ca 60%, #38bdf8 100%);
  border-radius: 50%;
  position: relative;
  overflow: hidden;
  animation: blink 4.2s infinite;
}
@keyframes blink {
  0%, 94%, 100% { transform: scaleY(1); }
  97% { transform: scaleY(0.08); }
}
.pupil {
  width: 14px;
  height: 18px;
  background: #312e81;
  border-radius: 50%;
  position: absolute;
  top: 10px;
  left: 6px;
}
.sparkle {
  width: 8px;
  height: 8px;
  background: #fff;
  border-radius: 50%;
  position: absolute;
  top: 5px;
  left: 6px;
  box-shadow: 0 0 4px #fff;
}

/* 腮红 */
.blush {
  position: absolute;
  top: 105px;
  width: 24px;
  height: 12px;
  background: rgba(244, 63, 94, 0.4);
  border-radius: 50%;
  filter: blur(2px);
  z-index: 3;
}
.left-blush { left: 16px; }
.right-blush { right: 16px; }

/* 实时动态声波口型 (LipSync) */
.mouth {
  position: absolute;
  bottom: 22px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  min-height: 4px;
  background: #e11d48;
  border: 2px solid #be123c;
  transition: height 0.08s ease-out, border-radius 0.08s;
  z-index: 3;
}

/* 身体与服装 */
.body {
  width: 110px;
  height: 130px;
  background: linear-gradient(180deg, #ffffff 0%, #e2e8f0 100%);
  border-radius: 30px 30px 20px 20px;
  position: relative;
  margin-top: -20px;
  z-index: 1;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}
.collar {
  position: absolute;
  top: 0;
  width: 100%;
  height: 35px;
  background: #3b82f6;
  clip-path: polygon(0 0, 100% 0, 85% 100%, 15% 100%);
}
.ribbon {
  position: absolute;
  top: 25px;
  left: 50%;
  transform: translateX(-50%);
  color: #facc15;
  font-size: 20px;
  filter: drop-shadow(0 0 4px rgba(250, 204, 21, 0.6));
}
</style>
