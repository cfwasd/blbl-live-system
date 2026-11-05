<template>
  <div class="aurora-player-container">
    <!-- 播放器主体卡片 -->
    <div
      class="aurora-player"
      :class="{
        'is-ducking': isDucking,
        'is-minimized': isMinimized
      }"
    >
      <!-- 唱针 (Disc 模式) -->
      <div class="needle-arm" :class="{ 'needle-on': isPlaying }"></div>

      <!-- 旋转黑胶唱片 / 专辑封面 (点击切换最小化/展开) -->
      <div
        class="vinyl-disc-wrap"
        :class="{ 'is-spinning': isPlaying }"
        title="点击折叠/展开迷你模式"
        @click="toggleMinimize"
      >
        <div class="vinyl-disc">
          <img :src="currentTrack.cover" :alt="currentTrack.title" class="album-cover" />
          <div class="vinyl-center-core">
            <div class="center-hole"></div>
          </div>
        </div>
      </div>

      <!-- 展开视图下的播放器元信息与控制面板 -->
      <div v-show="!isMinimized" class="aurora-body">
        <!-- 顶部信息区：歌曲标题、艺术家与状态指示 -->
        <div class="track-header">
          <div class="track-info-wrap" :title="`${currentTrack.title} - ${currentTrack.artist}`">
            <span class="track-title">{{ currentTrack.title }}</span>
            <span class="track-artist">{{ currentTrack.artist }}</span>
          </div>

          <div class="header-tags">
            <span class="status-badge" :class="isDucking ? 'badge-ducking' : 'badge-playing'">
              {{ isDucking ? '🗣️ 避让 8%' : (isPlaying ? '🎶 播放中' : '⏸️ 已暂停') }}
            </span>
          </div>
        </div>

        <!-- 进度条与播放时间 -->
        <div class="progress-section">
          <div class="time-label">{{ formatTime(currentTime) }}</div>
          <div class="progress-bar-bg" ref="progressBgRef" @click="handleSeek">
            <div class="progress-bar-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <div class="time-label">{{ formatTime(duration) }}</div>
        </div>

        <!-- 控制按钮栏 (上一首、播放/暂停、下一首、模式切换、折叠按钮) -->
        <div class="controls-bar">
          <div class="main-buttons">
            <button class="btn-ctrl btn-prev" title="上一首" @click.stop="playPrevTrack">
              ⏮️
            </button>

            <button class="btn-ctrl btn-play-pause" :title="isPlaying ? '暂停' : '播放'" @click.stop="togglePlay">
              {{ isPlaying ? '⏸️' : '▶️' }}
            </button>

            <button class="btn-ctrl btn-next" title="下一首 (弹幕发送'切歌'亦可触发)" @click.stop="playNextTrack(true)">
              ⏭️
            </button>
          </div>

          <div class="mode-buttons">
            <button class="btn-mode" :title="isShuffle ? '当前模式: 随机播放' : '当前模式: 顺序循环'" @click.stop="toggleMode">
              {{ isShuffle ? '🔀' : '🔁' }}
            </button>

            <button class="btn-minimize" title="最小化到迷你唱片" @click.stop="toggleMinimize">
              ↙️
            </button>
          </div>
        </div>
      </div>

      <!-- 底层 HTML5 Audio 标签 -->
      <audio
        ref="audioRef"
        preload="auto"
        @timeupdate="onTimeUpdate"
        @loadedmetadata="onLoadedMetadata"
        @ended="onTrackEnded"
        @play="isPlaying = true"
        @pause="isPlaying = false"
        @error="onAudioError"
      ></audio>
    </div>

    <!-- 弹幕切歌与点歌触发通知气泡 (类似 AuroraPlayer 交互气泡) -->
    <transition name="toast-slide">
      <div v-if="toastMsg" class="aurora-toast">
        <span class="toast-icon">{{ toastIcon }}</span>
        <span class="toast-content">{{ toastMsg }}</span>
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
  (e: 'timeUpdate', time: number): void;
}>();

const baseUrl = import.meta.env.BASE_URL.replace(/\/$/, '') + '/';

export interface AuroraTrack {
  id: number | string;
  title: string;
  artist: string;
  cover: string;
  url: string;
  source?: string;
}

