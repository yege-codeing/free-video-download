<template>
  <Transition name="toast">
    <div
      v-if="visible"
      role="status"
      aria-live="polite"
      class="absolute inset-0 flex items-center justify-center z-20 pointer-events-none"
    >
      <div class="toast-panel glass-card px-6 py-3 shadow-lg shadow-black/40 border border-border/60">
        <span class="toast-text">{{ message }}</span>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { useToast } from '../composables/useToast.js'

const { visible, message } = useToast()
</script>

<style scoped>
.toast-panel {
  min-width: 8rem;
  text-align: center;
}

.toast-text {
  display: inline-block;
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.5;
  color: #ff6b6b;
  background: linear-gradient(135deg, #ff6b6b 0%, #ffd93d 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: scale(0.96);
}
</style>
