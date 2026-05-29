import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export async function parseVideo(url) {
  // Bilibili parse can exceed default 30s axios timeout
  const { data } = await api.post('/parse', { url }, { timeout: 120000 })
  if (data.code !== 0) {
    throw new Error(data.message || '解析失败')
  }
  return data.data
}

function parseFilename(contentDisposition) {
  if (!contentDisposition) return 'video.mp4'
  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;\s]+)/i)
  if (utf8Match) {
    try {
      return decodeURIComponent(utf8Match[1])
    } catch {
      return utf8Match[1]
    }
  }
  const plainMatch = contentDisposition.match(/filename="?([^";\n]+)"?/i)
  return plainMatch ? plainMatch[1].trim() : 'video.mp4'
}

/**
 * Fetch video file from backend with progress callbacks.
 * Server blocks until yt-dlp finishes — phase "processing" covers that wait.
 */
export async function fetchDownloadVideo(url, formatId, { onProgress, onPhase } = {}) {
  const params = new URLSearchParams({ url, format_id: formatId })
  onPhase?.('processing')

  const response = await fetch(`/api/download?${params.toString()}`)

  if (!response.ok) {
    let message = '下载失败'
    try {
      const data = await response.json()
      message = data.detail || data.message || message
    } catch {
      const text = await response.text().catch(() => '')
      if (text) message = text
    }
    throw new Error(message)
  }

  onPhase?.('transferring')
  onProgress?.(90)

  const total = parseInt(response.headers.get('Content-Length') || '0', 10)
  if (!response.body) {
    throw new Error('浏览器不支持流式下载')
  }

  const reader = response.body.getReader()
  const chunks = []
  let received = 0
  let streamPct = 90

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    chunks.push(value)
    received += value.length

    if (onProgress) {
      if (total > 0) {
        streamPct = 90 + Math.round((received / total) * 9)
      } else if (received > streamPct) {
        // No Content-Length: advance slowly by bytes received (~2% per 5MB)
        streamPct = Math.min(99, 90 + Math.floor(received / (5 * 1024 * 1024)) * 2)
      }
      onProgress(Math.min(99, streamPct))
    }
  }

  const blob = new Blob(chunks)
  const filename = parseFilename(response.headers.get('Content-Disposition'))
  onPhase?.('saving')
  onProgress?.(100)
  return { blob, filename }
}

export async function getPlatforms() {
  const { data } = await api.get('/platforms')
  return data.data
}
