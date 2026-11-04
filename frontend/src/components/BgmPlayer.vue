<template>
  <div class="bgm-player" :class="{ 'is-ducking': isDucking }">
    <div class="vinyl-disc" :class="{ 'is-spinning': isPlaying }">
      <div class="vinyl-core"></div>
    </div>
    <div class="bgm-info">
      <div class="track-title">🎵 {{ currentTrackTitle }}</div>
      <div class="status-tag">{{ isDucking ? '🗣️ AI 语音避让中...' : '🎶 伴奏播放中' }}</div>
    </div>
    <audio ref="audioRef" loop preload="auto"></audio>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineProps<{
  isDucking: boolean;
}>();

const isPlaying = ref(true);
const currentTrackTitle = ref('二次元元气日常伴奏');
const audioRef = ref<HTMLAudioElement | null>(null);

const setTrack = (title: string, src?: string) => {
  currentTrackTitle.value = title;
  if (src && audioRef.value) {
    audioRef.value.src = src;
    audioRef.value.play().catch(() => {});
  }
};

const setPlayState = (play: boolean) => {
  isPlaying.value = play;
  if (audioRef.value) {
    play ? audioRef.value.play().catch(() => {}) : audioRef.value.pause();
  }
};

defineExpose({ setTrack, setPlayState });
</script>

<style scoped>
.bgm-player {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 8px 14px;
  border-radius: 40px;
  color: #fff;
  transition: opacity 0.3s;
}
.is-ducking { opacity: 0.6; }
.vinyl-disc {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: radial-gradient(#111 60%, #333 100%);
  border: 2px solid #555;
  display: flex;
  align-items: center;
  justify-content: center;
}
.is-spinning { animation: spin 4s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.vinyl-core { width: 10px; height: 10px; border-radius: 50%; background: #38bdf8; }
.track-title { font-size: 12px; font-weight: 600; }
.status-tag { font-size: 10px; color: #94a3b8; }
</style>
