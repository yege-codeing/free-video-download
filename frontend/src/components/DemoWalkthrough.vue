<template>
  <div class="demo-walkthrough px-4 sm:px-6 mb-6" role="list" aria-label="产品演示步骤">
    <div class="flex items-center justify-center gap-2 sm:gap-4 flex-wrap">
      <template v-for="(step, i) in steps" :key="step.key">
        <button
          type="button"
          role="listitem"
          :aria-current="activeStep === i ? 'step' : undefined"
          class="demo-step focus-ring cursor-pointer"
          :class="{ 'demo-step-active': activeStep === i, 'demo-step-done': activeStep > i }"
          @click="$emit('goto', i)"
        >
          <span class="demo-step-num">
            <svg v-if="activeStep > i" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            <span v-else>{{ i + 1 }}</span>
          </span>
          <span class="demo-step-label">{{ step.label }}</span>
          <span class="demo-step-hint hidden lg:block">{{ step.hint }}</span>
        </button>
        <span v-if="i < steps.length - 1" class="demo-step-connector" :class="{ 'demo-step-connector-done': activeStep > i }" aria-hidden="true" />
      </template>
    </div>
  </div>
</template>

<script setup>
defineProps({
  activeStep: { type: Number, default: 0 },
})
defineEmits(['goto'])

const steps = [
  { key: 'paste', label: '粘贴链接', hint: '支持 1800+ 平台' },
  { key: 'parse', label: '解析视频', hint: '自动识别格式' },
  { key: 'action', label: '下载 / 总结', hint: '一键完成' },
]
</script>
