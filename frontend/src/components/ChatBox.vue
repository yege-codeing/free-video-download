<template>
  <div class="flex flex-col">
    <p class="text-text-secondary text-xs mb-3">基于视频字幕追问，AI 仅依据视频内容回答</p>

    <!-- Message list -->
    <div ref="listRef" class="flex-1 max-h-80 overflow-y-auto space-y-3 mb-3 pr-1">
      <div v-if="messages.length === 0" class="text-text-tertiary text-sm text-center py-6">
        还没有提问，试试问"这个视频的核心结论是什么？"
      </div>
      <div v-for="(msg, i) in messages" :key="i"
           :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
        <div :class="[
          'max-w-[85%] rounded-2xl px-3.5 py-2 text-sm whitespace-pre-wrap leading-relaxed',
          msg.role === 'user'
            ? 'bg-accent/15 text-text-primary border border-accent/20'
            : 'bg-bg-tertiary/70 text-text-secondary border border-border/40'
        ]">
          <span v-if="msg.content">{{ msg.content }}</span>
          <span v-else class="inline-flex gap-1 items-center text-text-tertiary">
            思考中
            <span class="animate-pulse">...</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="flex items-center gap-2 bg-bg-tertiary rounded-2xl px-3 py-2 border border-border/40">
      <input
        v-model="input"
        type="text"
        :disabled="streaming"
        placeholder="输入你的问题..."
        class="flex-1 bg-transparent text-text-primary placeholder-text-tertiary outline-none text-sm disabled:opacity-60"
        @keydown.enter="send"
      />
      <button
        type="button"
        :disabled="streaming || !input.trim()"
        class="btn-primary px-4 py-1.5 text-sm"
        @click="send"
      >
        {{ streaming ? '回答中' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  streaming: { type: Boolean, default: false },
})
const emit = defineEmits(['ask'])

const input = ref('')
const listRef = ref(null)

function send() {
  const q = input.value.trim()
  if (!q || props.streaming) return
  emit('ask', q)
  input.value = ''
}

watch(
  () => props.messages.map((m) => m.content).join('|'),
  () => {
    nextTick(() => {
      if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
    })
  },
)
</script>
