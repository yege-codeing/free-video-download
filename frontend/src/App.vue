<template>
  <div class="min-h-screen flex flex-col relative w-full lg:w-[70%] mx-auto">
    <NavBar />

    <main class="flex-1 relative">
      <HeroSection />

      <ModeTabs :mode="mode" @update:mode="setMode" />

      <!-- Download mode -->
      <template v-if="mode === 'download'">
        <UrlInput
          :modelValue="videoUrl"
          @update:modelValue="videoUrl = $event"
          :loading="loading"
          :error="error"
          @parse="handleParse"
          @clear="reset"
        />

        <PlatformIcons />

        <VideoCard
          v-if="videoInfo"
          :info="videoInfo"
          :selectedFormat="selectedFormat"
          :downloading="downloading"
          :downloadProgress="downloadProgress"
          :downloadPhase="downloadPhase"
          @selectFormat="selectFormat"
          @download="handleDownload"
        />
      </template>

      <!-- AI summary mode -->
      <template v-else>
        <UrlInput
          :modelValue="summaryUrl"
          @update:modelValue="summaryUrl = $event"
          :loading="loadingTranscript || summarizing"
          :loadingLabel="loadingTranscript ? '字幕/语音识别中…' : 'AI 总结中…'"
          :error="summaryError"
          @parse="handleGetTranscript"
          @clear="resetSummary"
        />

        <SummaryPanel
          v-if="transcript"
          :info="transcript"
          :summary="summary"
          :chapters="chapters"
          :mindmap="mindmap"
          :summarizing="summarizing"
          :chatMessages="chatMessages"
          :chatStreaming="chatStreaming"
          @ask="handleAsk"
        />
        <SummaryIntro v-else />
      </template>

      <ComingSoon />
    </main>

    <FooterBar />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import NavBar from './components/NavBar.vue'
import HeroSection from './components/HeroSection.vue'
import ModeTabs from './components/ModeTabs.vue'
import UrlInput from './components/UrlInput.vue'
import PlatformIcons from './components/PlatformIcons.vue'
import VideoCard from './components/VideoCard.vue'
import SummaryPanel from './components/SummaryPanel.vue'
import SummaryIntro from './components/SummaryIntro.vue'
import ComingSoon from './components/ComingSoon.vue'
import FooterBar from './components/FooterBar.vue'
import { useVideoDownload } from './composables/useVideoDownload.js'
import { useVideoSummary } from './composables/useVideoSummary.js'

const mode = ref('download')
function setMode(m) {
  mode.value = m
}

const {
  videoUrl,
  videoInfo,
  selectedFormat,
  loading,
  downloading,
  downloadProgress,
  downloadPhase,
  error,
  handleParse,
  handleDownload,
  selectFormat,
  reset,
} = useVideoDownload()

const {
  summaryUrl,
  transcript,
  loadingTranscript,
  error: summaryError,
  summary,
  chapters,
  mindmap,
  summarizing,
  chatMessages,
  chatStreaming,
  handleGetTranscript,
  handleAsk,
  reset: resetSummary,
} = useVideoSummary()
</script>
