<template>
  <div class="bg-pattern"></div>
  <div class="particle"></div>
  <div class="particle"></div>
  <div class="particle"></div>
  <div class="particle"></div>
  <div class="particle"></div>
  <div class="particle"></div>

  <div class="app-root">
    <div v-if="reconnecting" class="reconnect-banner">连接断开，正在重连...</div>
    <div v-if="reminderBanner" class="reminder-banner" @click="reminderBanner = ''">
      {{ reminderBanner }}
    </div>
    <div v-if="toast" class="toast">{{ toast }}</div>

    <!-- Join Screen -->
    <JoinScreen
      v-if="!joined"
      :join-game="joinGame"
      v-model:admin-password="adminPassword"
    />

    <!-- Main View -->
    <template v-else>
      <div class="top-bar">
        <h1>斗蛐蛐 计分板</h1>
        <div class="top-bar-right">
          <span class="badge" :class="phaseBadge">{{ phaseLabel }}</span>
          <button
            v-if="isAdmin"
            class="icon-btn icon-btn-admin active"
            @click="showAdmin = !showAdmin"
            title="管理面板"
          >
            &#9881;
          </button>
          <button
            v-else
            class="icon-btn icon-btn-admin"
            @click="unlockAdmin"
            title="解锁管理"
          >
            &#9881;
          </button>
          <button class="icon-btn icon-btn-theme" @click="toggleTheme">
            {{ isDark ? '&#9728;' : '&#9790;' }}
          </button>
        </div>
      </div>

      <div class="page">
        <!-- Finished: Titles Screen -->
        <TitlesScreen
          v-if="state.round_phase === 'finished'"
          :state="state"
          :user-id="userId"
          :my-titles="myTitles"
          :sorted-players="sortedPlayers"
          :format-score="formatScore"
        />

        <!-- Admin Panel -->
        <AdminPanel
          v-if="state.round_phase !== 'finished'"
          :is-admin="isAdmin"
          :show-admin="showAdmin"
          :state="state"
          :local-timer-remaining="localTimerRemaining"
          :timer-display="timerDisplay"
          v-model:pending-answer="pendingAnswer"
          :sorted-players="sortedPlayers"
          :last-round-result="lastRoundResult"
          :format-score="formatScore"
          :send-action="sendAction"
          :confirm-answer="confirmAnswer"
          :force-confirm-answer="forceConfirmAnswer"
          :send-reminder="sendReminder"
        />

        <!-- Player Section -->
        <PlayerSection
          v-if="state.round_phase !== 'finished'"
          :state="state"
          :is-admin="isAdmin"
          :show-admin="showAdmin"
          :user-id="userId"
          :local-timer-remaining="localTimerRemaining"
          :timer-display="timerDisplay"
          :my-score="myScore"
          :my-choice="myChoice"
          :my-eliminated="myEliminated"
          :my-confirmed="myConfirmed"
          :forced-all-in="forcedAllIn"
          :can-voluntary-all-in="canVoluntaryAllIn"
          :all-in="allIn"
          :sorted-players="sortedPlayers"
          :last-round-result="lastRoundResult"
          :my-last-change="myLastChange"
          :format-score="formatScore"
          :vote="vote"
          :submit-vote="submitVote"
          :confirm-vote="confirmVote"
          @toggle-all-in="allIn = !allIn"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { useWebSocket } from './composables/useWebSocket.js'
import JoinScreen from './components/JoinScreen.vue'
import AdminPanel from './components/AdminPanel.vue'
import PlayerSection from './components/PlayerSection.vue'
import TitlesScreen from './components/TitlesScreen.vue'

const {
  joined,
  isAdmin,
  showAdmin,
  userId,
  toast,
  allIn,
  myConfirmed,
  reminderBanner,
  adminPassword,
  pendingAnswer,
  isDark,
  reconnecting,
  state,
  localTimerRemaining,
  myScore,
  myChoice,
  myEliminated,
  forcedAllIn,
  canVoluntaryAllIn,
  timerDisplay,
  phaseLabel,
  phaseBadge,
  sortedPlayers,
  lastRoundResult,
  myLastChange,
  myTitles,
  toggleTheme,
  formatScore,
  sendAction,
  joinGame,
  unlockAdmin,
  vote,
  submitVote,
  confirmVote,
  confirmAnswer,
  forceConfirmAnswer,
  sendReminder,
} = useWebSocket()
</script>
