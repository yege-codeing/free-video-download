<template>
  <div class="px-4 mb-8 animate-fade-in-up">
    <div class="glass-card overflow-hidden">
      <!-- Thumbnail + Info row -->
      <div class="flex flex-col sm:flex-row">
        <!-- Thumbnail -->
        <div class="sm:w-64 flex-shrink-0 relative overflow-hidden bg-bg-primary">
          <img v-if="info.thumbnail" :src="info.thumbnail" :alt="info.title"
               class="w-full h-40 sm:h-full object-cover" referrerpolicy="no-referrer" />
          <div v-else class="w-full h-40 sm:h-full flex items-center justify-center bg-bg-tertiary">
            <svg class="w-12 h-12 text-text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round"
                    d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
            </svg>
          </div>
          <!-- Duration badge -->
          <span v-if="info.duration_str" class="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-0.5 rounded">
            {{ info.duration_str }}
          </span>
        </div>

        <!-- Info -->
        <div class="flex-1 p-4 flex flex-col justify-between">
          <div>
            <h3 class="font-bold text-base text-text-primary mb-2 line-clamp-2 leading-snug">{{ info.title }}</h3>
            <div class="flex items-center gap-3 text-xs text-text-secondary">
              <span class="flex items-center gap-1">
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0" />
                </svg>
                {{ info.author }}
              </span>
              <span v-if="info.platform_label" class="px-2 py-0.5 rounded-full bg-bg-tertiary border border-border/50">
                {{ info.platform_label }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Format selector -->
      <div class="border-t border-border/50 p-4">
        <p class="text-text-secondary text-xs mb-3">选择清晰度 / 格式</p>
        <div class="flex flex-wrap gap-2 mb-4">
          <button
            v-for="fmt in info.formats" :key="fmt.format_id"
            type="button"
            :disabled="downloading"
            @click="$emit('selectFormat', fmt.format_id)"
            :class="[
              'px-3 py-1.5 rounded-lg text-xs border transition-all',
              downloading
                ? 'opacity-50 cursor-not-allowed'
                : 'cursor-pointer',
              selectedFormat === fmt.format_id
                ? 'border-accent bg-accent/10 text-accent'
                : 'border-border/50 text-text-secondary hover:border-border-light hover:text-text-primary'
            ]"
          >
            <span class="font-medium">{{ fmt.label }}</span>
            <span v-if="fmt.filesize_str && fmt.filesize_str !== '自动选择'" class="ml-1 opacity-60">{{ fmt.filesize_str }}</span>
          </button>
        </div>

        <!-- Download progress -->
        <div v-if="downloading" class="mb-4">
          <div class="flex justify-between text-xs text-text-secondary mb-1.5">
            <span>{{ progressLabel }}</span>
            <span v-if="downloadPhase !== 'processing'">{{ Math.round(downloadProgress) }}%</span>
            <span v-else class="text-text-tertiary">处理中</span>
          </div>
          <div class="h-2 rounded-full bg-bg-primary overflow-hidden relative">
            <div
              class="h-full rounded-full gradient-bg transition-all duration-500 ease-out"
              :class="{ 'animate-pulse': downloadPhase === 'processing' && downloadProgress >= 90 }"
              :style="{ width: `${downloadProgress}%` }"
            />
          </div>
          <p v-if="downloadPhase === 'processing' && downloadProgress >= 90"
             class="text-text-tertiary text-xs mt-1.5">
            视频较大时处理时间较长，请耐心等待，进度条会继续缓慢前进
          </p>
        </div>

        <!-- Download button -->
        <button
          type="button"
          @click="$emit('download')"
          :disabled="downloading || !selectedFormat"
          class="btn-primary w-full py-3 text-base flex items-center justify-center gap-2"
        >
          <svg v-if="downloading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          <span>{{ downloading ? '准备下载中...' : '立即下载' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  info: { type: Object, required: true },
  selectedFormat: { type: String, default: null },
  downloading: { type: Boolean, default: false },
  downloadProgress: { type: Number, default: 0 },
  downloadPhase: { type: String, default: 'idle' },
})
defineEmits(['selectFormat', 'download'])

const progressLabel = computed(() => {
  switch (props.downloadPhase) {
    case 'processing':
      return '正在从平台下载并处理视频...'
    case 'transferring':
      return '正在传输到浏览器...'
    case 'saving':
      return '即将弹出保存窗口...'
    default:
      return '准备中...'
  }
})
</script>
