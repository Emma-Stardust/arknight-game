<template>
  <div v-if="isAdmin && showAdmin">
    <!-- Game not started -->
    <div v-if="!state.game_active" class="admin-section">
      <div class="card">
        <div class="card-header">管理面板</div>
        <button class="btn btn-primary" @click="sendAction('start_game')">开始新游戏！</button>
      </div>
    </div>

    <!-- Game active -->
    <template v-else>
      <div class="round-info" style="padding-top: 8px">
        <div class="round-number">
          第 <strong>{{ state.current_round }}</strong> / {{ state.total_rounds }} 轮
        </div>
        <div class="round-stake-mini">积分 {{ formatScore(state.round_stake) }}</div>
        <div
          v-if="state.round_phase === 'voting' && localTimerRemaining > 0"
          class="timer"
          :class="{ warning: timerDisplay.warning, danger: timerDisplay.danger }"
        >
          {{ timerDisplay.text }}
        </div>
      </div>

      <!-- Voting: set answer -->
      <div v-if="state.round_phase === 'voting'" class="admin-section">
        <div class="card">
          <div class="card-header">选择正确答案</div>
          <div class="admin-votes">
            已确认 <strong>{{ state.voted_count }}</strong> / {{ state.active_count }}
          </div>
          <div
            v-if="!state.all_confirmed && !state.timer_expired"
            style="text-align: center; margin-top: 8px; font-size: 12px; color: var(--orange)"
          >
            等待所有玩家确认...
          </div>
          <div class="answer-btns">
            <div
              class="answer-btn left-ans"
              :class="{ chosen: pendingAnswer === 'left' }"
              @click="$emit('update:pendingAnswer', 'left')"
            >
              LEFT
            </div>
            <div
              class="answer-btn right-ans"
              :class="{ chosen: pendingAnswer === 'right' }"
              @click="$emit('update:pendingAnswer', 'right')"
            >
              RIGHT
            </div>
          </div>
          <button
            class="btn btn-primary mt-12"
            @click="confirmAnswer"
            :disabled="!pendingAnswer"
          >
            确认答案！
          </button>
          <div
            v-if="!state.all_confirmed && !state.timer_expired && pendingAnswer"
            style="margin-top: 8px"
          >
            <button class="btn btn-danger btn-sm" @click="forceConfirmAnswer">
              仍要公布答案！
            </button>
          </div>
          <div style="margin-top: 10px; display: flex; gap: 8px">
            <button
              class="btn btn-secondary btn-sm"
              style="flex: 1"
              @click="sendReminder('别人都选完了，就差你了！')"
              :disabled="state.all_confirmed"
            >
              催一下！
            </button>
            <button
              class="btn btn-danger btn-sm"
              style="flex: 1"
              @click="sendReminder('再等几年也行...不着急...真的...')"
              :disabled="state.all_confirmed"
            >
              狠狠催！
            </button>
          </div>
        </div>
      </div>

      <!-- Revealed -->
      <div v-if="state.round_phase === 'revealed'" class="admin-section">
        <div class="card">
          <div class="card-header">本轮结算完成</div>
          <div v-if="lastRoundResult" style="margin-top: 8px">
            <div
              v-for="(r, i) in lastRoundResult"
              :key="r.uid"
              class="result-item"
              :style="{ 'animation-delay': i * 50 + 'ms' }"
            >
              <div class="result-icon" :class="r.result">
                {{ r.result === 'win' ? '+' : r.result === 'eliminated' ? '!' : r.result === 'lose' ? '-' : '~' }}
              </div>
              <div class="result-name">{{ r.name }}</div>
              <div
                class="result-change"
                :class="r.change > 0 ? 'pos' : r.change < 0 ? 'neg' : ''"
              >
                {{ r.change > 0 ? '+' : '' }}{{ formatScore(Math.abs(r.change)) }}
              </div>
              <span v-if="r.all_in" class="result-tag">ALL IN</span>
            </div>
          </div>
          <div class="admin-action-row mt-16">
            <button
              class="btn btn-danger btn-sm"
              @click="sendAction('rollback')"
              :disabled="!state.can_rollback"
            >
              回滚！
            </button>
            <button
              class="btn btn-primary btn-sm"
              @click="sendAction('next_round')"
              v-if="state.current_round < state.total_rounds"
            >
              下一轮！
            </button>
            <button class="btn btn-secondary btn-sm" @click="sendAction('end_game')">
              结束！
            </button>
          </div>
        </div>
      </div>

      <!-- Admin Player List -->
      <div class="card admin-section">
        <div class="card-header">
          玩家列表 ({{ state.active_count }} /
          {{ Object.keys(state.players).length }})
        </div>
        <div
          v-for="(p, i) in sortedPlayers"
          :key="p.uid"
          class="lb-item"
          :style="{ 'animation-delay': i * 40 + 'ms' }"
        >
          <div class="lb-rank" :class="{ top: i < 3 }">{{ i + 1 }}</div>
          <div class="lb-name" :class="{ eliminated: p.eliminated }">
            {{ p.name }}<span class="lb-uid">@{{ p.uid }}</span>
          </div>
          <span v-if="p.choice === 'left'" class="lb-choice left">L</span>
          <span v-else-if="p.choice === 'right'" class="lb-choice right">R</span>
          <span v-else-if="p.choice === 'watch'" class="lb-choice watch">-</span>
          <span v-else-if="state.round_phase === 'voting'" class="lb-choice watch">?</span>
          <span v-if="p.all_in" class="lb-tag allin">ALL IN</span>
          <span v-if="p.confirmed" class="lb-tag confirmed">OK</span>
          <div class="lb-score" :class="{ eliminated: p.eliminated }">
            {{ formatScore(p.score) }}
          </div>
        </div>
      </div>

      <!-- History -->
      <div class="card admin-section" v-if="state.history.length">
        <div class="card-header">历史记录</div>
        <div v-for="h in [...state.history].reverse()" :key="h.round" class="history-item">
          <div class="history-round">
            第 {{ h.round }} 轮 / 积分 {{ formatScore(h.stake) }}
          </div>
          <div class="history-answer" :class="h.answer">
            {{ h.answer === 'left' ? 'LEFT' : 'RIGHT' }}
          </div>
        </div>
      </div>

      <div class="admin-section">
        <button class="btn btn-danger" @click="sendAction('end_game')">结束游戏！</button>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  isAdmin: Boolean,
  showAdmin: Boolean,
  state: Object,
  localTimerRemaining: Number,
  timerDisplay: Object,
  pendingAnswer: { type: [String, null], default: null },
  sortedPlayers: Array,
  lastRoundResult: { type: [Array, null], default: null },
  formatScore: Function,
  sendAction: Function,
  confirmAnswer: Function,
  forceConfirmAnswer: Function,
  sendReminder: Function,
})

