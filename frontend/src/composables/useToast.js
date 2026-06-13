import { ref } from 'vue'

const visible = ref(false)
const message = ref('')
const type = ref('success')

let hideTimer = null

export function showToast(msg, toastType = 'success', duration = 2400) {
  message.value = msg
  type.value = toastType
  visible.value = true
  if (hideTimer) clearTimeout(hideTimer)
  hideTimer = setTimeout(() => {
    visible.value = false
  }, duration)
}

export function useToast() {
  return { visible, message, type, showToast }
}
