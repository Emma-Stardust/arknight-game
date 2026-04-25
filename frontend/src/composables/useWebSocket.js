import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'

export function useWebSocket() {
  const joined = ref(false)
  const isAdmin = ref(false)
  const showAdmin = ref(false)
  const userId = ref(null)
  const toast = ref('')
  const allIn = ref(false)
  const myConfirmed = ref(false)
  const reminderBanner = ref('')
  const adminPassword = ref('')
  const pendingAnswer = ref(null)
  const isDark = ref(false)
  const reconnecting = ref(false)
  const serverVersion = ref(0)
  const localTimerRemaining = ref(0)
  const ws = ref(null)

  const state = reactive({
    version: 0,
    game_active: false,
    current_round: 0,
    total_rounds: 10,
    round_stake: 0,
    round_phase: 'idle',
    correct_answer: null,
    can_rollback: false,
    all_confirmed: false,
    timer_remaining: 0,
    timer_expired: false,
    players: {},
    history: [],
    titles: {},
    voted_count: 0,
    active_count: 0,
  })

  let toastTimer = null
  let reconnectTimer = null
  let heartbeatTimer = null
  let localTimerInterval = null

  // ── Computed ──
  const myData = computed(() =>
    userId.value && state.players[userId.value] ? state.players[userId.value] : null
  )
  const myScore = computed(() => (myData.value ? myData.value.score : 0))
  const myChoice = computed(() => (myData.value ? myData.value.choice : null))
  const myEliminated = computed(() => (myData.value ? myData.value.eliminated : false))
  const forcedAllIn = computed(() => {
    if (!myData.value || myEliminated.value) return false
    return myScore.value > 0 && myScore.value < state.round_stake
  })
  const canVoluntaryAllIn = computed(() => {
    if (!myData.value || myEliminated.value) return false
    if (myScore.value <= 0) return false
    if (state.current_round < 6) return false
    return myScore.value >= state.round_stake
  })
  const phaseLabel = computed(
    () =>
      ({ idle: '未开始', voting: '投票中', revealed: '已揭晓', finished: '已结束' }[
        state.round_phase
      ] || '')
  )
  const phaseBadge = computed(
    () =>
      ({
        idle: 'badge-idle',
        voting: 'badge-voting',
        revealed: 'badge-revealed',
        finished: 'badge-finished',
      }[state.round_phase] || 'badge-idle')
  )
  const sortedPlayers = computed(() => {
    const l = Object.entries(state.players).map(([uid, p]) => ({ ...p, uid }))
    l.sort((a, b) => b.score - a.score)
    return l
  })
  const lastRoundResult = computed(() =>
    state.history.length ? state.history[state.history.length - 1].results : null
  )
  const myLastChange = computed(() => {
    if (!lastRoundResult.value || !userId.value) return 0
    const r = lastRoundResult.value.find((x) => x.uid === userId.value)
    return r ? r.change : 0
  })
  const timerDisplay = computed(() => {
    const s = localTimerRemaining.value
    if (s <= 0) return { text: '00:00', warning: false, danger: false }
    const m = Math.floor(s / 60)
    const sec = s % 60
    return {
      text: `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`,
      warning: s <= 60 && s > 30,
      danger: s <= 30,
    }
  })
  const myTitles = computed(() => {
    if (state.round_phase !== 'finished' || !userId.value) return []
    return state.titles[userId.value] || []
  })

  // ── Theme ──
  function initTheme() {
    const s = localStorage.getItem('game-theme')
    if (s) {
      isDark.value = s === 'dark'
    } else {
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
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

  // ── Score format ──
  function formatScore(val) {
    if (val >= 10000) {
      const wan = val / 10000
      return (wan % 1 === 0 ? wan.toFixed(0) : wan.toFixed(1)) + '万'
    }
    return String(val)
  }

  // ── WebSocket ──
  function connect() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    ws.value = new WebSocket(`${proto}://${location.host}/ws`)
    ws.value.onopen = () => {
      reconnecting.value = false
      if (joined.value) return
      const saved = localStorage.getItem('game-uid')
      if (saved) {
        const savedPwd = localStorage.getItem('game-admin-pwd') || ''
        ws.value.send(JSON.stringify({ action: 'reconnect', user_id: saved, admin_password: savedPwd }))
      }
    }
    ws.value.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'joined') {
        userId.value = msg.user_id
        joined.value = true
        isAdmin.value = msg.is_admin || false
        localStorage.setItem('game-uid', msg.user_id)
        if (isAdmin.value) localStorage.setItem('game-admin-pwd', adminPassword.value)
        applyState(msg.data)
        reconnecting.value = false
      } else if (msg.type === 'reconnected') {
        userId.value = msg.user_id
        joined.value = true
        isAdmin.value = msg.is_admin || false
        localStorage.setItem('game-uid', msg.user_id)
        applyState(msg.data)
        reconnecting.value = false
      } else if (msg.type === 'admin_unlocked') {
        isAdmin.value = true
        localStorage.setItem('game-admin-pwd', adminPassword.value)
      } else if (msg.type === 'state') {
        applyState(msg.data)
      } else if (msg.type === 'error') {
        showToast(msg.message)
        if (!joined.value) localStorage.removeItem('game-uid')
      } else if (msg.type === 'reminder') {
        reminderBanner.value = msg.message
        setTimeout(() => {
          reminderBanner.value = ''
        }, 8000)
      } else if (msg.type === 'info') {
        showToast(msg.message)
      }
    }
    ws.value.onclose = () => {
      reconnecting.value = true
      reconnectTimer = setTimeout(connect, 2000)
    }
    ws.value.onerror = () => {
      ws.value.close()
    }
  }

  function applyState(data) {
    if (data.version !== undefined && data.version <= serverVersion.value) return
    if (data.version !== undefined) serverVersion.value = data.version
    if (data.timer_remaining !== undefined && data.round_phase === 'voting') {
      if (Math.abs(data.timer_remaining - localTimerRemaining.value) > 3) {
        localTimerRemaining.value = data.timer_remaining
      }
    } else if (data.round_phase !== 'voting') {
      localTimerRemaining.value = 0
    }
    Object.assign(state, data)
    if (userId.value && data.players && data.players[userId.value]) {
      myConfirmed.value = data.players[userId.value].confirmed || false
    }
  }

  function sendAction(action, data = {}) {
    if (ws.value && ws.value.readyState === WebSocket.OPEN)
      ws.value.send(JSON.stringify({ action, ...data }))
  }

  // ── Actions ──
  function joinGame(nameInput, uidInput) {
    const UID_RE = /^[A-Za-z0-9_-]{2,16}$/
    if (!uidInput.trim() || !UID_RE.test(uidInput.trim()) || !nameInput.trim()) return
    if (ws.value && ws.value.readyState === WebSocket.OPEN)
      ws.value.send(
        JSON.stringify({
          action: 'join',
          name: nameInput.trim(),
          user_id: uidInput.trim(),
          admin_password: adminPassword.value,
        })
      )
  }

  function unlockAdmin() {
    const pwd = prompt('输入管理员密码')
    if (pwd === null) return
    adminPassword.value = pwd
    sendAction('unlock_admin', { password: pwd })
  }

  function vote(choice) {
    if (myEliminated.value || state.round_phase !== 'voting') return
    if (choice !== 'watch' && choice !== 'left' && choice !== 'right') return
    if (choice === 'watch') allIn.value = false
    const effectiveAllIn = choice !== 'watch' && forcedAllIn.value ? true : allIn.value
    sendAction('vote', { choice, all_in: effectiveAllIn })
  }

  function submitVote() {
    if (myChoice.value && myChoice.value !== 'watch') {
      const effectiveAllIn = forcedAllIn.value ? true : allIn.value
      sendAction('vote', { choice: myChoice.value, all_in: effectiveAllIn })
    }
  }

  function confirmVote() {
    sendAction('confirm_vote')
  }

  function confirmAnswer() {
    if (!pendingAnswer.value) return
    sendAction('set_answer', { answer: pendingAnswer.value })
    pendingAnswer.value = null
  }

  function forceConfirmAnswer() {
    if (!pendingAnswer.value) return
    if (confirm('还有玩家未确认选择！未选择者将按观望处理。确定要公布答案吗？')) {
      sendAction('set_answer', { answer: pendingAnswer.value })
      pendingAnswer.value = null
    }
  }

  function sendReminder(text) {
    sendAction('send_reminder', { text })
  }

  function showToast(msg) {
    toast.value = msg
    clearTimeout(toastTimer)
    toastTimer = setTimeout(() => {
      toast.value = ''
    }, 3000)
  }

  // ── Lifecycle ──
  onMounted(() => {
    initTheme()
    connect()
    heartbeatTimer = setInterval(() => {
      if (ws.value && ws.value.readyState === WebSocket.OPEN) sendAction('sync')
    }, 15000)
    localTimerInterval = setInterval(() => {
      if (state.round_phase === 'voting' && localTimerRemaining.value > 0)
        localTimerRemaining.value--
    }, 1000)
  })

  onUnmounted(() => {
    clearTimeout(reconnectTimer)
    clearInterval(heartbeatTimer)
    clearInterval(localTimerInterval)
    if (ws.value) ws.value.close()
  })

  watch(
    () => state.round_phase,
    (v) => {
      if (v === 'voting') {
        pendingAnswer.value = null
        myConfirmed.value = false
        allIn.value = false
      }
      if (v === 'idle' || v === 'finished') {
        allIn.value = false
        myConfirmed.value = false
        pendingAnswer.value = null
      }
    }
  )

  return {
    // State
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
    // Computed
    myData,
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
    // Methods
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
    showToast,
  }
}
