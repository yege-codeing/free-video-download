<template>
  <div class="px-4 sm:px-6 mb-6">
    <div class="gradient-border glow-input transition-shadow duration-300">
      <div class="flex items-center gap-2 bg-bg-tertiary rounded-2xl px-4 py-3">
        <!-- Link icon -->
        <svg class="w-5 h-5 text-text-tertiary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round"
                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>

        <input
          ref="inputRef"
          :value="modelValue"
          @input="emit('update:modelValue', $event.target.value)"
          type="url"
          aria-label="视频链接"
          placeholder="粘贴视频链接，如 bilibili.com/video/BV..."
          class="flex-1 bg-transparent text-text-primary placeholder-text-tertiary outline-none text-base rounded-md"
          @keydown.enter="$emit('parse')"
          @paste="onPaste"
        />

        <!-- Clear button -->
        <button v-if="modelValue" @click="$emit('clear')"
                type="button" aria-label="清空输入"
                class="focus-ring text-text-tertiary hover:text-text-secondary transition-colors p-1 cursor-pointer rounded">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <!-- Parse button -->
        <button
          type="button"
          :disabled="!modelValue || loading"
          class="btn-primary px-5 py-2 text-sm flex items-center gap-2 whitespace-nowrap"
          @click="$emit('parse')"
        >
          <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <span>{{ loading ? (loadingLabel || '解析中') : '解析' }}</span>
        </button>
      </div>
    </div>

    <!-- Error message -->
    <p v-if="error" class="text-error text-sm mt-3 text-center animate-fade-in-up">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  loadingLabel: { type: String, default: '' },
  error: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'parse', 'clear'])
const inputRef = ref(null)

function onPaste() {
  setTimeout(() => emit('parse'), 100)
}

function focus() {
  inputRef.value?.focus()
}

defineExpose({ focus })
</script>
