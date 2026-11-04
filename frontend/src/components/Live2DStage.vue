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
let app: any = null;
let currentModel: any = null;

onMounted(async () => {
  if (!viewportRef.value) return;
  app = new PIXI.Application({
    width: 600,
    height: 800,
    backgroundAlpha: 0
  });
  viewportRef.value.appendChild(app.view as HTMLCanvasElement);

  (window as any).PIXI = PIXI;
  try {
    const { Live2DModel } = await import('pixi-live2d-display');
    // 尝试加载内置的 Gemini 娘 Live2D 模型包
    currentModel = await Live2DModel.from('/models/gemini/gemini.model3.json');
    currentModel.scale.set(props.scale || 0.25);
    currentModel.x = 100;
    currentModel.y = 150;
    app.stage.addChild(currentModel);
  } catch (err) {
    console.warn('Live2D 模型加载失败，切换到备用模式', err);
  }
});

// 监听 Web Audio 口型振幅，动态开合 Live2D 嘴唇
watch(() => props.mouthOpenY, (val) => {
  if (currentModel && currentModel.internalModel?.coreModel) {
    try {
      currentModel.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', val);
    } catch (e) {
      // 忽略参数不存在异常
    }
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
