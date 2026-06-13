<template>
  <section class="pt-24 pb-6 px-4 sm:px-6 text-center relative">
    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[450px] opacity-20 pointer-events-none"
         style="background: radial-gradient(ellipse at center, rgba(255,107,107,0.3) 0%, rgba(255,217,61,0.1) 40%, transparent 70%);">
    </div>

    <span class="demo-section-badge relative">交互式产品演示</span>

    <h1 class="text-4xl sm:text-5xl font-extrabold mb-4 mt-5 relative leading-tight">
      <span class="text-text-primary">万能视频</span>
      <span class="gradient-text">下载器</span>
    </h1>

    <p class="text-text-secondary text-base sm:text-lg mb-6 max-w-xl mx-auto relative">
      无需注册，直接在下方体验完整流程 — 粘贴链接、解析视频、一键下载或 AI 总结
    </p>

    <button
      type="button"
      class="btn-demo-cta focus-ring relative"
      @click="$emit('scrollToDemo')"
    >
      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
      </svg>
      立即体验 Live Demo
    </button>
  </section>
</template>

<script setup>
defineEmits(['scrollToDemo'])
</script>