// 默认备选曲目
const DEFAULT_PLAYLIST: AuroraTrack[] = [
  {
    id: 1,
    title: '🌸 恋爱循环 (Renai Circulation)',
    artist: '花泽香菜 · 元气BGM',
    cover: 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=140&auto=format&fit=crop&q=80',
    url: `${baseUrl}bgm/bgm_01.mp3`
  },
  {
    id: 2,
    title: '☕ 晴天 (Sunny Day) · Lo-Fi',
    artist: '周杰伦 · 伴奏轻音',
    cover: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=140&auto=format&fit=crop&q=80',
    url: `${baseUrl}bgm/bgm_02.mp3`
  },
  {
    id: 3,
    title: '🌌 赛博星空夜曲 (Cyber Night)',
    artist: 'Synthwave · 梦幻电音',
    cover: 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=140&auto=format&fit=crop&q=80',
    url: `${baseUrl}bgm/bgm_03.mp3`
  }
];

// 响应式曲库列表
const playlist = ref<AuroraTrack[]>(DEFAULT_PLAYLIST);
const currentIndex = ref(0);
const isPlaying = ref(false);
const isMinimized = ref(false);
const isShuffle = ref(false);

const currentTime = ref(0);
const duration = ref(0);

const audioRef = ref<HTMLAudioElement | null>(null);
const progressBgRef = ref<HTMLDivElement | null>(null);

const currentTrack = computed(() => playlist.value[currentIndex.value] || DEFAULT_PLAYLIST[0]);
const progressPercent = computed(() => {
  if (duration.value <= 0) return 0;
  return Math.min(100, Math.max(0, (currentTime.value / duration.value) * 100));
});

// Toast 状态
const toastMsg = ref('');
const toastIcon = ref('🎵');
let toastTimer: any = null;

const showNotification = (msg: string, icon = '🎵') => {
  toastMsg.value = msg;
  toastIcon.value = icon;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastMsg.value = '';
  }, 3500);
};

const DEFAULT_VOLUME = 0.35;
const DUCK_VOLUME = 0.08;

// 监听 AI 播报避让 (Audio Ducking)
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

watch(() => props.isDucking, (ducking) => {
  setVolumeSmoothly(ducking ? DUCK_VOLUME : DEFAULT_VOLUME);
});

// 格式化时间 mm:ss
const formatTime = (secs: number) => {
  if (isNaN(secs)) return '00:00';
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
};

// 切歌方法
const loadAndPlayTrack = (track: AuroraTrack) => {
  if (audioRef.value && track) {
    audioRef.value.src = track.url;
    audioRef.value.volume = props.isDucking ? DUCK_VOLUME : DEFAULT_VOLUME;
    audioRef.value.play().then(() => {
      isPlaying.value = true;
      emit('playStarted');
    }).catch((e) => {
      console.warn('AuroraPlayer 自动起播等待交互', e);
      isPlaying.value = false;
      emit('autoplayBlocked');
    });
  }
};

// 点歌专用方法：将歌曲插入曲库头部并立即播送
const playSong = (song: AuroraTrack, uname = '观众') => {
  if (!song || !song.url) return;
  const existingIdx = playlist.value.findIndex(t => t.id === song.id);
  if (existingIdx !== -1) {
    currentIndex.value = existingIdx;
  } else {
    playlist.value.unshift(song);
    currentIndex.value = 0;
  }
  showNotification(`观众【${uname}】点歌成功: 《${song.title}》`, '🎉');
  loadAndPlayTrack(playlist.value[currentIndex.value]);
};

const playNextTrack = (userAction = false, byDanmu = false, triggerUser = '') => {
  const list = playlist.value;
  if (!list.length) return;
  if (isShuffle.value) {
    let nextIdx = Math.floor(Math.random() * list.length);
    if (nextIdx === currentIndex.value && list.length > 1) {
      nextIdx = (nextIdx + 1) % list.length;
    }
    currentIndex.value = nextIdx;
  } else {
    currentIndex.value = (currentIndex.value + 1) % list.length;
  }

  const track = list[currentIndex.value];
  if (byDanmu) {
    showNotification(`观众【${triggerUser || '热心观众'}】切歌: 《${track.title}》`, '🔀');
  } else if (userAction) {
    showNotification(`已切歌: 《${track.title}》`, '🔀');
  }
  loadAndPlayTrack(track);
};

const playPrevTrack = () => {
  const list = playlist.value;
  if (!list.length) return;
  currentIndex.value = (currentIndex.value - 1 + list.length) % list.length;
  const track = list[currentIndex.value];
  showNotification(`上一首: 《${track.title}》`, '⏮️');
  loadAndPlayTrack(track);
};

