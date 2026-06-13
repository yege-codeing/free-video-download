import { api, isUnauthorizedResponse } from './client.js'
import { onUnauthorized } from '../composables/authState.js'

/** Extract subtitles/transcript for a video. Throws Error with a friendly message. */
export async function getTranscript(url) {
  const { data } = await api.post('/transcript', { url }, { timeout: 600000 })
  if (data.code !== 0) {
    const err = new Error(data.message || '字幕提取失败')
    err.code = data.code
    throw err
  }
  return data.data
}

export async function getAiStatus() {
  try {
    const { data } = await api.get('/ai-status')
    return !!data?.data?.configured
  } catch {
    return false
  }
}

/**
 * Parse a Server-Sent Events stream from a fetch Response body.
 * Calls onEvent(eventName, dataObject) for each complete event.
 */
async function consumeSSE(response, onEvent) {
  if (isUnauthorizedResponse(response)) {
    onUnauthorized()
    throw new Error('未登录或登录已过期')
  }
  if (!response.ok) {
    let message = '请求失败'
    try {
      const data = await response.json()
      message = data.detail || data.message || message
    } catch {
      /* ignore */
    }
    throw new Error(message)
  }
  if (!response.body) throw new Error('浏览器不支持流式响应')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let sep
    while ((sep = buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = buffer.slice(0, sep)
      buffer = buffer.slice(sep + 2)

      let eventName = 'message'
      const dataLines = []
      for (const line of rawEvent.split('\n')) {
        if (line.startsWith('event:')) eventName = line.slice(6).trim()
        else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
      }
      if (dataLines.length === 0) continue
      let payload = {}
      try {
        payload = JSON.parse(dataLines.join('\n'))
      } catch {
        payload = {}
      }
      onEvent(eventName, payload)
    }
  }
}

/**
 * Stream AI summary. Callbacks:
 *  - onSummaryDelta(text), onStructure({chapters, mindmap}), onError(msg)
 */
export async function streamSummarize(title, segments, handlers = {}) {
  const response = await fetch('/api/summarize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ title, segments }),
  })
  await consumeSSE(response, (name, data) => {
    if (name === 'summary') handlers.onSummaryDelta?.(data.text || '')
    else if (name === 'structure') handlers.onStructure?.(data)
    else if (name === 'error') handlers.onError?.(data.message || 'AI 总结失败')
  })
}

/** Stream a Q&A answer. Callbacks: onDelta(text), onError(msg). */
export async function streamChat(fullText, history, question, handlers = {}) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ full_text: fullText, history, question }),
  })
  await consumeSSE(response, (name, data) => {
    if (name === 'delta') handlers.onDelta?.(data.text || '')
    else if (name === 'error') handlers.onError?.(data.message || 'AI 回答失败')
  })
}
