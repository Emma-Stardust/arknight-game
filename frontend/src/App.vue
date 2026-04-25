<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import JoinScreen from './components/JoinScreen.vue'
import AdminPanel from './components/AdminPanel.vue'
import PlayerSection from './components/PlayerSection.vue'
import { useWebSocket } from './composables/useWebSocket.js'

const joined = ref(false)
const isAdmin = ref(false)
const showAdmin = ref(false)
const isDark = ref(false)
const reconnecting = ref(false)
const reminderBanner = ref('')
const toast = ref('')
let toastTimer = null

const {
  state, localTimerRemaining, myData, myScore, myChoice, myEliminated,
  myConfirmed, forcedAllIn, canVoluntaryAllIn, myLastChange,
  sortedPlayers, lastRoundResult, phaseLabel, phaseBadge, timerDisplay,
  connect, sendAction, joinGame, vote, submitVote, confirmVote,
  setStake, confirmAnswer, forceConfirmAnswer, sendReminder, unlockAdmin,
} = useWebSocket({ joined, isAdmin, reminderBanner, toast, onToast })

function onToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 3000)
}

// Theme
function initTheme() {
  const s = localStorage.getItem('game-theme')
  isDark.value = s ? s === 'dark' : window.matchMedia('(prefers-color-scheme:dark)').matches
  applyTheme()
}
function applyTheme() {
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}
function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('game-theme', isDark.value ? 'dark' : 'light')
  applyTheme()
}

onMounted(() => { initTheme(); connect() })
</script>

<template>
  <div v-if="reconnecting" class="reconnect-banner">连接断开，正在重连...</div>
  <div v-if="reminderBanner" class="reminder-banner" @click="reminderBanner = ''">{{ reminderBanner }}</div>
  <div v-if="toast" class="toast">{{ toast }}</div>

  <!-- Join Screen -->
  <JoinScreen v-if="!joined" @join="joinGame" />

  <!-- Main View -->
  <template v-else>
    <div class="top-bar">
      <h1>斗蛐蛐 计分板</h1>
      <div class="top-bar-right">
        <span class="badge" :class="phaseBadge">{{ phaseLabel }}</span>
        <button v-if="isAdmin" class="icon-btn icon-btn-admin active" @click="showAdmin = !showAdmin" title="管理面板">&#9881;</button>
        <button v-else class="icon-btn icon-btn-admin" @click="unlockAdmin" title="解锁管理">&#9881;</button>
        <button class="icon-btn icon-btn-theme" @click="toggleTheme">{{ isDark ? '☀' : '☾' }}</button>
      </div>
    </div>

    <div class="page">
      <!-- Admin Panel -->
      <AdminPanel
        v-if="isAdmin && showAdmin"
        :state="state"
        :timerDisplay="timerDisplay"
        :localTimerRemaining="localTimerRemaining"
        :sortedPlayers="sortedPlayers"
        :lastRoundResult="lastRoundResult"
        :pendingAnswer="pendingAnswer"
        @action="sendAction"
        @set-stake="setStake"
        @confirm-answer="confirmAnswer"
        @force-confirm="forceConfirmAnswer"
        @send-reminder="sendReminder"
      />

      <!-- Player Section -->
      <PlayerSection
        :state="state"
        :timerDisplay="timerDisplay"
        :localTimerRemaining="localTimerRemaining"
        :myScore="myScore"
        :myChoice="myChoice"
        :myEliminated="myEliminated"
        :myConfirmed="myConfirmed"
        :forcedAllIn="forcedAllIn"
        :canVoluntaryAllIn="canVoluntaryAllIn"
        :myLastChange="myLastChange"
        :sortedPlayers="sortedPlayers"
        :lastRoundResult="lastRoundResult"
        :showRoundInfo="!isAdmin || !showAdmin"
        @vote="vote"
        @submit-vote="submitVote"
        @confirm-vote="confirmVote"
      />
    </div>
  </template>

  <!-- Animated BG -->
  <div class="bg-pattern"></div>
  <div class="particle"></div><div class="particle"></div><div class="particle"></div>
  <div class="particle"></div><div class="particle"></div><div class="particle"></div>
</template>
