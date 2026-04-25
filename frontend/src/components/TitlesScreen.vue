<template>
  <div class="titles-screen">
    <div class="titles-emblem"><span>AK</span></div>
    <div class="titles-heading">游戏结束</div>
    <div class="titles-sub">最终结算</div>

    <!-- My titles -->
    <div v-if="myTitles.length" class="my-titles">
      <div class="my-titles-label">你的称号</div>
      <div class="my-titles-list">
        <div v-for="(t, i) in myTitles" :key="i" class="title-badge" :style="{ 'animation-delay': i * 150 + 'ms' }">
          {{ t }}
        </div>
      </div>
    </div>

    <!-- Final ranking -->
    <div class="card" style="margin-top: 24px" v-if="sortedPlayers.length">
      <div class="card-header">最终排行榜</div>
      <div
        v-for="(p, i) in sortedPlayers"
        :key="p.uid"
        class="lb-item"
        :style="{ 'animation-delay': i * 60 + 'ms' }"
      >
        <div class="lb-rank" :class="{ top: i < 3 }">{{ i + 1 }}</div>
        <div class="lb-name" :class="{ eliminated: p.eliminated }">
          {{ p.name }}<span class="lb-uid">@{{ p.uid }}</span>
        </div>
        <div class="lb-score" :class="{ eliminated: p.eliminated }">
          {{ formatScore(p.score) }}
        </div>
      </div>
    </div>

    <!-- All players' titles -->
    <div v-if="allTitles.length" class="card" style="margin-top: 16px">
      <div class="card-header">称号一览</div>
      <div
        v-for="entry in allTitles"
        :key="entry.uid"
        class="player-titles-row"
      >
        <div class="player-titles-name">{{ entry.name }}</div>
        <div class="player-titles-list">
          <span v-for="(t, i) in entry.titles" :key="i" class="title-badge-sm">{{ t }}</span>
          <span v-if="!entry.titles.length" class="title-badge-sm empty">--</span>
        </div>
      </div>
    </div>

    <div style="margin-top: 24px; text-align: center">
      <div style="font-size: 13px; color: var(--text3)">你的ID: {{ userId }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  state: Object,
  userId: String,
  myTitles: Array,
  sortedPlayers: Array,
  formatScore: Function,
})

const allTitles = computed(() => {
  if (!props.state.titles) return []
  return Object.entries(props.state.titles)
    .map(([uid, titles]) => {
      const player = props.state.players[uid]
      return {
        uid,
        name: player ? player.name : uid,
        titles: titles || [],
      }
    })
    .sort((a, b) => {
      const pa = props.state.players[a.uid]
      const pb = props.state.players[b.uid]
      return (pb ? pb.score : 0) - (pa ? pa.score : 0)
    })
})
</script>

<style scoped>
.titles-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px 20px;
  text-align: center;
}
.titles-emblem {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  box-shadow: 0 4px 20px rgba(212, 168, 67, 0.2);
  animation: emblemPulse 3s ease-in-out infinite;
}
.titles-emblem span {
  font-size: 32px;
  color: #d4a843;
  font-weight: 800;
}
.titles-heading {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.3px;
  margin-bottom: 2px;
}
.titles-sub {
  font-size: 16px;
  font-weight: 500;
  color: var(--arknights-gold);
  margin-bottom: 24px;
}
.my-titles {
  margin-top: 8px;
  margin-bottom: 8px;
}
.my-titles-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}
.my-titles-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}
.title-badge {
  padding: 8px 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--accent-light), rgba(212, 168, 67, 0.15));
  border: 1px solid var(--arknights-gold);
  color: var(--arknights-gold);
  font-size: 15px;
  font-weight: 700;
  animation: titleAppear 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) backwards;
}
@keyframes titleAppear {
  from {
    opacity: 0;
    transform: scale(0.7) translateY(8px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
.player-titles-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 0.5px solid var(--divider);
}
.player-titles-row:last-child {
  border-bottom: none;
}
.player-titles-name {
  flex-shrink: 0;
  font-size: 14px;
  font-weight: 500;
  min-width: 60px;
  text-align: left;
}
.player-titles-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.title-badge-sm {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--accent-light);
  color: var(--accent);
  border: 0.5px solid var(--border);
}
.title-badge-sm.empty {
  color: var(--text3);
  background: transparent;
  border: none;
}
</style>