const cleanSongName = (str: string) => {
  return str.replace(/^(?:点歌|想听|来一首|来首|播放|听)[\s:：]*/i, '').replace(/^[《“\"'【\[]+|[》”\"'】\]]+$/g, '').trim();
};

// 本地点歌匹配兜底
const requestSong = async (songQuery: string, uname = '观众') => {
  const query = cleanSongName(songQuery) || songQuery.trim();
  // 1. 先尝试向后端在线点歌解析接口搜索
  try {
    const res = await fetch(`/api/music/search?keyword=${encodeURIComponent(query)}`);
    if (res.ok) {
      const data = await res.json();
      if (data.status === 'ok' && data.song) {
        playSong(data.song, uname);
        return;
      }
    }
  } catch (e) {
    console.warn('在线点歌搜索异常，进入本地模糊匹配', e);
  }

  // 2. 本地曲目模糊匹配
  const foundIdx = playlist.value.findIndex(t =>
    t.title.toLowerCase().includes(query.toLowerCase()) ||
    t.artist.toLowerCase().includes(query.toLowerCase())
  );

  if (foundIdx !== -1) {
    currentIndex.value = foundIdx;
    const track = playlist.value[foundIdx];
    showNotification(`观众【${uname}】点歌: 《${track.title}》`, '🎉');
    loadAndPlayTrack(track);
  } else {
    playNextTrack(false, false);
    const track = playlist.value[currentIndex.value];
    showNotification(`收到观众【${uname}】点歌【${songQuery}】，为你播送《${track.title}》`, '🎵');
  }
};

const togglePlay = () => {
  if (!audioRef.value) return;
  if (audioRef.value.paused) {
    if (!audioRef.value.src) {
      loadAndPlayTrack(playlist.value[currentIndex.value]);
    } else {
      audioRef.value.play().then(() => {
        isPlaying.value = true;
        emit('playStarted');
      }).catch(() => {
        loadAndPlayTrack(playlist.value[currentIndex.value]);
      });
    }
  } else {
    audioRef.value.pause();
    isPlaying.value = false;
  }
};

const toggleMinimize = () => {
  isMinimized.value = !isMinimized.value;
};

const toggleMode = () => {
  isShuffle.value = !isShuffle.value;
  showNotification(isShuffle.value ? '模式: 随机播放' : '模式: 列表循环', isShuffle.value ? '🔀' : '🔁');
};

const handleSeek = (e: MouseEvent) => {
  if (!progressBgRef.value || !audioRef.value || duration.value <= 0) return;
  const rect = progressBgRef.value.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const percent = Math.min(1, Math.max(0, clickX / rect.width));
  audioRef.value.currentTime = percent * duration.value;
};

const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime;
    emit('timeUpdate', currentTime.value);
  }
};

const onLoadedMetadata = () => {
  if (audioRef.value) {
    duration.value = audioRef.value.duration;
  }
};

const onTrackEnded = () => {
  playNextTrack(false, false);
};

const onAudioError = () => {
  console.warn('AuroraPlayer 音轨加载出错，自动跳下一首');
  playNextTrack(false, false);
};

const tryPlay = () => {
  if (audioRef.value) {
    if (!audioRef.value.src) {
      const track = currentTrack.value;
      audioRef.value.src = track.url;
      audioRef.value.volume = props.isDucking ? DUCK_VOLUME : DEFAULT_VOLUME;
    }
    return audioRef.value.play().then(() => {
      isPlaying.value = true;
      emit('playStarted');
      return true;
    }).catch(() => {
      isPlaying.value = false;
      return false;
    });
  }
  return Promise.resolve(false);
};

// 暴露给外层调用 (弹幕切歌、点歌、管理端后台控制)
const setTrack = (payload?: string, uname?: string) => {
  if (payload) {
    requestSong(payload, uname || '观众');
  } else {
    playNextTrack(false, true, uname || '观众');
  }
};

