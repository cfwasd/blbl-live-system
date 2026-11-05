<template>
  <div class="bgm-player-container">
    <div class="bgm-player" :class="{ 'is-ducking': isDucking }" @click="togglePlayOrNext">
      <!-- 唱针 -->
      <div class="needle-arm" :class="{ 'needle-on': isPlaying }"></div>

      <!-- 旋转黑胶唱片 (可点击切换/播放) -->
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
          <span class="music-icon">{{ isPlaying ? '🎵' : '⏸️' }}</span>
          <div class="track-title-wrapper" :title="currentTrack.title">
            <span class="track-title">{{ currentTrack.title }}</span>
          </div>
        </div>

        <div class="meta-bottom">
          <!-- 动态跳动频谱波形条 -->
          <div class="equalizer" :class="{ 'eq-paused': !isPlaying || isDucking }">
            <span class="eq-bar bar-1"></span>
            <span class="eq-bar bar-2"></span>
            <span class="eq-bar bar-3"></span>
            <span class="eq-bar bar-4"></span>
            <span class="eq-bar bar-5"></span>
            <span class="eq-bar bar-6"></span>
          </div>

          <span class="status-tag" :class="isDucking ? 'tag-ducking' : 'tag-playing'">
            {{ isDucking ? '🗣️ 避让 8%' : (isPlaying ? `🎶 ${currentTrack.tag}` : '点击播放') }}
          </span>

          <!-- 弹幕切歌/下一首按钮 -->
          <button class="random-btn" title="切歌 (弹幕发送'切歌'亦可触发)" @click.stop="playNextTrack(true, true)">
            🔀
          </button>
        </div>
      </div>

      <audio
        ref="audioRef"
        preload="auto"
        @ended="onTrackEnded"
        @play="isPlaying = true"
        @pause="isPlaying = false"
        @error="onAudioError"
      ></audio>
    </div>

    <!-- 弹幕触发切歌实时提示气泡 -->
    <transition name="toast-fade">
      <div v-if="showTrackToast" class="track-change-toast">
        <span class="toast-icon">🔀</span>
        <span class="toast-text">已切换伴奏: {{ currentTrack.title }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';

const props = defineProps<{
  isDucking: boolean;
}>();

const emit = defineEmits<{
  (e: 'autoplayBlocked'): void;
  (e: 'playStarted'): void;
}>();

const baseUrl = import.meta.env.BASE_URL.replace(/\/$/, '') + '/';

export interface TrackItem {
  id: number;
  title: string;
  tag: string;
  url: string;
}

// 内置自带 3 套高质感离线伴奏音源
const PLAYLIST: TrackItem[] = [
  {
    id: 1,
    title: '🌸 二次元元气日常',
    tag: '元气日常',
    url: `${baseUrl}bgm/bgm_01.mp3`
  },
  {
    id: 2,
    title: '☕ 治愈系林间午后',
    tag: 'Lo-Fi治愈',
    url: `${baseUrl}bgm/bgm_02.mp3`
  },
  {
    id: 3,
    title: '🌌 赛博星空夜曲',
    tag: '赛博轻音',
    url: `${baseUrl}bgm/bgm_03.mp3`
  }
];

const currentIndex = ref(0);
const isPlaying = ref(false);
const currentTrack = computed(() => PLAYLIST[currentIndex.value]);
const showTrackToast = ref(false);
let toastTimer: any = null;

const audioRef = ref<HTMLAudioElement | null>(null);

const DEFAULT_VOLUME = 0.35;
const DUCK_VOLUME = 0.08;

// 平滑音量渐变 (Ducking)
const setVolumeSmoothly = (targetVol: number) => {
  if (!audioRef.value) return;
  const audio = audioRef.value;
  const step = (targetVol - audio.volume) / 10;
  let count = 0;
  const timer = setInterval(() => {
    count++;
    audio.volume = Math.max(0, Math.min(1, audio.volume + step));
    if (count >= 10 || Math.abs(audio.volume - targetVol) < 0.02) {
      audio.volume = targetVol;
      clearInterval(timer);
    }
  }, 20);
};

// 监听 AI 说话避让
watch(() => props.isDucking, (ducking) => {
  setVolumeSmoothly(ducking ? DUCK_VOLUME : DEFAULT_VOLUME);
});

const triggerToast = () => {
  showTrackToast.value = true;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    showTrackToast.value = false;
  }, 3000);
};

