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
      <a href="https://github.com/yt-dlp/yt-dlp" target="_blank" rel="noopener"
         class="focus-ring rounded-lg px-2 py-1 text-text-secondary hover:text-text-primary transition-colors text-sm hidden sm:inline-flex items-center gap-1 cursor-pointer">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
        GitHub
      </a>
    </div>
  </nav>
</template>
