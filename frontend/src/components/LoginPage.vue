<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-12 relative overflow-hidden">
    <div class="absolute inset-0 pointer-events-none" aria-hidden="true">
      <div class="absolute top-1/4 -left-32 w-96 h-96 rounded-full bg-accent/10 blur-3xl" />
      <div class="absolute bottom-1/4 -right-32 w-96 h-96 rounded-full bg-accent-gold/10 blur-3xl" />
    </div>

    <div class="glass-card w-full max-w-md p-8 relative z-10 -translate-y-[10px]">
      <ToastHost />
      <div class="flex items-center justify-center gap-4 mb-8">
        <div class="w-12 h-12 rounded-xl gradient-bg flex items-center justify-center flex-shrink-0">
          <svg class="w-6 h-6 text-bg-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 3l14 9-14 9V3z" />
          </svg>
        </div>
        <div class="text-left">
          <h1 class="text-2xl font-bold gradient-text leading-tight">SaveAny</h1>
          <p class="text-text-secondary text-sm mt-1">万能视频下载器</p>
        </div>
      </div>

      <form class="space-y-5" @submit.prevent="handleSubmit">
        <div class="gradient-border glow-input transition-shadow duration-300">
          <input
            id="username"
            v-model="form.username"
            type="text"
            autocomplete="username"
            aria-label="账号"
            placeholder="请输入账号"
            class="w-full bg-bg-tertiary rounded-2xl px-4 py-3 text-text-primary placeholder-text-tertiary outline-none"
          />
        </div>

        <div class="gradient-border glow-input transition-shadow duration-300">
          <div class="flex items-center bg-bg-tertiary rounded-2xl px-4 py-3">
            <input
              id="password"
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              aria-label="密码"
              placeholder="请输入密码"
              class="flex-1 min-w-0 bg-transparent text-text-primary placeholder-text-tertiary outline-none"
            />
            <button
              type="button"
              class="text-text-tertiary hover:text-text-secondary transition-colors p-1 cursor-pointer flex-shrink-0"
              :aria-label="showPassword ? '隐藏密码' : '显示密码'"
              @click="showPassword = !showPassword"
            >
              <svg v-if="showPassword" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
          </div>
        </div>

        <div class="flex gap-3">
          <div class="gradient-border glow-input transition-shadow duration-300 flex-1 min-w-0">
            <input
              id="captcha"
              v-model="form.captcha"
              type="text"
              autocomplete="off"
              aria-label="验证码"
              placeholder="请输入验证码"
              maxlength="4"
              class="w-full bg-bg-tertiary rounded-2xl px-4 py-3 text-text-primary placeholder-text-tertiary outline-none uppercase"
            />
          </div>
          <button
            type="button"
            class="flex-shrink-0 rounded-xl overflow-hidden border border-border hover:border-border-light transition-colors cursor-pointer focus-ring"
            title="点击刷新验证码"
            :disabled="captchaLoading"
            @click="loadCaptcha"
          >
            <img
              v-if="captchaImage"
              :src="captchaImage"
              alt="验证码"
              class="block w-[120px] h-10 object-cover"
            />
            <div v-else class="w-[120px] h-10 bg-bg-tertiary flex items-center justify-center text-text-tertiary text-xs">
              {{ captchaLoading ? '加载中…' : '点击刷新' }}
            </div>
          </button>
        </div>

        <button
          type="submit"
          class="btn-primary w-full py-3 text-base flex items-center justify-center gap-2"
          :disabled="loading || !canSubmit"
        >
          <svg v-if="loading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <span>{{ loading ? '登录中…' : '登录' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import * as authApi from '../api/auth.js'
import { setAuthenticated } from '../composables/authState.js'
import { showToast } from '../composables/useToast.js'
import ToastHost from './ToastHost.vue'

const emit = defineEmits(['success'])

const form = reactive({
  username: '',
  password: '',
  captcha: '',
})

const showPassword = ref(false)
const captchaImage = ref('')
const captchaLoading = ref(false)
const loading = ref(false)

const canSubmit = computed(() =>
  form.username.trim() && form.password && form.captcha.trim(),
)

async function loadCaptcha() {
  captchaLoading.value = true
  try {
    const data = await authApi.getCaptcha()
    captchaImage.value = data.image
    form.captcha = ''
  } catch (e) {
    showToast(e.message || '验证码加载失败', 'error')
    captchaImage.value = ''
  } finally {
    captchaLoading.value = false
  }
}

function resolveLoginError(message) {
  if (message.includes('验证码')) return '验证码错误'
  if (message.includes('账号或密码')) return '账号或密码错误'
  return message || '登录失败'
}

async function handleSubmit() {
  if (!canSubmit.value || loading.value) return
  loading.value = true
  try {
    const data = await authApi.login({
      username: form.username.trim(),
      password: form.password,
      captcha: form.captcha.trim(),
    })
    showToast('登录成功', 'success')
    await new Promise((resolve) => setTimeout(resolve, 800))
    setAuthenticated(data.username || form.username.trim())
    emit('success')
  } catch (e) {
    showToast(resolveLoginError(e.message), 'error')
    await loadCaptcha()
  } finally {
    loading.value = false
  }
}

onMounted(loadCaptcha)
</script>
