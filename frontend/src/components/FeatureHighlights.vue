<template>
  <section class="px-4 sm:px-6 mb-12">
    <div class="text-center mb-8">
      <span class="demo-section-badge">功能亮点</span>
      <h2 class="text-xl sm:text-2xl font-bold text-text-primary mt-3 mb-2">
        悬停探索，<span class="gradient-text">所见即所得</span>
      </h2>
      <p class="text-text-secondary text-sm max-w-md mx-auto">
        悬停或点击功能卡片，查看每项能力的详细说明
      </p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <button
        v-for="(feat, i) in features" :key="feat.title"
        type="button"
        class="feature-reveal group cursor-pointer text-left w-full"
        :class="{ 'feature-reveal-open': openIndex === i }"
        :aria-expanded="openIndex === i"
        @click="toggle(i)"
      >
        <div class="feature-reveal-icon">
          <component :is="feat.icon" />
        </div>
        <h3 class="text-sm font-semibold text-text-primary mb-1">{{ feat.title }}</h3>
        <p class="text-xs text-text-tertiary leading-relaxed">{{ feat.desc }}</p>
        <div class="feature-reveal-overlay">
          <p class="text-sm text-text-primary font-medium mb-2">{{ feat.title }}</p>
          <p class="text-xs text-text-secondary leading-relaxed">{{ feat.detail }}</p>
          <span v-if="feat.tag" class="feature-reveal-tag">{{ feat.tag }}</span>
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
    title: '全网解析',
    desc: '粘贴链接，自动识别平台与格式',
    detail: '基于 yt-dlp 引擎，支持 B站、抖音、YouTube 等 1800+ 平台，自动提取最高清晰度。',
    tag: '核心能力',
    icon: icon(['M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1']),
  },
  {
    title: 'AI 智能总结',
    desc: '字幕提取 + 语音识别 + 结构化输出',
    detail: '优先使用平台字幕，无字幕时自动调用 SenseVoice 本地识别，生成总结、章节、思维导图。',
    tag: 'AI 能力',
    icon: icon(['M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z']),
  },
  {
    title: '高清无水印',
    desc: '多格式选择，FFmpeg 自动合并',
    detail: '支持 1080P / 4K 等多种清晰度，音视频分离时自动合并，下载进度实时可见。',
    tag: '下载',
    icon: icon(['M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3']),
  },
  {
    title: '章节时间戳',
    desc: '点击跳转源视频对应位置',
    detail: 'AI 自动划分章节并标注时间戳，一键跳转到 YouTube、B站等原视频对应片段。',
    tag: 'AI 总结',
    icon: icon(['M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z']),
  },
  {
    title: '思维导图',
    desc: '层级化梳理知识结构',
    detail: '自动生成可交互的思维导图，支持缩放、拖拽和 PNG 导出，方便分享与复习。',
    tag: '可视化',
    icon: icon(['M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7']),
  },
  {
    title: 'AI 追问',
    desc: '基于视频内容深入问答',
    detail: '在总结完成后，可以就视频内容自由提问，AI 基于完整转录文本进行回答。',
    tag: '对话',
    icon: icon(['M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z']),
  },
]
</script>
