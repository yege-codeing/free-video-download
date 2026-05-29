import { ref } from 'vue'
import { parseVideo, fetchDownloadVideo } from '../api/video.js'

export function useVideoDownload() {
  const videoUrl = ref('')
  const videoInfo = ref(null)
  const selectedFormat = ref(null)
  const loading = ref(false)
  const downloading = ref(false)
  const downloadProgress = ref(0)
  /** idle | processing | transferring | saving */
  const downloadPhase = ref('idle')
  const error = ref('')

  let prepTimer = null

  function startPrepProgress() {
    downloadProgress.value = 5
    prepTimer = setInterval(() => {
      // Server is still running yt-dlp — creep toward 97% so UI never looks frozen
      const p = downloadProgress.value
      if (p >= 97) return
      const step = p < 50 ? 3 : p < 80 ? 1.5 : 0.4
      downloadProgress.value = Math.min(97, Math.round((p + step) * 10) / 10)
    }, 600)
  }

  function stopPrepProgress() {
    if (prepTimer) {
      clearInterval(prepTimer)
      prepTimer = null
    }
  }

  function setProgress(pct) {
    downloadProgress.value = Math.max(downloadProgress.value, pct)
  }

  async function handleParse() {
    const url = videoUrl.value.trim()
    if (!url) {
      error.value = '请输入视频链接'
      return
    }

    error.value = ''
    videoInfo.value = null
    selectedFormat.value = null
    loading.value = true

    try {
      const info = await parseVideo(url)
      videoInfo.value = info
      if (info.formats && info.formats.length > 0) {
        selectedFormat.value = info.formats[0].format_id
      }
    } catch (e) {
      error.value = e.message || '解析失败，请检查链接是否正确'
    } finally {
      loading.value = false
    }
  }

  function selectFormat(formatId) {
    if (downloading.value) return
    selectedFormat.value = formatId
  }

  async function handleDownload() {
    if (!videoInfo.value || !selectedFormat.value || downloading.value) return

    downloading.value = true
    downloadProgress.value = 0
    downloadPhase.value = 'processing'
    error.value = ''
    startPrepProgress()

    try {
      const { blob, filename } = await fetchDownloadVideo(
        videoUrl.value.trim(),
        selectedFormat.value,
        {
          onPhase: (phase) => {
            if (phase === 'transferring' || phase === 'saving') {
              stopPrepProgress()
            }
            downloadPhase.value = phase
          },
          onProgress: (pct) => {
            stopPrepProgress()
            setProgress(pct)
          },
        },
      )

      const blobUrl = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = filename
      a.style.display = 'none'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(blobUrl)
    } catch (e) {
      error.value = e.message || '下载失败'
    } finally {
      stopPrepProgress()
      downloading.value = false
      downloadProgress.value = 0
      downloadPhase.value = 'idle'
    }
  }

  function reset() {
    stopPrepProgress()
    videoUrl.value = ''
    videoInfo.value = null
    selectedFormat.value = null
    loading.value = false
    downloading.value = false
    downloadProgress.value = 0
    downloadPhase.value = 'idle'
    error.value = ''
  }

  return {
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
  }
}
