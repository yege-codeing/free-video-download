import { ref } from 'vue'

export const isAuthenticated = ref(false)
export const username = ref('')
export const authEnabled = ref(true)
export const checking = ref(true)
export const sessionMessage = ref('')

export function onUnauthorized() {
  if (!authEnabled.value) return
  isAuthenticated.value = false
  username.value = ''
  sessionMessage.value = '登录已过期，请重新登录'
}

export function setAuthenticated(user) {
  isAuthenticated.value = true
  username.value = user || ''
  sessionMessage.value = ''
}

export function clearAuthenticated() {
  isAuthenticated.value = false
  username.value = ''
  sessionMessage.value = ''
}
