<template>
  <div class="px-4 sm:px-6 mb-5 flex justify-center">
    <div class="inline-flex p-1 rounded-xl bg-bg-tertiary/80 border border-border/50" role="tablist" aria-label="演示模式">
      <button
        v-for="m in modes" :key="m.id"
        type="button"
        :aria-pressed="mode === m.id"
        role="tab"
        @click="$emit('update:mode', m.id)"
        :class="[
          'focus-ring cursor-pointer px-4 py-2 text-sm rounded-lg transition-colors flex items-center gap-1.5',
          mode === m.id
            ? 'gradient-bg text-bg-primary font-bold shadow'
            : 'text-text-secondary hover:text-text-primary hover:bg-bg-primary/50'
        ]"
      >
        <svg v-if="m.id === 'download'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
        <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.456-2.456L14.25 6l1.035-.259a3.375 3.375 0 002.456-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z" />
        </svg>
        <span>{{ m.label }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  mode: { type: String, default: 'download' },
})
defineEmits(['update:mode'])

const modes = [
  { id: 'download', label: '视频下载' },
  { id: 'summary', label: 'AI 总结' },
]
</script>
