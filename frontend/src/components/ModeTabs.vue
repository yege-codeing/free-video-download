<template>
  <div class="px-4 mb-6 flex justify-center">
    <div class="inline-flex p-1 rounded-2xl bg-bg-tertiary/60 border border-border/40">
      <button
        v-for="m in modes" :key="m.id"
        type="button"
        @click="$emit('update:mode', m.id)"
        :class="[
          'px-5 py-2 text-sm rounded-xl transition-all flex items-center gap-1.5',
          mode === m.id
            ? 'gradient-bg text-bg-primary font-bold shadow'
            : 'text-text-secondary hover:text-text-primary'
        ]"
      >
        <span>{{ m.icon }}</span>
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
  { id: 'download', label: '视频下载', icon: '⬇️' },
  { id: 'summary', label: 'AI 总结', icon: '✨' },
]
</script>
