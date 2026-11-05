<template>
  <div class="command-guide-card">
    <div class="guide-header">
      <div class="guide-title-wrap">
        <span class="guide-icon">🎮</span>
        <span class="guide-title">直播互动玩法指南</span>
      </div>
      <span class="guide-chip">COMMANDS</span>
    </div>

    <div class="commands-list">
      <div v-for="(item, idx) in activeItems" :key="idx" class="cmd-item">
        <span class="cmd-tag" :class="'cmd-' + (item.type || (idx === 1 ? 'music' : idx === 2 ? 'switch' : idx === 3 ? 'sc' : 'chat'))">
          {{ item.tag }}
        </span>
        <span class="cmd-desc">{{ item.desc }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

export interface GuideItem {
  tag: string;
  desc: string;
  type?: string;
}

const props = withDefaults(defineProps<{
  items?: GuideItem[];
}>(), {
  items: () => []
});

const defaultItems: GuideItem[] = [
  { tag: '💬 弹幕聊天', desc: '发送任意弹幕即刻触发 AI 思考与语音回答', type: 'chat' },
  { tag: '🎵 在线点歌', desc: '发送【点歌 歌名】即播网易云高质音乐', type: 'music' },
  { tag: '🔀 快速切歌', desc: '发送【切歌】或【下一首】切换在线伴奏', type: 'switch' },
  { tag: '💎 醒目留言', desc: '投喂 SC 解锁专属置顶打赏卡与优先语音答谢', type: 'sc' }
];

const activeItems = computed(() => {
  return props.items && props.items.length > 0 ? props.items : defaultItems;
});
</script>

<style scoped>
.command-guide-card {
  width: 330px;
  background: rgba(11, 15, 25, 0.82);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(192, 132, 252, 0.3);
  border-radius: 18px;
  padding: 12px 14px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55), inset 0 0 12px rgba(192, 132, 252, 0.08);
  color: #fff;
  user-select: none;
}

.guide-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.guide-title-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}
.guide-icon { font-size: 13px; }
.guide-title {
  font-size: 11px;
  font-weight: 800;
  color: #f1f5f9;
  letter-spacing: 0.5px;
}
.guide-chip {
  font-size: 9px;
  font-weight: 800;
  color: #c084fc;
  background: rgba(192, 132, 252, 0.15);
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid rgba(192, 132, 252, 0.3);
}

.commands-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cmd-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
}

.cmd-tag {
  font-size: 10px;
  font-weight: 700;
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  padding: 1.5px 6px;
  border-radius: 6px;
  border: 1px solid rgba(56, 189, 248, 0.25);
  white-space: nowrap;
}
.cmd-chat {
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  border-color: rgba(56, 189, 248, 0.3);
}
.cmd-music {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border-color: rgba(16, 185, 129, 0.3);
}
.cmd-switch {
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
  border-color: rgba(168, 85, 247, 0.3);
}
.cmd-sc {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border-color: rgba(245, 158, 11, 0.3);
}

.cmd-desc {
  color: #cbd5e1;
  font-size: 10.5px;
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
