<template>
  <div class="min-h-screen flex flex-col relative w-full lg:w-[70%] mx-auto">
    <NavBar />

    <main class="flex-1 relative">
      <HeroSection />

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

      <ComingSoon />
    </main>

    <FooterBar />
  </div>
</template>

<script setup>
import NavBar from './components/NavBar.vue'
import HeroSection from './components/HeroSection.vue'
import UrlInput from './components/UrlInput.vue'
import PlatformIcons from './components/PlatformIcons.vue'
import VideoCard from './components/VideoCard.vue'
import ComingSoon from './components/ComingSoon.vue'
import FooterBar from './components/FooterBar.vue'
import { useVideoDownload } from './composables/useVideoDownload.js'

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
</script>
