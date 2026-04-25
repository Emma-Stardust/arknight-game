<template>
  <template v-if="state.game_active">
    <!-- Round info (when admin panel not showing) -->
    <div class="round-info" v-if="!isAdmin || !showAdmin">
      <div class="round-number">
        第 <strong>{{ state.current_round }}</strong> / {{ state.total_rounds }} 轮
      </div>
      <div v-if="state.round_stake > 0" class="round-stake">
        <span>积分</span>{{ formatScore(state.round_stake) }}
      </div>
      <div
        v-if="state.round_phase === 'voting' && localTimerRemaining > 0"
        class="timer"
        :class="{ warning: timerDisplay.warning, danger: timerDisplay.danger }"
      >
        {{ timerDisplay.text }}
      </div>
    </div>

    <!-- R6+ ALL IN tip -->
    <div
      v-if="state.round_phase === 'voting' && state.current_round >= 6"
      class="all-in-tip"
    >
      第6轮起允许全力支持！投入所有的点数ALL吧！
    </div>

    <!-- Voting -->
    <template v-if="state.round_phase === 'voting'">
      <div class="choices">
        <div
          class="choice choice-left"
          :class="{
            selected: myChoice === 'left',
            disabled: myEliminated || myConfirmed,
            'all-in-active': allIn && myChoice === 'left',
          }"
          @click="vote('left')"
        >
          <span class="choice-icon">&#9664;</span><span class="choice-label">LEFT</span>
        </div>
        <div
          class="choice choice-right"
          :class="{
            selected: myChoice === 'right',
            disabled: myEliminated || myConfirmed,
            'all-in-active': allIn && myChoice === 'right',
          }"
          @click="vote('right')"
        >
          <span class="choice-icon">&#9654;</span><span class="choice-label">RIGHT</span>
        </div>
      </div>
      <div class="watch-btn">
        <button
          class="btn"
          :class="{ selected: myChoice === 'watch' }"
          @click="vote('watch')"
          :disabled="myEliminated || myConfirmed"
        >
          {{ myChoice === 'watch' ? '已选择观望' : '观望' }}
        </button>
      </div>
      <!-- Forced ALL IN -->
      <div
        v-if="forcedAllIn && myChoice && myChoice !== 'watch'"
        class="all-in-row"
        style="border-color: rgba(255, 149, 0, 0.4)"
      >
        <div>
          <div class="label">ALL IN (强制)</div>
          <div class="desc">积分不足，投入全部，胜利翻倍，失败淘汰</div>
        </div>
        <div class="toggle on" style="cursor: default"><div class="knob"></div></div>
      </div>
      <!-- Voluntary ALL IN -->
      <div
        v-else-if="canVoluntaryAllIn && myChoice && myChoice !== 'watch' && !myConfirmed"
        class="all-in-row"
      >
        <div>
          <div class="label">ALL IN</div>
          <div class="desc">投入全部，胜利翻倍，失败淘汰</div>
        </div>
        <div class="toggle" :class="{ on: allIn }" @click="handleToggleAllIn">
          <div class="knob"></div>
        </div>
      </div>
      <!-- Confirm -->
      <div style="margin-top: 20px" v-if="myChoice && !myConfirmed && !myEliminated">
        <button
          class="btn btn-primary"
          @click="confirmVote"
          style="font-size: 17px; padding: 16px"
        >
          确定！
        </button>
      </div>
      <div
        v-if="myConfirmed"
        style="
          margin-top: 16px;
          text-align: center;
          padding: 14px;
          border-radius: var(--radius-sm);
          background: var(--green-bg);
          border: 1px solid var(--green-border);
          color: var(--green);
          font-size: 14px;
          font-weight: 600;
        "
      >
        已确认选择，无法更改
      </div>
    </template>

    <!-- Revealed -->
    <template v-if="state.round_phase === 'revealed'">
      <div class="card mt-24">
        <div class="card-header">本轮答案</div>
        <div style="font-size: 24px; font-weight: 700">
          <span
            :style="{
              color: state.correct_answer === 'left' ? 'var(--red)' : 'var(--green)',
            }"
          >
            {{ state.correct_answer === 'left' ? 'LEFT' : 'RIGHT' }}
          </span>
        </div>
      </div>
      <div class="card mt-16" v-if="lastRoundResult">
        <div class="card-header">结算结果</div>
        <div
          v-for="(r, i) in lastRoundResult"
          :key="r.uid"
          class="result-item"
          :style="{ 'animation-delay': i * 50 + 'ms' }"
        >
          <div class="result-icon" :class="r.result">
            {{
              r.result === 'win'
                ? '+'
                : r.result === 'eliminated'
                  ? '!'
                  : r.result === 'lose'
                    ? '-'
                    : '~'
            }}
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
    </template>

    <!-- My Score -->
    <div class="my-score">
      <div class="label">{{ myEliminated ? '已淘汰' : '我的积分' }}</div>
      <div class="value" :style="{ opacity: myEliminated ? 0.4 : 1 }">
        {{ formatScore(myScore) }}
      </div>
      <div
        v-if="myLastChange !== 0 && state.round_phase === 'revealed'"
        class="change"
        :class="myLastChange > 0 ? 'positive' : 'negative'"
      >
        {{ myLastChange > 0 ? '+' : '' }}{{ formatScore(Math.abs(myLastChange)) }}
      </div>
    </div>

    <!-- Leaderboard -->
    <div class="card" style="margin-top: 24px" v-if="sortedPlayers.length">
      <div class="card-header">排行榜</div>
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
        <span v-if="p.all_in" class="lb-tag allin">ALL IN</span>
        <span v-if="p.confirmed" class="lb-tag confirmed">OK</span>
        <div class="lb-score" :class="{ eliminated: p.eliminated }">
          {{ formatScore(p.score) }}
        </div>
      </div>
    </div>
  </template>

  <!-- Not started -->
  <div v-if="!state.game_active && state.round_phase !== 'finished'" class="empty-state">
    <div class="icon">&#9711;</div>
    <div class="title">等待游戏开始</div>
    <div class="desc">管理员尚未开始游戏</div>
    <div style="margin-top: 12px; font-size: 13px; color: var(--text3)">
      你的ID: {{ userId }}
    </div>
  </div>
</template>

<script setup>
import { nextTick } from 'vue'

defineProps({
  state: Object,
  isAdmin: Boolean,
  showAdmin: Boolean,
  userId: String,
  localTimerRemaining: Number,
  timerDisplay: Object,
  myScore: Number,
  myChoice: String,
  myEliminated: Boolean,
  myConfirmed: Boolean,
  forcedAllIn: Boolean,
  canVoluntaryAllIn: Boolean,
  allIn: Boolean,
  sortedPlayers: Array,
  lastRoundResult: { type: [Array, null], default: null },
  myLastChange: Number,
  formatScore: Function,
  vote: Function,
  submitVote: Function,
  toggleAllInAndResubmit: Function,
  confirmVote: Function,
})

const emit = defineEmits(['update:allIn', 'toggleAllIn'])

function handleToggleAllIn() {
  // Use the atomic toggle+resubmit from parent to avoid stale allIn value
  if (props.toggleAllInAndResubmit) {
    props.toggleAllInAndResubmit()
  } else {
    emit('toggleAllIn')
  }
}
</script>
