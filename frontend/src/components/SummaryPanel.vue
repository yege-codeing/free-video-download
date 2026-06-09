<template>
  <div class="px-4 mb-8 animate-fade-in-up">
    <div class="glass-card overflow-hidden">
      <!-- Header: thumbnail + meta -->
      <div class="flex flex-col sm:flex-row">
        <div class="sm:w-56 flex-shrink-0 relative overflow-hidden bg-bg-primary">
          <img v-if="info.thumbnail" :src="info.thumbnail" :alt="info.title"
               class="w-full h-36 sm:h-full object-cover" referrerpolicy="no-referrer" />
          <span v-if="info.duration_str" class="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-0.5 rounded">
            {{ info.duration_str }}
          </span>
        </div>
        <div class="flex-1 p-4">
          <h3 class="font-bold text-base text-text-primary mb-2 line-clamp-2 leading-snug">{{ info.title }}</h3>
          <div class="flex flex-wrap items-center gap-2 text-xs text-text-secondary">
            <span>{{ info.author }}</span>
            <span v-if="info.platform_label" class="px-2 py-0.5 rounded-full bg-bg-tertiary border border-border/50">
              {{ info.platform_label }}
            </span>
            <span v-if="info.source_label" class="px-2 py-0.5 rounded-full bg-accent/10 border border-accent/25 text-accent">
              {{ info.source_label }}
            </span>
            <span v-if="info.language" class="px-2 py-0.5 rounded-full bg-bg-tertiary border border-border/50">
              {{ info.language }}
            </span>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="border-t border-border/50 px-4 pt-3">
        <div class="flex items-center gap-1 overflow-x-auto">
          <button
            v-for="tab in tabs" :key="tab.id"
            type="button"
            @click="activeTab = tab.id"
            :class="[
              'px-3.5 py-2 text-sm rounded-t-lg whitespace-nowrap transition-colors border-b-2',
              activeTab === tab.id
                ? 'text-accent border-accent font-medium'
                : 'text-text-secondary border-transparent hover:text-text-primary'
            ]"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>

      <!-- Tab content -->
      <div class="p-4">
        <!-- Summary -->
        <div v-show="activeTab === 'summary'">
          <div v-if="summary" class="md-body" v-html="summaryHtml"></div>
          <div v-else class="text-text-tertiary text-sm py-8 text-center">
            <span v-if="summarizing" class="inline-flex items-center gap-2">
              <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              AI 正在生成总结...
            </span>
            <span v-else>暂无总结</span>
          </div>
          <TabActions
            :can-act="!!summary"
            copy-label="复制总结"
            export-label="导出总结"
            :copied="copiedTab === 'summary'"
            @copy="copyTab('summary')"
            @export="exportTab('summary')"
          />
        </div>

        <!-- Chapters -->
        <div v-show="activeTab === 'chapters'">
          <div v-if="chapters.length" class="space-y-2">
            <a
              v-for="(ch, i) in chapters" :key="i"
              :href="jumpUrl(ch.start)" target="_blank" rel="noopener"
              class="block p-3 rounded-xl bg-bg-tertiary/50 border border-border/40 hover:border-accent/30 transition-colors group"
            >
              <div class="flex items-center gap-2 mb-1">
                <span class="text-xs font-mono px-1.5 py-0.5 rounded bg-accent/15 text-accent">{{ ch.time }}</span>
                <span class="text-sm font-medium text-text-primary group-hover:text-accent transition-colors">{{ ch.title }}</span>
              </div>
              <p v-if="ch.summary" class="text-xs text-text-secondary leading-relaxed">{{ ch.summary }}</p>
            </a>
          </div>
          <div v-else class="text-text-tertiary text-sm py-8 text-center">
            {{ summarizing ? '正在生成章节...' : '暂无章节' }}
          </div>
          <TabActions
            :can-act="chapters.length > 0"
            copy-label="复制章节"
            export-label="导出章节"
            :copied="copiedTab === 'chapters'"
            @copy="copyTab('chapters')"
            @export="exportTab('chapters')"
          />
        </div>

        <!-- Transcript -->
        <div v-show="activeTab === 'transcript'">
          <div v-if="info.segments && info.segments.length" class="max-h-96 overflow-y-auto space-y-1.5 pr-1">
            <div v-for="(seg, i) in info.segments" :key="i" class="flex gap-3 text-sm">
              <a :href="jumpUrl(seg.t)" target="_blank" rel="noopener"
                 class="text-xs font-mono text-text-tertiary hover:text-accent pt-0.5 flex-shrink-0 w-14">{{ fmtTs(seg.t) }}</a>
              <span class="text-text-secondary leading-relaxed">{{ seg.text }}</span>
            </div>
          </div>
          <div v-else class="text-text-tertiary text-sm py-8 text-center">暂无转录</div>
          <TabActions
            :can-act="!!(info.segments && info.segments.length)"
            copy-label="复制转录"
            export-label="导出转录"
            :copied="copiedTab === 'transcript'"
            @copy="copyTab('transcript')"
            @export="exportTab('transcript')"
          />
        </div>

        <!-- Mind map -->
        <div v-show="activeTab === 'mindmap'">
          <MindMap v-if="mindmap" ref="mindmapRef" :markdown="mindmap" />
          <div v-else class="text-text-tertiary text-sm py-8 text-center">
            {{ summarizing ? '正在生成思维导图...' : '暂无思维导图' }}
          </div>
          <p v-if="exportError" class="mt-3 text-xs text-accent">{{ exportError }}</p>
          <TabActions
            :can-act="!!mindmap"
            copy-label="复制导图"
            export-label="导出 PNG"
            :copied="copiedTab === 'mindmap'"
            @copy="copyTab('mindmap')"
            @export="exportMindmapPng"
          />
        </div>

        <!-- AI chat -->
        <div v-show="activeTab === 'chat'">
          <ChatBox :messages="chatMessages" :streaming="chatStreaming" @ask="$emit('ask', $event)" />
          <TabActions
            :can-act="chatMessages.length > 0"
            copy-label="复制对话"
            export-label="导出对话"
            :copied="copiedTab === 'chat'"
            @copy="copyTab('chat')"
            @export="exportTab('chat')"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { marked } from 'marked'
