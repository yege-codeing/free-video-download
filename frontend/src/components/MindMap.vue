<template>
  <div class="relative">
    <div
      ref="wrapper"
      class="mindmap-viewport w-full h-[420px] rounded-xl bg-bg-primary/60 border border-border/40 overflow-hidden cursor-grab active:cursor-grabbing"
    >
      <svg ref="svgRef" class="w-full h-full touch-none select-none"></svg>
    </div>
    <div class="absolute top-2 right-2 flex items-center gap-2">
      <span class="hidden sm:inline text-[10px] text-text-tertiary/80 px-2 py-1 rounded-lg bg-bg-tertiary/60 border border-border/40">
        滚轮缩放 · 拖拽移动
      </span>
      <button
        type="button"
        @click="fit"
        class="text-xs px-2.5 py-1 rounded-lg bg-bg-tertiary/80 border border-border/50 text-text-secondary hover:text-text-primary transition-colors"
      >
        重置视图
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { toPng } from 'html-to-image'
import { Transformer } from 'markmap-lib'
import { Markmap } from 'markmap-view'

const props = defineProps({
  markdown: { type: String, default: '' },
})

const svgRef = ref(null)
const wrapper = ref(null)
let mm = null
const transformer = new Transformer()

const MARKMAP_OPTS = {
  autoFit: true,
  duration: 300,
  paddingX: 16,
  zoom: true,
  pan: false,
  scrollForPan: false,
  color: () => '#FF8585',
  style: (id) => `
    .markmap-${id} .markmap-foreign div,
    .markmap-${id} .markmap-foreign span,
    .markmap-${id} .markmap-foreign p {
      color: #ffffff !important;
    }
  `,
}

function render() {
  if (!svgRef.value || !props.markdown) return
  const { root } = transformer.transform(props.markdown)
  if (!mm) {
    mm = Markmap.create(svgRef.value, MARKMAP_OPTS)
  } else {
    mm.setOptions(MARKMAP_OPTS)
  }
  mm.setData(root)
  mm.fit()
}

function fit() {
  mm?.fit()
}

function downloadDataUrl(dataUrl, filename) {
  const a = document.createElement('a')
  a.href = dataUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

async function waitForLayout() {
  await nextTick()
  await new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(resolve))
  })
}

const TEXT_COLOR = '#ffffff'
const TEXT_SELECTORS = '.markmap-foreign, .markmap-foreign *'

function prepareExportStyles(root) {
  const touched = []
  root.querySelectorAll(TEXT_SELECTORS).forEach((el) => {
    touched.push({
      el,
      color: el.style.color,
      webkitTextFillColor: el.style.webkitTextFillColor,
    })
    el.style.setProperty('color', TEXT_COLOR, 'important')
    el.style.setProperty('-webkit-text-fill-color', TEXT_COLOR, 'important')
  })
  return () => {
    touched.forEach(({ el, color, webkitTextFillColor }) => {
      if (color) el.style.color = color
      else el.style.removeProperty('color')
      if (webkitTextFillColor) el.style.webkitTextFillColor = webkitTextFillColor
      else el.style.removeProperty('-webkit-text-fill-color')
    })
  }
}

async function captureNode(node) {
  const restoreStyles = prepareExportStyles(node)
  try {
    return await toPng(node, {
      cacheBust: true,
      pixelRatio: 2,
      backgroundColor: '#0B0B0F',
    })
  } finally {
    restoreStyles()
  }
}

async function exportPng(filename = '思维导图.png') {
  if (!wrapper.value || !props.markdown) return false

  await waitForLayout()
  await mm?.fit()
  await waitForLayout()

  const { width, height } = wrapper.value.getBoundingClientRect()
  if (width < 1 || height < 1) return false

  try {
    const dataUrl = await captureNode(wrapper.value)
    downloadDataUrl(dataUrl, filename)
    return true
  } catch (wrapperErr) {
    console.warn('Wrapper PNG export failed, retrying SVG node:', wrapperErr)
  }

  if (!svgRef.value) return false

  try {
    const dataUrl = await captureNode(svgRef.value)
    downloadDataUrl(dataUrl, filename)
    return true
  } catch (err) {
    console.error('Mind map PNG export failed:', err)
    return false
  }
}

defineExpose({ exportPng, fit })

onMounted(() => nextTick(render))

watch(
  () => props.markdown,
  () => nextTick(render),
)

onBeforeUnmount(() => {
  if (mm) {
    mm.destroy()
    mm = null
  }
})
</script>

<style scoped>
.mindmap-viewport :deep(.markmap-foreign div),
.mindmap-viewport :deep(.markmap-foreign span),
.mindmap-viewport :deep(.markmap-foreign p) {
  color: #ffffff !important;
}
</style>
