<template>
  <div class="px-4 sm:px-6 mb-8 animate-fade-in-up" aria-hidden="true">
    <div class="glass-card overflow-hidden">
      <div class="flex flex-col sm:flex-row">
        <div class="sm:w-64 flex-shrink-0 h-40 sm:h-auto sm:min-h-[9rem] bg-bg-tertiary skeleton-shimmer" />
        <div class="flex-1 p-4 space-y-3">
          <div class="h-4 w-3/4 rounded bg-bg-tertiary skeleton-shimmer" />
          <div class="h-4 w-1/2 rounded bg-bg-tertiary skeleton-shimmer" />
          <div class="flex gap-3 pt-1">
            <div class="h-3 w-20 rounded bg-bg-tertiary skeleton-shimmer" />
            <div class="h-3 w-16 rounded-full bg-bg-tertiary skeleton-shimmer" />
          </div>
        </div>
      </div>
      <div class="border-t border-border/50 p-4">
        <div class="h-3 w-28 rounded bg-bg-tertiary skeleton-shimmer mb-3" />
        <div class="flex flex-wrap gap-2 mb-4">
          <div v-for="i in 5" :key="i" class="h-7 w-20 rounded-lg bg-bg-tertiary skeleton-shimmer" />
        </div>
        <div class="h-12 w-full rounded-xl bg-bg-tertiary skeleton-shimmer" />
      </div>
    </div>
  </div>
</template>