import MindMap from './MindMap.vue'
import ChatBox from './ChatBox.vue'
import TabActions from './TabActions.vue'

const props = defineProps({
  info: { type: Object, required: true },
  summary: { type: String, default: '' },
  chapters: { type: Array, default: () => [] },
  mindmap: { type: String, default: '' },
  summarizing: { type: Boolean, default: false },
  chatMessages: { type: Array, default: () => [] },
  chatStreaming: { type: Boolean, default: false },
})
defineEmits(['ask'])

const tabs = [
  { id: 'summary', label: '总结' },
  { id: 'chapters', label: '章节' },
  { id: 'transcript', label: '转录' },
  { id: 'mindmap', label: '思维导图' },
  { id: 'chat', label: 'AI 追问' },
]
const activeTab = ref('summary')
const copiedTab = ref('')
const mindmapRef = ref(null)

const TAB_SUFFIX = {
  summary: '总结',
  chapters: '章节',
  transcript: '转录',
  mindmap: '思维导图',
  chat: 'AI追问',
}

const summaryHtml = computed(() => marked.parse(props.summary || ''))

function fmtTs(seconds) {
  const s = Math.max(0, Math.floor(seconds || 0))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  const pad = (n) => String(n).padStart(2, '0')
  return h > 0 ? `${pad(h)}:${pad(m)}:${pad(sec)}` : `${pad(m)}:${pad(sec)}`
}

function jumpUrl(start) {
  const base = props.info.webpage_url || ''
  const t = Math.max(0, Math.floor(start || 0))
  if (!base) return '#'
  try {
    const u = new URL(base)
    if (u.hostname.includes('youtube.com') || u.hostname.includes('youtu.be')) {
      u.searchParams.set('t', `${t}s`)
    } else {
      u.searchParams.set('t', String(t))
    }
    return u.toString()
  } catch {
    return base
  }
}

function metaHeader() {
  const lines = [`# ${props.info.title || '视频总结'}`, '']
  if (props.info.author) lines.push(`> 作者：${props.info.author}`, '')
  if (props.info.webpage_url) lines.push(`> 链接：${props.info.webpage_url}`, '')
  return lines
}

function buildTabText(tab) {
  switch (tab) {
    case 'summary':
      return props.summary || ''
    case 'chapters':
      if (!props.chapters.length) return ''
      return props.chapters
        .map((ch) => `- **${ch.time}** ${ch.title}${ch.summary ? ` — ${ch.summary}` : ''}`)
        .join('\n')
    case 'transcript':
      if (!props.info.segments?.length) return ''
      return props.info.segments
        .map((seg) => `[${fmtTs(seg.t)}] ${seg.text}`)
        .join('\n')
    case 'mindmap':
      return props.mindmap || ''
    case 'chat':
      if (!props.chatMessages.length) return ''
      return props.chatMessages
        .map((m) => `**${m.role === 'user' ? '我' : 'AI'}**：${m.content}`)
        .join('\n\n')
    default:
      return ''
  }
}

function buildTabMarkdown(tab) {
  const suffix = TAB_SUFFIX[tab] || tab
  const lines = [...metaHeader(), `## ${suffix}`, '']
  const body = buildTabText(tab)
  if (body) lines.push(body)
  return lines.join('\n').trim() + '\n'
}

async function copyTab(tab) {
  const text = tab === 'summary' || tab === 'mindmap'
    ? buildTabText(tab)
    : buildTabMarkdown(tab)
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    copiedTab.value = tab
    setTimeout(() => {
      if (copiedTab.value === tab) copiedTab.value = ''
    }, 1500)
  } catch {
    /* ignore */
  }
}

function exportTab(tab) {
  const content = buildTabMarkdown(tab)
  if (!content.trim()) return
  const suffix = TAB_SUFFIX[tab] || tab
  const safeTitle = (props.info.title || '视频').slice(0, 40).replace(/[\\/:*?"<>|]/g, '_')
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${safeTitle}-${suffix}.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const exportError = ref('')

async function exportMindmapPng() {
  if (!props.mindmap) return
  exportError.value = ''
  activeTab.value = 'mindmap'
  await nextTick()
  await new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(resolve))
  })

  const safeTitle = (props.info.title || '视频').slice(0, 40).replace(/[\\/:*?"<>|]/g, '_')
  const ok = await mindmapRef.value?.exportPng?.(`${safeTitle}-思维导图.png`)
  if (!ok) {
    exportError.value = '导出失败，请稍后重试'
  }
}
</script>
