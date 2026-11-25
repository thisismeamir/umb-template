<template>
  <header class="h-12 bg-carbon-100 text-white border-b border-carbon-80 flex items-center justify-between px-4 shrink-0 select-none">
    <!-- Left: Institutional Wordmark + Primary Views -->
    <div class="flex items-center gap-6 h-full">
      <div class="flex items-center gap-2.5">
        <span class="w-1.5 h-5 bg-fcc inline-block" aria-hidden="true" />
        <span class="text-xs font-semibold tracking-wider uppercase text-white">FCC</span>
        <span class="text-xs text-carbon-50">/</span>
        <span class="text-xs font-medium tracking-wide text-carbon-20">Universal Metadata Browser</span>
      </div>

      <nav class="flex items-center h-full">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          class="h-full px-3.5 text-xs font-medium transition-colors border-b-2 cursor-pointer flex items-center gap-1.5"
          :class="
            activeView === tab.id
              ? 'border-fcc text-white bg-carbon-90'
              : 'border-transparent text-carbon-30 hover:text-white hover:bg-carbon-90/60'
          "
          @click="emit('update:activeView', tab.id)"
        >
          <span>{{ tab.label }}</span>
          <span
            v-if="tab.id === 'saved' && savedCount > 0"
            class="font-mono tabular text-[10px] px-1.5 py-0.5 bg-fcc text-carbon-100 font-semibold"
          >
            {{ savedCount }}
          </span>
        </button>
      </nav>
    </div>

    <!-- Center: Minimal Global Search -->
    <form class="hidden md:flex items-center w-80 lg:w-96" @submit.prevent="submitSearch">
      <input
        v-model="searchInput"
        type="text"
        placeholder="Full-text search (e.g. Whizard, ee_ZH, 240)..."
        class="w-full h-8 px-3 bg-carbon-90 border border-carbon-80 text-xs text-white placeholder:text-carbon-50 focus:outline-none focus:border-fcc"
      >
      <button
        type="submit"
        class="h-8 px-3 bg-carbon-80 hover:bg-fcc text-xs font-medium text-white transition-colors cursor-pointer"
      >
        Search
      </button>
    </form>

    <!-- Right: Jobs, Export, Auth -->
    <div class="flex items-center gap-2">
      <button
        type="button"
        class="h-8 px-3 text-xs border border-carbon-80 text-carbon-20 hover:border-fcc hover:text-white transition-colors cursor-pointer flex items-center gap-1.5"
        @click="emit('openExport')"
      >
        <span>Export</span>
      </button>

      <button
        type="button"
        class="h-8 px-3 text-xs border border-carbon-80 text-carbon-20 hover:border-fcc hover:text-white transition-colors cursor-pointer flex items-center gap-1.5"
        @click="emit('openJobs')"
      >
        <span>Jobs</span>
        <span
          v-if="activeJobsCount > 0"
          class="font-mono tabular text-[10px] px-1 bg-fcc text-carbon-100 font-semibold"
        >
          {{ activeJobsCount }}
        </span>
      </button>

      <button
        type="button"
        class="h-8 px-3 text-xs bg-carbon-90 border border-carbon-80 text-carbon-20 hover:border-fcc transition-colors cursor-pointer"
        @click="emit('openAuth')"
      >
        <span v-if="!authStatus?.authEnabled" class="text-carbon-30">Public</span>
        <span v-else-if="authStatus.authenticated" class="text-fcc font-mono">
          {{ authStatus.user?.username }}
        </span>
        <span v-else class="text-white">Sign in</span>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import type { AuthStatusResponse } from "~/types/api";

defineProps<{
  activeView: "catalog" | "saved" | "analytics";
  savedCount: number;
  activeJobsCount: number;
  authStatus: AuthStatusResponse | null;
}>();

const emit = defineEmits<{
  "update:activeView": [view: "catalog" | "saved" | "analytics"];
  search: [query: string];
  openExport: [];
  openJobs: [];
  openAuth: [];
}>();

const tabs = [
  { id: "catalog" as const, label: "Catalog" },
  { id: "saved" as const, label: "Saved & Collections" },
  { id: "analytics" as const, label: "Analytics" },
];

const searchInput = ref("");

const submitSearch = () => {
  emit("search", searchInput.value.trim());
};
</script>
