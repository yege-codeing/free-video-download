<template>
  <nav class="fixed top-4 left-4 right-4 z-50 max-w-5xl mx-auto rounded-xl border border-border/60 bg-bg-secondary/90 backdrop-blur-md shadow-lg shadow-black/20">
    <div class="flex items-center gap-3 px-4 h-12">
      <div class="demo-chrome-dots hidden sm:flex" aria-hidden="true">
        <span class="demo-dot demo-dot-red" />
        <span class="demo-dot demo-dot-yellow" />
        <span class="demo-dot demo-dot-green" />
      </div>
      <div class="flex items-center gap-2 flex-1 min-w-0">
        <div class="w-7 h-7 rounded-lg gradient-bg flex items-center justify-center flex-shrink-0">
          <svg class="w-4 h-4 text-bg-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 3l14 9-14 9V3z" />
          </svg>
        </div>
        <span class="text-base font-bold gradient-text">SaveAny</span>
        <span class="demo-chrome-badge hidden md:inline">Live Demo</span>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="username" class="text-base font-bold gradient-text hidden sm:inline">{{ username }}</span>
        <button
          v-if="username"
          type="button"
          class="focus-ring rounded-lg px-2 py-1 text-base font-bold gradient-text cursor-pointer"
          @click="$emit('logout')"
        >
          退出
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
defineProps({
  username: { type: String, default: '' },
})

defineEmits(['logout'])
</script>
