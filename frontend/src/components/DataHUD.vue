<template>
  <div class="hud-panel">
    <!-- 顶部标题与在线脉冲 -->
    <div class="hud-header">
      <div class="hud-title-wrap">
        <span class="hud-icon">⚡</span>
        <span class="hud-title">AI LIVE METRICS</span>
      </div>
      <div class="hud-live-badge">
        <span class="pulse-dot"></span>
        LIVE HUD
      </div>
    </div>

    <!-- 核心指标网格 -->
    <div class="metric-grid">
      <!-- 累计消耗 Token -->
      <div class="metric-card token-card">
        <div class="metric-top">
          <span class="metric-label">累计消耗 TOKEN</span>
          <span class="chip-badge">AI</span>
        </div>
        <div class="token-value">{{ (stats?.total_tokens || 0).toLocaleString() }}</div>
        <div class="token-bar-bg">
          <div class="token-bar-fill" :style="{ width: Math.min(100, ((stats?.total_tokens || 0) % 50000) / 500) + '%' }"></div>
        </div>
      </div>

      <!-- 弹幕与问答总计 -->
      <div class="metric-card danmu-card">
        <div class="metric-top">
          <span class="metric-label">弹幕 / AI 互动</span>
          <span class="metric-count-icon">💬</span>
        </div>
        <div class="stat-counts">
          <span class="main-count">{{ stats?.danmu_count || 0 }}</span>
          <span class="divider">/</span>
          <span class="sub-count">{{ stats?.ai_reply_count || 0 }} 答</span>
        </div>
        <div class="block-info">已过滤风控: {{ stats?.blocked_count || 0 }} 条</div>
      </div>
    </div>

    <!-- 活跃观众 Top 5 榜单 -->
    <div class="top-section">
      <div class="top-section-header">
        <span class="top-title">🏆 活跃粉丝榜 TOP 5</span>
        <span class="top-subtitle">实时热度</span>
      </div>
      <div class="top-list">
        <div v-if="(!stats?.top_users || stats.top_users.length === 0)" class="empty-top">
          暂无观众上榜，发送弹幕即可登顶~
        </div>
        <div v-for="user in (stats?.top_users || [])" :key="user.rank" class="top-row" :class="'rank-row-' + user.rank">
          <div class="rank-badge" :class="'badge-' + user.rank">
            {{ user.rank === 1 ? '🥇' : (user.rank === 2 ? '🥈' : (user.rank === 3 ? '🥉' : user.rank)) }}
          </div>
          <div class="user-name" :title="user.uname">{{ user.uname }}</div>
          <div class="user-score">{{ user.count }} <span class="unit">条</span></div>
        </div>
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
    blocked_count?: number;
    top_users: Array<{ rank: number; uname: string; count: number }>;
  }
}>();
</script>

<style scoped>
.hud-panel {
  width: 290px;
  background: rgba(11, 15, 25, 0.78);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 20px;
  padding: 16px;
  color: #f8fafc;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5), inset 0 0 15px rgba(56, 189, 248, 0.08);
  font-family: system-ui, -apple-system, sans-serif;
  user-select: none;
}
.hud-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.hud-title-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}
.hud-icon { font-size: 14px; }
.hud-title {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 1px;
  background: linear-gradient(90deg, #38bdf8, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hud-live-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 800;
  color: #22d3ee;
  background: rgba(34, 211, 238, 0.12);
  padding: 2px 8px;
  border-radius: 12px;
  border: 1px solid rgba(34, 211, 238, 0.3);
}
.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22d3ee;
  box-shadow: 0 0 8px #22d3ee;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}

.metric-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 14px;
}
.metric-card {
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 12px;
  padding: 10px 12px;
}
.metric-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.metric-label {
  font-size: 10px;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.5px;
}
.chip-badge {
  font-size: 9px;
  font-weight: 800;
  background: #0284c7;
  color: #fff;
  padding: 1px 5px;
  border-radius: 4px;
}
.token-value {
  font-family: monospace;
  font-size: 20px;
  font-weight: 900;
  color: #38bdf8;
  text-shadow: 0 0 12px rgba(56, 189, 248, 0.5);
  line-height: 1.2;
  margin-bottom: 6px;
}
.token-bar-bg {
  width: 100%;
  height: 3px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}
.token-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #38bdf8, #c084fc);
  box-shadow: 0 0 6px #38bdf8;
}

.stat-counts {
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.main-count {
  font-size: 16px;
  font-weight: 800;
  color: #f1f5f9;
}
.divider { color: #64748b; }
.sub-count {
  font-size: 12px;
  color: #a855f7;
  font-weight: 600;
}
.block-info {
  font-size: 10px;
  color: #64748b;
  margin-top: 2px;
}

.top-section {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 14px;
  padding: 10px 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}
.top-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.top-title {
  font-size: 11px;
  font-weight: 800;
  color: #e2e8f0;
}
.top-subtitle {
  font-size: 10px;
  color: #64748b;
}
.top-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.empty-top {
  font-size: 11px;
  color: #64748b;
  text-align: center;
  padding: 8px 0;
}
.top-row {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  font-size: 12px;
}
.rank-row-1 { background: rgba(234, 179, 8, 0.08); border-left: 2px solid #eab308; }
.rank-row-2 { background: rgba(203, 213, 225, 0.06); border-left: 2px solid #cbd5e1; }
.rank-row-3 { background: rgba(251, 146, 60, 0.06); border-left: 2px solid #fb923c; }
.rank-badge {
  width: 20px;
  font-weight: 800;
  font-size: 12px;
  text-align: center;
}
.badge-4, .badge-5 { color: #64748b; font-size: 11px; }
.user-name {
  flex: 1;
  margin: 0 8px;
  font-weight: 600;
  color: #cbd5e1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.user-score {
  font-family: monospace;
  font-size: 11px;
  color: #38bdf8;
  font-weight: 700;
}
.unit { font-size: 9px; color: #64748b; }
</style>
