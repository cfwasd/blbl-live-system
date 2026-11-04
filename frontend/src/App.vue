<template>
  <div class="overlay-screen" :class="'theme-' + currentTheme">
    <!-- 顶部居中 SuperChat 醒目打赏区 -->
    <SuperChat ref="scRef" />

    <!-- 顶部两侧功能区 -->
    <div class="top-bar">
      <BgmPlayer ref="bgmRef" :isDucking="isSpeaking" />
      <DataHUD :stats="globalStats" />
    </div>

    <!-- 底部主舞台区 -->
    <div class="bottom-stage">
      <DanmuList ref="danmuListRef" />
      <Live2DStage
        :mouthOpenY="currentAmplitude"
        :scale="mascotScale"
        :isSpeaking="isSpeaking"
        :speechText="currentSpeechText"
      />
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
import SuperChat from './components/SuperChat.vue';

const currentTheme = ref('transparent');
const mascotScale = ref(0.25);
const isSpeaking = ref(false);
const currentSpeechText = ref('');

const scRef = ref<any>(null);
const bgmRef = ref<any>(null);
const danmuListRef = ref<any>(null);

const globalStats = ref({
  total_tokens: 0,
  danmu_count: 0,
  ai_reply_count: 0,
  blocked_count: 0,
  top_users: []
});

const { currentAmplitude, playBase64Audio } = useLipSync();

useSSE((eventName: string, data: any) => {
  if (eventName === 'danmu') {
    danmuListRef.value?.addDanmu(data);
  } else if (eventName === 'super_chat') {
    scRef.value?.addSC(data);
    danmuListRef.value?.addDanmu({
      id: data.id,
      uname: data.uname,
      content: `[SC ￥${data.price}] ${data.content}`,
      badge: '醒目留言',
      level: 20
    });
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
    currentSpeechText.value = data.text || '';
    if (data.audio) {
      isSpeaking.value = true;
      playBase64Audio(data.audio, () => {
        isSpeaking.value = false;
        setTimeout(() => {
          if (!isSpeaking.value) currentSpeechText.value = '';
        }, 1500);
      });
    } else {
      // 无音频时显示字幕 3 秒
      isSpeaking.value = true;
      setTimeout(() => {
        isSpeaking.value = false;
        currentSpeechText.value = '';
      }, 3500);
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
  padding: 24px 32px;
  box-sizing: border-box;
  overflow: hidden;
}
.theme-transparent {
  background: transparent !important;
}
.theme-deep_sea {
  background: radial-gradient(circle at 75% 85%, rgba(67, 56, 202, 0.4) 0%, rgba(15, 23, 42, 0.85) 50%, rgba(2, 6, 23, 0.95) 100%);
}
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  z-index: 20;
}
.bottom-stage {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  z-index: 20;
}
</style>
