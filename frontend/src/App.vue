<template>
  <div class="min-h-screen flex flex-col relative w-full max-w-5xl mx-auto">
    <NavBar />

    <main class="flex-1 relative">
      <HeroSection @scroll-to-demo="scrollToDemo" />

      <DemoWalkthrough :active-step="demoStep" @goto="onGotoStep" />

      <div ref="demoRef">
        <DemoFrame>
          <ModeTabs :mode="mode" @update:mode="setMode" />

          <template v-if="mode === 'download'">
            <UrlInput
              ref="urlInputRef"
              :modelValue="videoUrl"
              @update:modelValue="videoUrl = $event"
              :loading="loading"
              :error="error"
              @parse="handleParse"
              @clear="reset"
            />
            <PlatformIcons />
            <VideoCardSkeleton v-if="loading && !videoInfo" />
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

          <template v-else>
            <UrlInput
              ref="urlInputRef"
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
            <VideoCardSkeleton v-else-if="loadingTranscript" />
            <SummaryIntro v-else />
          </template>
        </DemoFrame>
      </div>

      <FeatureHighlights />
      <ComingSoon />
    </main>

    <FooterBar />
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import NavBar from './components/NavBar.vue'
import HeroSection from './components/HeroSection.vue'
import DemoWalkthrough from './components/DemoWalkthrough.vue'
import DemoFrame from './components/DemoFrame.vue'
import ModeTabs from './components/ModeTabs.vue'
import UrlInput from './components/UrlInput.vue'
import PlatformIcons from './components/PlatformIcons.vue'
import VideoCard from './components/VideoCard.vue'
import VideoCardSkeleton from './components/VideoCardSkeleton.vue'
import SummaryPanel from './components/SummaryPanel.vue'
import SummaryIntro from './components/SummaryIntro.vue'
import FeatureHighlights from './components/FeatureHighlights.vue'
import ComingSoon from './components/ComingSoon.vue'
import FooterBar from './components/FooterBar.vue'
import { useVideoDownload } from './composables/useVideoDownload.js'
import { useVideoSummary } from './composables/useVideoSummary.js'

const mode = ref('download')
function setMode(m) {
  mode.value = m
}

const demoRef = ref(null)
const urlInputRef = ref(null)

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

const hasUrl = computed(() => {
  const url = mode.value === 'download' ? videoUrl.value : summaryUrl.value
  return !!url?.trim()
})

const hasResult = computed(() => {
  if (mode.value === 'download') {
    return !!videoInfo.value || downloading.value
  }
  return !!transcript.value || loadingTranscript.value || summarizing.value
})

const isParsing = computed(() => {
  if (mode.value === 'download') return loading.value
  return loadingTranscript.value || summarizing.value
})

const demoStep = computed(() => {
  if (hasResult.value) return 2
  if (hasUrl.value || isParsing.value) return 1
  return 0
})

function scrollToDemo() {
  demoRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function onGotoStep(step) {
  scrollToDemo()
  if (step === 0) {
    await nextTick()
    urlInputRef.value?.focus?.()
  }
}
</script>
