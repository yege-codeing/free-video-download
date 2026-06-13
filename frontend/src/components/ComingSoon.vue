<template>
  <section class="px-4 sm:px-6 mb-12">
    <div class="text-center mb-6">
      <span class="demo-section-badge">即将上线</span>
      <h2 class="text-lg font-bold text-text-primary mt-3 mb-1">更多功能正在开发中</h2>
      <p class="text-text-tertiary text-sm">悬停或点击查看功能说明</p>
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <button
        v-for="(feat, i) in features" :key="feat.title"
        type="button"
        class="feature-reveal group cursor-pointer text-center w-full"
        :class="{ 'feature-reveal-open': openIndex === i }"
        :aria-expanded="openIndex === i"
        @click="toggle(i)"
      >
        <div class="feature-reveal-icon mx-auto">
          <component :is="feat.icon" />
        </div>
        <div class="text-xs font-medium text-text-secondary">{{ feat.title }}</div>
        <div class="feature-reveal-overlay items-center justify-center text-center">
          <p class="text-sm text-text-primary font-medium">{{ feat.title }}</p>
          <p class="text-xs text-text-secondary mt-1">{{ feat.detail }}</p>
        </div>
      </button>
    </div>
  </section>
</template>

<script setup>
import { h, ref } from 'vue'

const openIndex = ref(-1)
function toggle(i) {
  openIndex.value = openIndex.value === i ? -1 : i
}

const icon = (paths) => ({
  render: () => h('svg', {
    class: 'w-5 h-5',
    fill: 'none',
    viewBox: '0 0 24 24',
    stroke: 'currentColor',
    'stroke-width': '2',
  }, paths.map((d) => h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d }))),
})

const features = [
  {
    title: '字幕翻译',
    detail: '多语言字幕自动翻译，打破语言壁垒',
    icon: icon(['M10.5 21l5.25-11.25L21 21l-5.25-11.25L10.5 21zm0 0L5.25 9.75 0 21l5.25-11.25L10.5 21z']),
  },
  {
    title: '批量下载',
    detail: 'Playlist / 收藏夹一键批量解析下载',
    icon: icon(['M3.75 9.75h16.5M3.75 12h16.5m-16.5 2.25h16.5M3.75 6.75h16.5']),
  },
  {
    title: '图文改写',
    detail: '视频内容一键改写为公众号 / 小红书文案',
    icon: icon(['M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10']),
  },
  {
    title: '会员专属',
    detail: '更高并发、更长视频、优先 AI 队列',
    icon: icon(['M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z']),
  },
]
</script>
