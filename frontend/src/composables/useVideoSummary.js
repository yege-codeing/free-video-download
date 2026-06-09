import { ref } from 'vue'
import { getTranscript, streamSummarize, streamChat } from '../api/summary.js'

export function useVideoSummary() {
  const summaryUrl = ref('')
  const transcript = ref(null)
  const loadingTranscript = ref(false)
  const error = ref('')

  const summary = ref('')
  const chapters = ref([])
  const mindmap = ref('')
  const summarizing = ref(false)
  const summarized = ref(false)

  const chatMessages = ref([]) // { role: 'user'|'assistant', content }
  const chatStreaming = ref(false)

  async function handleGetTranscript() {
    const url = summaryUrl.value.trim()
    if (!url) {
      error.value = '请输入视频链接'
      return
    }
    error.value = ''
    transcript.value = null
    summary.value = ''
    chapters.value = []
    mindmap.value = ''
    summarized.value = false
    chatMessages.value = []
    loadingTranscript.value = true

    try {
      const data = await getTranscript(url)
      transcript.value = data
      // Auto-trigger summarization once the transcript is ready.
      await handleSummarize()
    } catch (e) {
      error.value = e.message || '字幕提取失败，请检查链接或更换视频'
    } finally {
      loadingTranscript.value = false
    }
  }

  async function handleSummarize() {
    if (!transcript.value || summarizing.value) return
    summarizing.value = true
    summary.value = ''
    chapters.value = []
    mindmap.value = ''
    error.value = ''

    try {
      await streamSummarize(
        transcript.value.title,
        transcript.value.segments,
        {
          onSummaryDelta: (text) => {
            summary.value += text
          },
          onStructure: (data) => {
            chapters.value = data.chapters || []
            mindmap.value = data.mindmap || ''
          },
          onError: (msg) => {
            error.value = msg
          },
        },
      )
      summarized.value = true
    } catch (e) {
      error.value = e.message || 'AI 总结失败'
    } finally {
      summarizing.value = false
    }
  }

  async function handleAsk(question) {
    const q = (question || '').trim()
    if (!q || !transcript.value || chatStreaming.value) return

    chatMessages.value.push({ role: 'user', content: q })
    const assistantMsg = { role: 'assistant', content: '' }
    chatMessages.value.push(assistantMsg)
    chatStreaming.value = true

    // Send prior turns (exclude the just-added empty assistant turn).
    const history = chatMessages.value.slice(0, -1).map((m) => ({
      role: m.role,
      content: m.content,
    }))

    try {
      await streamChat(transcript.value.full_text, history.slice(0, -1), q, {
        onDelta: (text) => {
          assistantMsg.content += text
        },
        onError: (msg) => {
          assistantMsg.content = msg
        },
      })
    } catch (e) {
      assistantMsg.content = e.message || 'AI 回答失败'
    } finally {
      chatStreaming.value = false
    }
  }

  function reset() {
    summaryUrl.value = ''
    transcript.value = null
    loadingTranscript.value = false
    error.value = ''
    summary.value = ''
    chapters.value = []
    mindmap.value = ''
    summarizing.value = false
    summarized.value = false
    chatMessages.value = []
    chatStreaming.value = false
  }

  return {
    summaryUrl,
    transcript,
    loadingTranscript,
    error,
    summary,
    chapters,
    mindmap,
    summarizing,
    summarized,
    chatMessages,
    chatStreaming,
    handleGetTranscript,
    handleSummarize,
    handleAsk,
    reset,
  }
}
