<script setup>
import { ref } from 'vue'

const props = defineProps({
  state: Object,
  timerDisplay: Object,
  localTimerRemaining: Number,
  sortedPlayers: Array,
  lastRoundResult: Array,
  pendingAnswer: String,
})

const emit = defineEmits(['action', 'set-stake', 'confirm-answer', 'force-confirm', 'send-reminder'])

const stakeInput = ref(null)
const pendingAnswer = ref(null)

function setStake() {
  if (!stakeInput.value || stakeInput.value <= 0) return
  emit('set-stake', stakeInput.value)
  stakeInput.value = null
}

function confirmAnswer() {
  if (!pendingAnswer.value) return
  emit('confirm-answer', pendingAnswer.value)
  pendingAnswer.value = null
}

function forceConfirm() {
  if (!pendingAnswer.value) return
  if (confirm('还有玩家未确认选择！未选择者将按观望处理。确定要公布答案吗？')) {
    emit('force-confirm', pendingAnswer.value)
    pendingAnswer.value = null
  }
}
</script>

<template>
  <!-- Game Not Active -->
  <div v-if="!state.game_active" class="admin-section">
    <div class="card">
      <div class="card-header">管理面板</div>
      <button class="btn btn-primary" @click="emit('action', 'start_game')">开始新游戏！</button>
    </div>
  </div>

  <!-- Game Active -->
  <template v-else>
    <div class="round-info" style="padding-top:8px">
      <div class="round-number">第 <strong>{{ state.current_round }}</strong> / {{ state.total_rounds }} 轮</div>
      <div v-if="state.round_phase === 'voting' && localTimerRemaining > 0" class="timer" :class="{warning:timerDisplay.warning,danger:timerDisplay.danger}">{{ timerDisplay.text }}</div>
    </div>

    <!-- Waiting: set stake -->
    <div v-if="state.round_phase === 'waiting'" class="admin-section">
      <div class="card">
        <div class="card-header">设定本轮积分</div>
        <div class="stake-row">
          <input v-model.number="stakeInput" type="number" placeholder="输入积分" min="1" @keyup.enter="setStake">
          <button class="stake-confirm" @click="setStake" :disabled="!stakeInput || stakeInput <= 0">确认！</button>
        </div>
      </div>
    </div>

    <!-- Voting: set answer -->
    <div v-if="state.round_phase === 'voting'" class="admin-section">
      <div class="card">
        <div class="card-header">选择正确答案</div>
        <div class="admin-votes">已确认 <strong>{{ state.voted_count }}</strong> / {{ state.active_count }}</div>
        <div v-if="!state.all_confirmed && !state.timer_expired" style="text-align:center;margin-top:8px;font-size:12px;color:var(--orange)">等待所有玩家确认...</div>
        <div class="answer-btns">
          <div class="answer-btn left-ans" :class="{chosen:pendingAnswer==='left'}" @click="pendingAnswer='left'">LEFT</div>
          <div class="answer-btn right-ans" :class="{chosen:pendingAnswer==='right'}" @click="pendingAnswer='right'">RIGHT</div>
        </div>
        <button class="btn btn-primary mt-12" @click="confirmAnswer" :disabled="!pendingAnswer">确认答案！</button>
        <div v-if="!state.all_confirmed && !state.timer_expired && pendingAnswer" style="margin-top:8px">
          <button class="btn btn-danger btn-sm" @click="forceConfirm">仍要公布答案！</button>
        </div>
        <div style="margin-top:10px;display:flex;gap:8px">
          <button class="btn btn-secondary btn-sm" style="flex:1" @click="emit('send-reminder','别人都选完了，就差你了！')" :disabled="state.all_confirmed">催一下！</button>
          <button class="btn btn-danger btn-sm" style="flex:1" @click="emit('send-reminder','再等几年也行...不着急...真的...')" :disabled="state.all_confirmed">狠狠催！</button>
        </div>
      </div>
    </div>

    <!-- Revealed -->
    <div v-if="state.round_phase === 'revealed'" class="admin-section">
      <div class="card">
        <div class="card-header">本轮结算完成</div>
        <div v-if="lastRoundResult" style="margin-top:8px">
          <div v-for="(r,i) in lastRoundResult" :key="r.uid" class="result-item" :style="{'animation-delay':(i*50)+'ms'}">
            <div class="result-icon" :class="r.result">{{ r.result === 'win' ? '+' : r.result === 'eliminated' ? '!' : r.result === 'lose' ? '-' : '~' }}</div>
            <div class="result-name">{{ r.name }}</div>
            <div class="result-change" :class="r.change > 0 ? 'pos' : r.change < 0 ? 'neg' : ''">{{ r.change > 0 ? '+' : '' }}{{ r.change }}</div>
            <span v-if="r.all_in" class="result-tag">ALL IN</span>
          </div>
        </div>
        <div class="admin-action-row mt-16">
          <button class="btn btn-danger btn-sm" @click="emit('action','rollback')" :disabled="!state.can_rollback">回滚！</button>
          <button class="btn btn-primary btn-sm" @click="emit('action','next_round')" v-if="state.current_round < state.total_rounds">下一轮！</button>
          <button class="btn btn-secondary btn-sm" @click="emit('action','end_game')">结束！</button>
        </div>
      </div>
    </div>

    <!-- Player List -->
    <div class="card admin-section">
      <div class="card-header">玩家列表 ({{ state.active_count }} / {{ Object.keys(state.players).length }})</div>
      <div v-for="(p,i) in sortedPlayers" :key="p.uid" class="lb-item" :style="{'animation-delay':(i*40)+'ms'}">
        <div class="lb-rank" :class="{top:i<3}">{{ i+1 }}</div>
        <div class="lb-name" :class="{eliminated:p.eliminated}">{{ p.name }}<span class="lb-uid">@{{ p.uid }}</span></div>
        <span v-if="p.choice==='left'" class="lb-choice left">L</span>
        <span v-else-if="p.choice==='right'" class="lb-choice right">R</span>
        <span v-else-if="p.choice==='watch'" class="lb-choice watch">-</span>
        <span v-else-if="state.round_phase==='voting'" class="lb-choice watch">?</span>
        <span v-if="p.all_in" class="lb-tag allin">ALL IN</span>
        <span v-if="p.confirmed" class="lb-tag confirmed">OK</span>
        <div class="lb-score" :class="{eliminated:p.eliminated}">{{ p.score }}</div>
      </div>
    </div>

    <!-- History -->
    <div class="card admin-section" v-if="state.history.length">
      <div class="card-header">历史记录</div>
      <div v-for="h in [...state.history].reverse()" :key="h.round" class="history-item">
        <div class="history-round">第 {{ h.round }} 轮 / 积分 {{ h.stake }}</div>
        <div class="history-answer" :class="h.answer">{{ h.answer === 'left' ? 'LEFT' : 'RIGHT' }}</div>
      </div>
    </div>

    <div class="admin-section">
      <button class="btn btn-danger" @click="emit('action','end_game')">结束游戏！</button>
    </div>
  </template>
</template>