// 播放指定或随机下一首 (响应式驱动)
const playNextTrack = (random: boolean = true, showToast: boolean = true) => {
  if (random) {
    let nextIdx = Math.floor(Math.random() * PLAYLIST.length);
    if (nextIdx === currentIndex.value && PLAYLIST.length > 1) {
      nextIdx = (nextIdx + 1) % PLAYLIST.length;
    }
    currentIndex.value = nextIdx;
  } else {
    currentIndex.value = (currentIndex.value + 1) % PLAYLIST.length;
  }

  if (showToast) triggerToast();

  const track = PLAYLIST[currentIndex.value];
  if (audioRef.value) {
    audioRef.value.src = track.url;
    audioRef.value.volume = props.isDucking ? DUCK_VOLUME : DEFAULT_VOLUME;
    audioRef.value.play().then(() => {
      isPlaying.value = true;
      emit('playStarted');
    }).catch((e) => {
      console.warn('BGM 自动播放等待交互', e);
      isPlaying.value = false;
      emit('autoplayBlocked');
    });
  }
};

const onTrackEnded = () => {
  playNextTrack(false, false);
};

const onAudioError = () => {
  console.warn('当前音轨播放出错，自动跳至下一首自带曲目');
  playNextTrack(false, false);
};

const togglePlayOrNext = () => {
  if (!audioRef.value) return;
  if (audioRef.value.paused) {
    if (!audioRef.value.src) {
      playNextTrack(false, true);
    } else {
      audioRef.value.play().then(() => {
        isPlaying.value = true;
        emit('playStarted');
      }).catch(() => playNextTrack(true, true));
    }
  } else {
    audioRef.value.pause();
    isPlaying.value = false;
  }
};

const tryPlay = () => {
  if (audioRef.value) {
    if (!audioRef.value.src) {
      const track = PLAYLIST[currentIndex.value];
      audioRef.value.src = track.url;
      audioRef.value.volume = props.isDucking ? DUCK_VOLUME : DEFAULT_VOLUME;
    }
    return audioRef.value.play().then(() => {
      isPlaying.value = true;
      emit('playStarted');
      return true;
    }).catch((err) => {
      isPlaying.value = false;
      return false;
    });
  }
  return Promise.resolve(false);
};

// 暴露给外层调用 (弹幕切歌、点歌、管理端后台控制)
const setTrack = (title?: string, src?: string) => {
  if (src && audioRef.value) {
    audioRef.value.src = src;
    audioRef.value.play().catch(() => {});
    isPlaying.value = true;
    emit('playStarted');
    triggerToast();
  } else {
    playNextTrack(true, true);
  }
};

const setPlayState = (play: boolean) => {
  if (audioRef.value) {
    if (play) {
      if (!audioRef.value.src) {
        playNextTrack(false, false);
      } else {
        audioRef.value.play().catch(() => {});
      }
      isPlaying.value = true;
      emit('playStarted');
    } else {
      audioRef.value.pause();
      isPlaying.value = false;
    }
  }
};

onMounted(() => {
  if (audioRef.value) {
    const track = PLAYLIST[currentIndex.value];
    audioRef.value.src = track.url;
    audioRef.value.volume = DEFAULT_VOLUME;
    audioRef.value.play().then(() => {
      isPlaying.value = true;
      emit('playStarted');
    }).catch(() => {
      isPlaying.value = false;
      emit('autoplayBlocked');
    });
  }
});

onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer);
});

defineExpose({ setTrack, setPlayState, playNextTrack, tryPlay, isPlaying });
</script>

