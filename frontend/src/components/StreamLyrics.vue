<template>
  <div class="stream-lyrics-card">
    <div class="lyrics-header">
      <div class="title-wrap">
        <span class="music-icon">🎤</span>
        <span class="lyrics-tag">实时伴奏歌词</span>
      </div>
      <span class="track-hint" :title="trackTitle">{{ trackTitle }}</span>
    </div>

    <!-- 动态歌词三行滚动视口 -->
    <div class="lyrics-viewport">
      <div v-if="parsedLyrics.length === 0" class="no-lyrics-hint">
        <div class="lrc-wave-bars">
          <span class="lb-1"></span>
          <span class="lb-2"></span>
          <span class="lb-3"></span>
          <span class="lb-4"></span>
          <span class="lb-5"></span>
        </div>
        <span class="hint-text">伴奏沉浸旋律中 · 暂无滚动歌词</span>
      </div>

      <div v-else class="lyrics-lines-container">
        <!-- 上一句歌词 -->
        <div class="lyric-line line-prev">
          {{ prevLineText }}
        </div>

        <!-- 当前正在唱的歌词 (高亮发光) -->
        <div class="lyric-line line-current">
          <span class="singing-dot">✦</span>
          <span class="active-text">{{ currentLineText }}</span>
          <span class="singing-dot">✦</span>
        </div>

        <!-- 下一句歌词 -->
        <div class="lyric-line line-next">
          {{ nextLineText }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';

interface LyricLine {
  time: number;
  text: string;
}

const props = withDefaults(defineProps<{
  trackId?: number | string;
  trackTitle?: string;
  currentTime?: number;
}>(), {
  trackId: 0,
  trackTitle: '当前伴奏',
  currentTime: 0
});

const parsedLyrics = ref<LyricLine[]>([]);
const currentIndex = ref(0);

// 解析标准 LRC 歌词文本
const parseLRC = (lrcStr: string): LyricLine[] => {
  if (!lrcStr) return [];
  const lines = lrcStr.split(/\r?\n/);
  const result: LyricLine[] = [];
  const timeRegex = /\[(\d{2}):(\d{2})\.(\d{2,3})\]/g;

  for (const line of lines) {
    const text = line.replace(timeRegex, '').trim();
    if (!text) continue;

    let match;
    timeRegex.lastIndex = 0;
    while ((match = timeRegex.exec(line)) !== null) {
      const minutes = parseInt(match[1], 10);
      const seconds = parseInt(match[2], 10);
      const ms = parseInt(match[3].padEnd(3, '0').slice(0, 3), 10);
      const totalSecs = minutes * 60 + seconds + ms / 1000;
      result.push({ time: totalSecs, text });
    }
  }

  // 排序
  result.sort((a, b) => a.time - b.time);
  return result;
};

// 拉取当前歌曲歌词
const fetchLyric = async (id: number | string) => {
  parsedLyrics.value = [];
  currentIndex.value = 0;
  if (!id) return;

  try {
    const res = await fetch(`/api/music/lyric?id=${id}`);
    if (res.ok) {
      const data = await res.json();
      if (data.status === 'ok' && data.lyric) {
        parsedLyrics.value = parseLRC(data.lyric);
      }
    }
  } catch (e) {
    console.warn('拉取歌词异常:', e);
  }
};

// 监听歌曲 ID 变化重新加载歌词
watch(() => props.trackId, (newId) => {
  if (newId) {
    fetchLyric(newId);
  }
}, { immediate: true });

// 监听播放时间匹配当前行
watch(() => props.currentTime, (t) => {
  if (!parsedLyrics.value.length) return;
  const list = parsedLyrics.value;
  // 查找匹配的当前行
  let idx = 0;
  for (let i = 0; i < list.length; i++) {
    if (list[i].time <= t) {
      idx = i;
    } else {
      break;
    }
  }
  currentIndex.value = idx;
});

const prevLineText = computed(() => {
  if (currentIndex.value > 0 && parsedLyrics.value[currentIndex.value - 1]) {
    return parsedLyrics.value[currentIndex.value - 1].text;
  }
  return '';
});

const currentLineText = computed(() => {
  if (parsedLyrics.value[currentIndex.value]) {
    return parsedLyrics.value[currentIndex.value].text;
  }
  return '伴奏播放中...';
});

const nextLineText = computed(() => {
  if (currentIndex.value < parsedLyrics.value.length - 1 && parsedLyrics.value[currentIndex.value + 1]) {
    return parsedLyrics.value[currentIndex.value + 1].text;
  }
  return '';
});
</script>

<style scoped>
.stream-lyrics-card {
  width: 330px;
  background: rgba(11, 15, 25, 0.82);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(56, 189, 248, 0.28);
  border-radius: 18px;
  padding: 10px 14px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55), inset 0 0 12px rgba(56, 189, 248, 0.08);
  color: #fff;
  user-select: none;
}

.lyrics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 5px;
}
.music-icon { font-size: 12px; }
.lyrics-tag {
  font-size: 11px;
  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 0.5px;
}

.track-hint {
  font-size: 10px;
  color: #94a3b8;
  max-width: 170px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lyrics-viewport {
  height: 68px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.no-lyrics-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.lrc-wave-bars {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 14px;
}
.lrc-wave-bars span {
  width: 2.5px;
  background: #38bdf8;
  border-radius: 1px;
  animation: lrcWave 0.9s ease-in-out infinite alternate;
}
.lb-1 { height: 4px; animation-delay: 0.1s; }
.lb-2 { height: 12px; animation-delay: 0.25s; }
.lb-3 { height: 7px; animation-delay: 0.15s; }
.lb-4 { height: 14px; animation-delay: 0.35s; }
.lb-5 { height: 6px; animation-delay: 0.2s; }

@keyframes lrcWave {
  0% { transform: scaleY(0.3); }
  100% { transform: scaleY(1); }
}

.hint-text {
  font-size: 11px;
  color: #64748b;
  font-style: italic;
}

.lyrics-lines-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  width: 100%;
}

.lyric-line {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  text-align: center;
  transition: all 0.25s ease;
}

.line-prev, .line-next {
  font-size: 10.5px;
  color: #64748b;
  opacity: 0.65;
  height: 16px;
}

.line-current {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13.5px;
  font-weight: 800;
  color: #f8fafc;
  text-shadow: 0 0 10px rgba(56, 189, 248, 0.7);
  height: 22px;
}

.singing-dot {
  font-size: 10px;
  color: #38bdf8;
  animation: starTwinkle 1s infinite alternate;
}

.active-text {
  background: linear-gradient(90deg, #f8fafc 0%, #38bdf8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