defineEmits(['update:pendingAnswer'])
</script>

<style scoped>
.admin-section { margin-bottom: 16px }
.admin-section .card { padding: 16px }
.admin-votes { font-size: 14px; color: var(--text2); text-align: center; margin-top: 8px }
.admin-votes strong { color: var(--accent) }
.answer-btns { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px }
.answer-btn { padding: 14px; border-radius: var(--radius-sm); border: 2px solid var(--border); background: var(--bg-card); font-size: 16px; font-weight: 700; cursor: pointer; transition: all .2s; text-align: center }
.answer-btn:active { transform: scale(.96) }
.answer-btn.left-ans:hover, .answer-btn.left-ans.chosen { border-color: var(--red); background: var(--red-bg); color: var(--red) }
.answer-btn.right-ans:hover, .answer-btn.right-ans.chosen { border-color: var(--green); background: var(--green-bg); color: var(--green) }
.admin-action-row { display: flex; gap: 8px; margin-top: 10px }
.admin-action-row .btn { flex: 1 }
.history-item { padding: 10px 0; border-bottom: .5px solid var(--divider) }
.history-item:last-child { border-bottom: none }
.history-round { font-size: 13px; font-weight: 600; color: var(--text2) }
.history-answer { font-size: 14px; font-weight: 600; margin-top: 2px }
.history-answer.left { color: var(--red) }
.history-answer.right { color: var(--green) }
</style>
