<template>
  <div class="demo-frame mx-4 sm:mx-6 mb-10">
    <div class="demo-chrome">
      <div class="demo-chrome-dots" aria-hidden="true">
        <span class="demo-dot demo-dot-red" />
        <span class="demo-dot demo-dot-yellow" />
        <span class="demo-dot demo-dot-green" />
      </div>
      <div class="demo-chrome-url">
        <svg class="w-3.5 h-3.5 text-text-tertiary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        <span class="truncate">saveany.app/demo</span>
      </div>
      <span class="demo-chrome-badge">Live Demo</span>
    </div>
    <div class="demo-viewport">
      <slot />
    </div>
  </div>
</template>
