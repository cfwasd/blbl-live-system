<template>
  <div class="hud-panel">
    <div class="hud-title">⚡ AI LIVE HUD 指标</div>

    <!-- Token 消耗与核心指标 -->
    <div class="metric-row">
      <div class="metric-box">
        <span class="label">累计消耗 Token</span>
        <span class="value text-cyan-400">{{ (stats?.total_tokens || 0).toLocaleString() }}</span>
      </div>
      <div class="metric-box">
        <span class="label">弹幕 / 问答总数</span>
        <span class="value">{{ stats?.danmu_count || 0 }} / {{ stats?.ai_reply_count || 0 }}</span>
      </div>
    </div>

    <!-- 活跃观众 Top 5 榜单 -->
    <div class="top-list">
      <div class="top-header">🏆 活跃观众排行</div>
      <div v-for="user in (stats?.top_users || [])" :key="user.rank" class="top-item">
        <span class="rank" :class="'rank-' + user.rank">{{ user.rank }}</span>
        <span class="user-name">{{ user.uname }}</span>
        <span class="user-count">{{ user.count }} 条</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  stats: {
    total_tokens: number;
    danmu_count: number;
    ai_reply_count: number;
    top_users: Array<{ rank: number; uname: string; count: number }>;
  }
}>();
</script>

<style scoped>
.hud-panel {
  width: 260px;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 14px;
  color: #f8fafc;
  font-family: system-ui, sans-serif;
}
.hud-title { font-size: 13px; font-weight: bold; color: #38bdf8; margin-bottom: 8px; }
.metric-row { display: flex; gap: 8px; margin-bottom: 12px; }
.metric-box {
  flex: 1;
  background: rgba(0, 0, 0, 0.3);
  padding: 6px 8px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}
.label { font-size: 10px; color: #94a3b8; }
.value { font-size: 14px; font-weight: bold; }
.text-cyan-400 { color: #22d3ee; }
.top-list { display: flex; flex-direction: column; gap: 4px; }
.top-header { font-size: 11px; color: #cbd5e1; margin-bottom: 2px; }
.top-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.04);
  padding: 3px 8px;
  border-radius: 6px;
}
.rank { font-weight: bold; width: 16px; }
.rank-1 { color: #facc15; }
.rank-2 { color: #cbd5e1; }
.rank-3 { color: #fb923c; }
.user-name { flex: 1; margin: 0 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-count { color: #64748b; font-size: 11px; }
</style>
