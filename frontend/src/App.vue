<template>
  <div class="overlay-screen" :class="'theme-' + currentTheme">
    <!-- 顶部功能区 -->
    <div class="top-bar">
      <BgmPlayer ref="bgmRef" :isDucking="isSpeaking" />
      <DataHUD :stats="globalStats" />
    </div>

    <!-- 底部主舞台区 -->
    <div class="bottom-stage">
      <DanmuList ref="danmuListRef" />
      <Live2DStage :mouthOpenY="currentAmplitude" :scale="mascotScale" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useSSE } from './composables/useSSE';
import { useLipSync } from './composables/useLipSync';
import Live2DStage from './components/Live2DStage.vue';
import DanmuList from './components/DanmuList.vue';
import DataHUD from './components/DataHUD.vue';
import BgmPlayer from './components/BgmPlayer.vue';

const currentTheme = ref('transparent');
const mascotScale = ref(0.25);
const isSpeaking = ref(false);

const bgmRef = ref<any>(null);
const danmuListRef = ref<any>(null);

const globalStats = ref({
  total_tokens: 0,
  danmu_count: 0,
  ai_reply_count: 0,
  top_users: []
});

const { currentAmplitude, playBase64Audio } = useLipSync();

useSSE((eventName: string, data: any) => {
  if (eventName === 'danmu') {
    danmuListRef.value?.addDanmu(data);
  } else if (eventName === 'stats') {
    globalStats.value = data;
  } else if (eventName === 'bgm_action') {
    if (data.action === 'switch') {
      bgmRef.value?.setTrack(data.payload || '下一首元气旋律');
    } else if (data.action === 'pause') {
      bgmRef.value?.setPlayState(false);
    } else if (data.action === 'play') {
      bgmRef.value?.setPlayState(true);
    }
  } else if (eventName === 'config_sync') {
    if (data.theme) {
      currentTheme.value = data.theme === 'toggle'
        ? (currentTheme.value === 'transparent' ? 'deep_sea' : 'transparent')
        : data.theme;
    }
    if (data.mascot?.scale) {
      mascotScale.value = data.mascot.scale;
    }
  } else if (eventName === 'ai_speech') {
    if (data.audio) {
      isSpeaking.value = true;
      playBase64Audio(data.audio, () => {
        isSpeaking.value = false;
      });
    }
  }
});
</script>

<style>
.overlay-screen {
  width: 100vw;
  height: 100vh;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 24px;
  box-sizing: border-box;
}
.theme-transparent { background: transparent !important; }
.theme-deep_sea { background: radial-gradient(circle at center, rgba(14, 116, 144, 0.4) 0%, rgba(15, 23, 42, 0.9) 100%); }
.top-bar { display: flex; justify-content: space-between; align-items: flex-start; }
.bottom-stage { display: flex; justify-content: space-between; align-items: flex-end; }
</style>
