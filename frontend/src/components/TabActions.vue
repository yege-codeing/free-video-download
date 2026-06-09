<template>
  <div class="mt-4 pt-4 border-t border-border/40 flex flex-wrap gap-2">
    <button
      type="button"
      :disabled="!canAct"
      @click="$emit('copy')"
      class="px-4 py-2 text-sm rounded-lg border border-border/50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      :class="canAct ? 'text-text-secondary hover:text-text-primary hover:border-border-light' : 'text-text-tertiary'"
    >
      {{ copied ? '已复制 ✓' : copyLabel }}
    </button>
    <button
      type="button"
      :disabled="!canAct"
      @click="$emit('export')"
      class="px-4 py-2 text-sm rounded-lg border border-border/50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      :class="canAct ? 'text-text-secondary hover:text-text-primary hover:border-border-light' : 'text-text-tertiary'"
    >
      {{ exportLabel }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  canAct: { type: Boolean, default: false },
  copyLabel: { type: String, required: true },
  exportLabel: { type: String, required: true },
  copied: { type: Boolean, default: false },
})
defineEmits(['copy', 'export'])
</script>
