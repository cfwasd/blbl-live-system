<template>
  <div class="bgm-player" :class="{ 'is-ducking': isDucking }">
    <!-- 唱针 -->
    <div class="needle-arm" :class="{ 'needle-on': isPlaying }"></div>

    <!-- 旋转黑胶唱片 -->
    <div class="vinyl-disc" :class="{ 'is-spinning': isPlaying }">
      <div class="vinyl-groove groove-1"></div>
      <div class="vinyl-groove groove-2"></div>
      <div class="vinyl-center-label">
        <div class="vinyl-center-hole"></div>
      </div>
    </div>

    <!-- 歌曲信息与音频跳动频谱 -->
    <div class="bgm-meta">
      <div class="meta-top">
        <span class="music-icon">🎵</span>
        <div class="track-title-wrapper">
          <span class="track-title">{{ currentTrackTitle }}</span>
        </div>
      </div>

      <div class="meta-bottom">
        <!-- 动态跳动频谱波形条 (8段) -->
        <div class="equalizer" :class="{ 'eq-paused': !isPlaying || isDucking }">
          <span class="eq-bar bar-1"></span>
          <span class="eq-bar bar-2"></span>
          <span class="eq-bar bar-3"></span>
          <span class="eq-bar bar-4"></span>
          <span class="eq-bar bar-5"></span>
          <span class="eq-bar bar-6"></span>
        </div>
        <span class="status-tag" :class="isDucking ? 'tag-ducking' : 'tag-playing'">
          {{ isDucking ? '🗣️ 避让 8%' : '🎶 35%' }}
        </span>
      </div>
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
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  background: rgba(11, 15, 25, 0.78);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  padding: 10px 18px 10px 14px;
  border-radius: 50px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), inset 0 0 10px rgba(255, 255, 255, 0.05);
  color: #fff;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
}
.is-ducking {
  border-color: rgba(244, 63, 94, 0.4);
  box-shadow: 0 0 20px rgba(244, 63, 94, 0.2);
}

/* 唱针 */
.needle-arm {
  position: absolute;
  top: 4px;
  left: 36px;
  width: 24px;
  height: 3px;
  background: #94a3b8;
  border-radius: 2px;
  transform-origin: top left;
  transform: rotate(-35deg);
  transition: transform 0.4s ease;
  z-index: 5;
}
.needle-on {
  transform: rotate(5deg);
}

/* 黑胶唱片机 */
.vinyl-disc {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: radial-gradient(#111827 40%, #030712 100%);
  border: 2px solid #374151;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
  flex-shrink: 0;
}
.is-spinning {
  animation: spin 5s linear infinite;
}
@keyframes spin {
  100% { transform: rotate(360deg); }
}
.vinyl-groove {
  position: absolute;
  border-radius: 50%;
  border: 1px dashed rgba(255, 255, 255, 0.15);
}
.groove-1 { width: 34px; height: 34px; }
.groove-2 { width: 24px; height: 24px; }
.vinyl-center-label {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: linear-gradient(135deg, #06b6d4, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
}
.vinyl-center-hole {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #030712;
}

/* 元数据与跳动频谱 */
.bgm-meta {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.meta-top {
  display: flex;
  align-items: center;
  gap: 6px;
}
.music-icon { font-size: 12px; }
.track-title {
  font-size: 12px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: 0.3px;
  max-width: 140px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta-bottom {
  display: flex;
  align-items: center;
  gap: 8px;
}
.equalizer {
  display: flex;
  align-items: flex-end;
  gap: 2.5px;
  height: 12px;
}
.eq-bar {
  width: 2.5px;
  background: #38bdf8;
  border-radius: 2px;
  animation: bounce 1.2s ease-in-out infinite alternate;
}
.bar-1 { height: 4px; animation-delay: 0.1s; }
.bar-2 { height: 10px; animation-delay: 0.4s; }
.bar-3 { height: 6px; animation-delay: 0.2s; }
.bar-4 { height: 12px; animation-delay: 0.6s; }
.bar-5 { height: 8px; animation-delay: 0.3s; }
.bar-6 { height: 5px; animation-delay: 0.5s; }

@keyframes bounce {
  0% { height: 3px; }
  100% { height: 12px; }
}
.eq-paused .eq-bar {
  animation: none !important;
  height: 3px !important;
  background: #64748b;
}

.status-tag {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 6px;
}
.tag-playing {
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
}
.tag-ducking {
  background: rgba(244, 63, 94, 0.2);
  color: #fb7185;
}
</style>
