<template>
  <div class="stream-marquee-bar">
    <div class="marquee-tag">
      <span class="live-mic">📢</span>
      <span class="tag-text">直播公告</span>
    </div>

    <div class="marquee-track">
      <div class="marquee-content">
        <span class="notice-item">{{ text || defaultText }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  text?: string;
}>(), {
  text: ''
});

const defaultText = '✨ 欢迎来到 Gemini 娘的赛博电竞演播室！✦ 🎵 发送【点歌 歌名】在线点播网易云高质音乐 ✦ 🔀 发送【切歌】或【下一首】随时换伴奏 ✦ 💬 弹幕畅聊主播语音回答 ✦ 💎 投喂 SC 享专属置顶与优先答谢！';
</script>

<style scoped>
.stream-marquee-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(11, 15, 25, 0.82);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 30px;
  padding: 5px 14px 5px 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
  max-width: 620px;
  overflow: hidden;
  user-select: none;
}

.marquee-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(56, 189, 248, 0.15);
  padding: 2px 8px;
  border-radius: 20px;
  border: 1px solid rgba(56, 189, 248, 0.35);
  flex-shrink: 0;
}
.live-mic { font-size: 11px; }
.tag-text {
  font-size: 10px;
  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 0.5px;
}

.marquee-track {
  flex: 1;
  overflow: hidden;
  white-space: nowrap;
}

.marquee-content {
  display: inline-block;
  animation: marqueeScroll 26s linear infinite;
  font-size: 11.5px;
  font-weight: 600;
  color: #e2e8f0;
}

.notice-item {
  margin: 0 4px;
  letter-spacing: 0.5px;
}

@keyframes marqueeScroll {
  0% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}
</style>
