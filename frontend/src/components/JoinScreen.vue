<script setup>
import { ref, computed } from 'vue'

const emit = defineEmits(['join'])

const nameInput = ref('')
const uidInput = ref('')
const adminPassword = ref('')

const UID_RE = /^[A-Za-z0-9_-]{2,16}$/
const canJoin = computed(() => uidInput.value.trim() && UID_RE.test(uidInput.value.trim()) && nameInput.value.trim())

function submit() {
  if (!canJoin.value) return
  emit('join', { name: nameInput.value.trim(), uid: uidInput.value.trim(), password: adminPassword.value })
}
</script>

<template>
  <div class="join-screen">
    <div class="join-emblem"><span>AK</span></div>
    <div class="join-title">明日方舟</div>
    <div class="join-sub">斗蛐蛐 计分板</div>
    <div class="join-desc">选择你的方向，押上你的积分</div>
    <div class="input-group">
      <label>玩家 ID</label>
      <input v-model="uidInput" placeholder="输入你的ID" @keyup.enter="submit" maxlength="16" autocomplete="off" spellcheck="false">
      <div class="hint">2-16位，字母数字下划线横杠</div>
    </div>
    <div class="input-group">
      <label>昵称</label>
      <input v-model="nameInput" placeholder="输入昵称" @keyup.enter="submit" maxlength="12">
    </div>
    <div class="input-group">
      <label>管理员密码 (可选)</label>
      <input v-model="adminPassword" type="password" placeholder="输入密码解锁管理" @keyup.enter="submit" autocomplete="off">
    </div>
    <div style="width:100%;max-width:320px">
      <button class="btn btn-primary" @click="submit" :disabled="!canJoin">加入游戏！</button>
    </div>
  </div>
</template>
