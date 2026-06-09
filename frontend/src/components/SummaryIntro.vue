<template>
  <section class="px-4 mb-12">
    <div class="glass-card p-6">
      <h2 class="text-lg font-bold gradient-text mb-1 text-center">AI 视频总结</h2>
      <p class="text-text-tertiary text-sm mb-6 text-center">粘贴视频链接，AI 帮你快速提炼大纲与核心要点</p>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div v-for="feat in features" :key="feat.title"
             class="p-3 rounded-xl bg-bg-tertiary/50 border border-border/30">
          <div class="text-2xl mb-1">{{ feat.icon }}</div>
          <div class="text-xs font-medium text-text-secondary mb-0.5">{{ feat.title }}</div>
          <div class="text-[11px] text-text-tertiary leading-snug">{{ feat.desc }}</div>
        </div>
      </div>
      <p class="text-text-tertiary text-[11px] mt-5 text-center">
        优先使用平台字幕；B 站需登录的字幕会自动改用 SenseVoice 语音识别（无需登录，长视频需等待）
      </p>
    </div>
  </section>
</template>

<script setup>
const features = [
  { icon: '📝', title: '结构化总结', desc: '一句话概述 + 核心要点' },
  { icon: '🗂️', title: '章节时间戳', desc: '点击跳转源视频对应位置' },
  { icon: '🎙️', title: 'SenseVoice 兜底', desc: '无字幕时本地语音识别，无需 B 站登录' },
  { icon: '🧠', title: '思维导图', desc: '层级化梳理知识结构' },
  { icon: '💬', title: 'AI 追问', desc: '基于视频内容深入问答' },
  { icon: '⬇️', title: '分块导出', desc: '总结/章节/转录/导图/对话各自复制与导出' },
]
</script>
