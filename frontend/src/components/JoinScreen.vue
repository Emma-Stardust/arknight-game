<template>
  <div class="join-screen">
    <div class="join-emblem"><span>AK</span></div>
    <div class="join-title">明日方舟</div>
    <div class="join-sub">斗蛐蛐 计分板</div>
    <div class="join-desc">选择你的方向，押上你的积分</div>
    <div class="input-group">
      <label>玩家 ID</label>
      <input
        v-model="uidInput"
        placeholder="输入你的ID"
        @keyup.enter="doJoin"
        maxlength="16"
        autocomplete="off"
        spellcheck="false"
      />
      <div class="hint">2-16位，字母数字下划线横杠</div>
    </div>
    <div class="input-group">
      <label>昵称</label>
      <input v-model="nameInput" placeholder="输入昵称" @keyup.enter="doJoin" maxlength="12" />
    </div>
    <div class="input-group">
      <label>管理员密码 (可选)</label>
      <input
        v-model="adminPwd"
        type="password"
        placeholder="输入密码解锁管理"
        @keyup.enter="doJoin"
        autocomplete="off"
      />
    </div>
    <div style="width: 100%; max-width: 320px">
      <button class="btn btn-primary" @click="doJoin" :disabled="!canJoin">加入游戏！</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  joinGame: Function,
  adminPassword: String,
})

const UID_RE = /^[A-Za-z0-9_-]{2,16}$/
const uidInput = ref('')
const nameInput = ref('')
const adminPwd = ref(props.adminPassword || '')

const canJoin = computed(
  () => uidInput.value.trim() && UID_RE.test(uidInput.value.trim()) && nameInput.value.trim()
)

const emit = defineEmits(['update:adminPassword'])

function doJoin() {
  if (!canJoin.value) return
  emit('update:adminPassword', adminPwd.value)
  props.joinGame(nameInput.value, uidInput.value)
}
</script>

<style scoped>
.join-screen { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100dvh; padding: 32px 24px; text-align: center }
.join-emblem { width: 80px; height: 80px; border-radius: 20px; background: linear-gradient(135deg,#1A1A2E,#16213E); display: flex; align-items: center; justify-content: center; margin-bottom: 16px; box-shadow: 0 4px 20px rgba(0,0,0,.15); animation: emblemPulse 3s ease-in-out infinite }
.join-emblem span { font-size: 32px; color: #D4A843; font-weight: 800 }
.join-title { font-size: 24px; font-weight: 700; letter-spacing: -.3px; margin-bottom: 2px }
.join-sub { font-size: 16px; font-weight: 500; color: var(--arknights-gold); margin-bottom: 4px }
.join-desc { color: var(--text2); font-size: 13px; margin-bottom: 28px }
.input-group { width: 100%; max-width: 320px; margin-bottom: 12px }
.input-group label { display: block; font-size: 12px; font-weight: 600; color: var(--text2); text-align: left; margin-bottom: 4px; text-transform: uppercase; letter-spacing: .3px }
.input-group input { width: 100%; padding: 14px 16px; border-radius: var(--radius-sm); border: 1.5px solid var(--border); background: var(--bg-card); color: var(--text); font-size: 16px; outline: none; transition: border .2s }
.input-group input:focus { border-color: var(--accent) }
.input-group input::placeholder { color: var(--text3) }
.input-group .hint { font-size: 11px; color: var(--text3); text-align: left; margin-top: 4px }
</style>