<style scoped>
.bgm-player-container {
  position: relative;
  display: flex;
  flex-direction: column;
}

.bgm-player {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  background: rgba(11, 15, 25, 0.85);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(56, 189, 248, 0.28);
  padding: 10px 18px 10px 14px;
  border-radius: 50px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 0 10px rgba(56, 189, 248, 0.1);
  color: #fff;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  user-select: none;
}
.bgm-player:hover {
  border-color: rgba(56, 189, 248, 0.55);
  transform: translateY(-2px);
}
.is-ducking {
  border-color: rgba(244, 63, 94, 0.5);
  box-shadow: 0 0 20px rgba(244, 63, 94, 0.25);
}

/* 唱针臂 */
.needle-arm {
  position: absolute;
  top: 4px;
  left: 36px;
  width: 22px;
  height: 3px;
  background: #94a3b8;
  transform-origin: 0 50%;
  transform: rotate(-35deg);
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  border-radius: 2px;
  z-index: 5;
  box-shadow: 0 1px 3px rgba(0,0,0,0.5);
}
.needle-on {
  transform: rotate(10deg);
}

/* 黑胶唱片机 */
.vinyl-disc {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: radial-gradient(#111827 40%, #030712 100%);
  border: 2px solid #374151;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
}
.is-spinning {
  animation: spinDisc 3.5s linear infinite;
}
@keyframes spinDisc {
  100% { transform: rotate(360deg); }
}

.vinyl-groove {
  position: absolute;
  border-radius: 50%;
  border: 1px dashed rgba(255, 255, 255, 0.15);
}
.groove-1 { width: 36px; height: 36px; }
.groove-2 { width: 26px; height: 26px; }
.vinyl-center-label {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, #06b6d4, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
}
.vinyl-center-hole {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #030712;
}

/* 歌曲元数据 */
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
.music-icon {
  font-size: 13px;
}
.track-title-wrapper {
  max-width: 170px;
  overflow: hidden;
}
.track-title {
  font-size: 12px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: 0.3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.meta-bottom {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 跳动频谱 (6段) */
.equalizer {
  display: flex;
  align-items: flex-end;
  gap: 2.5px;
  height: 12px;
}
.eq-bar {
  width: 2.5px;
  border-radius: 1px;
  background: #38bdf8;
  animation: eqBounce 0.8s ease-in-out infinite alternate;
}
.bar-1 { height: 6px; animation-delay: 0.1s; }
.bar-2 { height: 12px; animation-delay: 0.25s; }
.bar-3 { height: 8px; animation-delay: 0.15s; }
.bar-4 { height: 10px; animation-delay: 0.35s; }
.bar-5 { height: 5px; animation-delay: 0.2s; }
.bar-6 { height: 11px; animation-delay: 0.3s; }

.eq-paused .eq-bar {
  animation: none !important;
  height: 2px !important;
  opacity: 0.4;
}

@keyframes eqBounce {
  0% { transform: scaleY(0.25); }
  100% { transform: scaleY(1); }
}

.status-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 10px;
  letter-spacing: 0.5px;
}
.tag-playing {
  background: rgba(56, 189, 248, 0.18);
  color: #38bdf8;
}
.tag-ducking {
  background: rgba(244, 63, 94, 0.2);
  color: #fb7185;
}

.random-btn {
  background: transparent;
  border: none;
  font-size: 12px;
  cursor: pointer;
  opacity: 0.75;
  transition: opacity 0.2s, transform 0.2s;
  padding: 0;
}
.random-btn:hover {
  opacity: 1;
  transform: scale(1.15);
}

/* 切歌提示气泡 */
.track-change-toast {
  position: absolute;
  top: 56px;
  left: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.95), rgba(168, 85, 247, 0.95));
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
  pointer-events: none;
}
.toast-icon { font-size: 12px; }
.toast-fade-enter-active, .toast-fade-leave-active { transition: all 0.3s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
