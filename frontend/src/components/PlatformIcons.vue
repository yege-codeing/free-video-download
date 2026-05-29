<template>
  <div class="px-4 mb-10">
    <p class="text-text-tertiary text-xs text-center mb-3">支持平台</p>
    <div class="flex flex-wrap justify-center gap-3">
      <div v-for="p in platforms" :key="p.id"
           class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-bg-secondary border border-border/50 text-xs text-text-secondary hover:border-accent/30 hover:text-text-primary transition-all cursor-default">
        <span class="w-2 h-2 rounded-full flex-shrink-0" :style="{ backgroundColor: p.color }"></span>
        <span>{{ p.name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
const platforms = [
  { id: 'bilibili', name: 'B站', color: '#00A1D6' },
  { id: 'douyin', name: '抖音', color: '#FE2C55' },
  { id: 'youtube', name: 'YouTube', color: '#FF0000' },
  { id: 'tiktok', name: 'TikTok', color: '#69C9D0' },
  { id: 'xiaohongshu', name: '小红书', color: '#FF2442' },
  { id: 'twitter', name: 'X/Twitter', color: '#1DA1F2' },
  { id: 'instagram', name: 'Instagram', color: '#E4405F' },
  { id: 'facebook', name: 'Facebook', color: '#1877F2' },
  { id: 'more', name: '1800+更多', color: '#888888' },
]
</script>
