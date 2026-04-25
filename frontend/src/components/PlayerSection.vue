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
        :class="{ warning: timerDisplay.warning, danger: timerDisplay.danger, bounce: timerDisplay.countdown }"
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
          <div class="knob"></div></div>
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
        <transition name="choice-fade">
          <span v-if="p.choice === 'left'" class="lb-choice left">L</span>
          <span v-else-if="p.choice === 'right'" class="lb-choice right">R</span>
          <span v-else-if="p.choice === 'watch'" class="lb-choice watch">-</span>
          <span v-else-if="p.confirmed && p.choice === null" class="lb-choice hidden">?</span>
        </transition>
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
  toggleAllInAndResubmit: Function,
  confirmVote: Function,
})

function handleToggleAllIn() {
  // Atomic toggle+resubmit from parent to avoid stale allIn value
  props.toggleAllInAndResubmit?.()
}
</script>

<style scoped>
.all-in-tip { text-align: center; margin-top: 12px; padding: 10px 16px; border-radius: var(--radius-sm); background: var(--orange-bg); border: 1px solid rgba(255,149,0,.25); color: var(--orange); font-size: 14px; font-weight: 600; animation: slideIn .3s ease }
.choices { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 20px }
.choice { position: relative; border-radius: var(--radius); padding: 28px 16px; text-align: center; cursor: pointer; border: 2px solid var(--border); background: var(--bg-card); transition: all .25s; user-select: none; -webkit-user-select: none; overflow: hidden }
.choice:active { transform: scale(.96) }
.choice::after { content: ''; position: absolute; inset: 0; opacity: 0; transition: opacity .3s; pointer-events: none }
.choice-left::after { background: radial-gradient(circle at center,rgba(255,59,48,.12) 0%,transparent 70%) }
.choice-right::after { background: radial-gradient(circle at center,rgba(52,199,89,.12) 0%,transparent 70%) }
.choice-left.selected::after, .choice-left:hover::after { opacity: 1 }
.choice-right.selected::after, .choice-right:hover::after { opacity: 1 }
.choice .choice-icon { font-size: 32px; font-weight: 800; display: block; margin-bottom: 6px; letter-spacing: -1px; position: relative; z-index: 1 }
.choice .choice-label { font-size: 14px; font-weight: 600; color: var(--text2); position: relative; z-index: 1 }
.choice-left .choice-icon { color: var(--red) }
.choice-right .choice-icon { color: var(--green) }
.choice-left:hover, .choice-left.selected { border-color: var(--red); background: var(--red-bg) }
.choice-left.selected .choice-label { color: var(--red) }
.choice-right:hover, .choice-right.selected { border-color: var(--green); background: var(--green-bg) }
.choice-right.selected .choice-label { color: var(--green) }
.choice.disabled { opacity: .4; pointer-events: none }
.choice.all-in-active { border-color: var(--orange) !important; box-shadow: 0 0 0 3px var(--orange-bg); animation: allInGlow 1.5s ease-in-out infinite alternate }
.watch-btn { margin-top: 16px }
.watch-btn .btn { padding: 12px; font-size: 14px; color: var(--text2); background: var(--bg-card); border: 1.5px solid var(--border) }
.watch-btn .btn.selected { background: var(--accent-light); color: var(--accent); border-color: var(--accent) }
.all-in-row { display: flex; align-items: center; justify-content: space-between; margin-top: 16px; padding: 14px 16px; border-radius: var(--radius-sm); background: var(--orange-bg); border: 1px solid rgba(255,149,0,.2); animation: slideIn .3s ease }
.all-in-row .label { font-size: 14px; font-weight: 600; color: var(--orange) }
.all-in-row .desc { font-size: 11px; color: var(--text2); margin-top: 2px }
.toggle { position: relative; width: 51px; height: 31px; border-radius: 16px; background: var(--text3); cursor: pointer; transition: background .2s; flex-shrink: 0 }
.toggle.on { background: var(--orange) }
.toggle .knob { position: absolute; top: 2px; left: 2px; width: 27px; height: 27px; border-radius: 50%; background: #FFF; box-shadow: 0 1px 3px rgba(0,0,0,.15); transition: transform .2s }
.toggle.on .knob { transform: translateX(20px) }
.my-score { margin-top: 24px; padding: 20px; border-radius: var(--radius); background: var(--bg-card); box-shadow: var(--shadow); border: .5px solid var(--border); text-align: center; position: relative; overflow: hidden }
.my-score::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg,var(--red),var(--arknights-gold),var(--green)) }
.my-score .label { font-size: 13px; color: var(--text2); font-weight: 500 }
.my-score .value { font-size: 40px; font-weight: 700; letter-spacing: -1px; margin-top: 2px; transition: all .3s }
.my-score .change { font-size: 14px; font-weight: 600; margin-top: 4px; animation: changePop .4s cubic-bezier(.34,1.56,.64,1) }
.my-score .change.positive { color: var(--green) }
.my-score .change.negative { color: var(--red) }

@media(max-width:380px){
  .choices { gap: 10px }
  .choice { padding: 20px 10px }
  .choice .choice-icon { font-size: 26px }
  .round-stake { font-size: 28px }
  .my-score .value { font-size: 32px }
}
</style>
