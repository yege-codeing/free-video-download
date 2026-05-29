<template>
  <footer class="border-t border-border/30 py-6 px-4 text-center">
    <p class="text-text-tertiary text-xs">
      基于
      <a href="https://github.com/yt-dlp/yt-dlp" target="_blank" rel="noopener"
         class="text-text-secondary hover:text-accent transition-colors">yt-dlp</a>
      开源项目构建 · 仅供个人学习使用
    </p>
    <p class="text-text-tertiary/50 text-xs mt-1">&copy; {{ year }} SaveAny</p>
  </footer>
</template>

<script setup>
const year = new Date().getFullYear()
</script>