const setPlayState = (play: boolean) => {
  if (audioRef.value) {
    if (play) {
      if (!audioRef.value.src) {
        loadAndPlayTrack(playlist.value[currentIndex.value]);
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

onMounted(async () => {
  // 1. 初次挂载时在线拉取推荐歌单曲库
  try {
    const res = await fetch('/api/music/playlist');
    if (res.ok) {
      const data = await res.json();
      if (data.status === 'ok' && data.playlist && data.playlist.length > 0) {
        playlist.value = data.playlist;
        currentIndex.value = 0;
      }
    }
  } catch (e) {
    console.warn('拉取在线歌单异常，使用备用曲库', e);
  }

  // 2. 初始起播
  if (audioRef.value) {
    const track = currentTrack.value;
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

defineExpose({
  playNextTrack,
  playPrevTrack,
  requestSong,
  playSong,
  setTrack,
  setPlayState,
  togglePlay,
  tryPlay,
  isPlaying,
  currentTrack
});
</script>

<style scoped>
.aurora-player-container {
  position: relative;
  display: flex;
  flex-direction: column;
  user-select: none;
}

/* AuroraPlayer 主卡片 (NeteaseMiniPlayer 亚克力微型播放器质感) */
.aurora-player {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  background: rgba(11, 15, 25, 0.88);
  backdrop-filter: blur(24px);
  border: 1.5px solid rgba(56, 189, 248, 0.32);
  padding: 10px 18px 10px 14px;
  border-radius: 24px;
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.55), inset 0 0 14px rgba(56, 189, 248, 0.1);
  color: #fff;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 320px;
}

.aurora-player:hover {
  border-color: rgba(56, 189, 248, 0.6);
  box-shadow: 0 18px 44px rgba(0, 0, 0, 0.65), 0 0 20px rgba(56, 189, 248, 0.2);
}

.is-ducking {
  border-color: rgba(244, 63, 94, 0.55);
  box-shadow: 0 0 25px rgba(244, 63, 94, 0.3);
}

.is-minimized {
  min-width: auto;
  padding: 8px;
  border-radius: 50px;
}

/* 唱针臂 */
.needle-arm {
  position: absolute;
  top: 4px;
  left: 38px;
  width: 24px;
  height: 3.5px;
  background: #94a3b8;
  transform-origin: 0 50%;
  transform: rotate(-35deg);
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  border-radius: 2px;
  z-index: 10;
  box-shadow: 0 1px 4px rgba(0,0,0,0.6);
}
.needle-on {
  transform: rotate(8deg);
}

/* 旋转黑胶唱片包装 */
.vinyl-disc-wrap {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  cursor: pointer;
  flex-shrink: 0;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.is-spinning .vinyl-disc {
  animation: spinVinyl 6s linear infinite;
}
@keyframes spinVinyl {
  100% { transform: rotate(360deg); }
}

.vinyl-disc {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: radial-gradient(#111827 30%, #030712 100%);
  border: 2px solid #374151;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
}

.album-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
  opacity: 0.85;
}

.vinyl-center-core {
  position: absolute;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, #06b6d4, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 6px rgba(6, 182, 212, 0.6);
}
.center-hole {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #030712;
}

/* 展开区域：歌曲信息与进度控制 */
.aurora-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-width: 240px;
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.track-info-wrap {
  display: flex;
  flex-direction: column;
  max-width: 180px;
}
.track-title {
  font-size: 13px;
  font-weight: 800;
  color: #f1f5f9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 0.3px;
}
.track-artist {
  font-size: 10px;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-tags {
  display: flex;
  align-items: center;
  gap: 6px;
}
.status-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 10px;
}
.badge-playing {
  background: rgba(56, 189, 248, 0.18);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.35);
}
.badge-ducking {
  background: rgba(244, 63, 94, 0.2);
  color: #fb7185;
  border: 1px solid rgba(244, 63, 94, 0.4);
}

/* 进度条 */
.progress-section {
  display: flex;
  align-items: center;
  gap: 8px;
}
.time-label {
  font-family: monospace;
  font-size: 9px;
  color: #64748b;
  min-width: 28px;
}
.progress-bar-bg {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 3px;
  overflow: hidden;
  cursor: pointer;
  position: relative;
}
.progress-bar-bg:hover {
  height: 6px;
}
.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #38bdf8, #a855f7);
  box-shadow: 0 0 8px #38bdf8;
  border-radius: 3px;
  transition: width 0.1s linear;
}

/* 控制按钮栏 */
.controls-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 2px;
}

.main-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}
.btn-ctrl {
  background: transparent;
  border: none;
  font-size: 13px;
  cursor: pointer;
  opacity: 0.8;
  transition: all 0.2s;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-ctrl:hover {
  opacity: 1;
  transform: scale(1.15);
}
.btn-play-pause {
  font-size: 15px;
}

.mode-buttons {
  display: flex;
  align-items: center;
  gap: 6px;
}
.btn-mode, .btn-minimize {
  background: transparent;
  border: none;
  font-size: 11px;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s, transform 0.2s;
  padding: 0;
}
.btn-mode:hover, .btn-minimize:hover {
  opacity: 1;
  transform: scale(1.15);
}

/* 弹幕切歌与点歌通知 Toast */
.aurora-toast {
  position: absolute;
  top: 76px;
  left: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.95), rgba(168, 85, 247, 0.95));
  backdrop-filter: blur(12px);
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45), 0 0 12px rgba(168, 85, 247, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.3);
  pointer-events: none;
  z-index: 100;
}
.toast-icon { font-size: 14px; }
.toast-content { letter-spacing: 0.3px; }

.toast-slide-enter-active, .toast-slide-leave-active {
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
.toast-slide-enter-from, .toast-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.95);
}
</style>
