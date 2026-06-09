<template>
  <section class="px-4 mb-12">
    <div class="glass-card p-6 text-center">
      <h2 class="text-lg font-bold gradient-text mb-2">更多功能，即将上线</h2>
      <p class="text-text-tertiary text-sm mb-5">我们正在打造更强大的视频工具</p>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div v-for="feat in features" :key="feat.title"
             class="p-3 rounded-xl bg-bg-tertiary/50 border border-border/30 hover:border-accent/20 transition-colors">
          <div class="text-2xl mb-1">{{ feat.icon }}</div>
          <div class="text-xs font-medium text-text-secondary">{{ feat.title }}</div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const features = [
  { icon: '🌐', title: '字幕翻译' },
  { icon: '📦', title: '批量下载' },
  { icon: '✍️', title: '图文改写' },
  { icon: '💎', title: '会员专属' },
]
</script>
