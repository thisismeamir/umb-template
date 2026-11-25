<template>
  <section class="grid grid-cols-1 lg:grid-cols-3 gap-4">
    <!-- Left: Saved Events List -->
    <div class="lg:col-span-2 bg-white border border-carbon-20">
      <div class="px-4 py-3 border-b border-carbon-20 flex items-center justify-between">
        <div>
          <h2 class="text-xs font-semibold uppercase tracking-wider text-carbon-100">
            Saved Events ({{ savedList.length }})
          </h2>
          <p class="text-[11px] text-carbon-60 mt-0.5">
            Star any entry in the Catalog to stage it here, then persist to a server-side Collection or export.
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button
            v-if="savedList.length > 0"
            type="button"
            class="px-2.5 py-1 text-xs border border-carbon-30 text-carbon-80 hover:border-fcc cursor-pointer"
            @click="exportSavedJson"
          >
            Download JSON
          </button>
          <button
            v-if="savedList.length > 0"
            type="button"
            class="px-2.5 py-1 text-xs text-carbon-60 hover:text-red-700 cursor-pointer"
            @click="clearSaved"
          >
            Clear All
          </button>
        </div>
      </div>

      <div v-if="savedList.length === 0" class="p-8 text-center text-xs text-carbon-60">
        No saved events yet. Click ☆ on any row in the Catalog tab.
      </div>

      <div v-else class="divide-y divide-carbon-20">
        <div
          v-for="row in savedList"
          :key="row.id"
          class="px-4 py-2.5 flex items-center justify-between hover:bg-carbon-10/60 text-xs"
        >
          <button type="button" class="text-left hover:text-fcc cursor-pointer" @click="emit('inspect', row)">
            <div class="font-medium text-carbon-100">{{ row.metadata?.name || row.id }}</div>
            <div class="font-mono text-[10px] text-carbon-50">{{ row.id }}</div>
          </button>
          <button
            type="button"
            class="text-xs text-carbon-60 hover:text-red-700 cursor-pointer"
            @click="toggleSave(row)"
          >
            Remove
          </button>
        </div>
      </div>
    </div>

    <!-- Right: Persist to Collection + Collection List -->
    <div class="space-y-4">
      <div class="bg-white border border-carbon-20 p-4 space-y-3">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-carbon-100">
          Save List as Collection
        </h3>
        <input
          v-model="newName"
          type="text"
          placeholder="Collection name (e.g. ZH 240 GeV)"
          class="w-full h-8 px-2.5 text-xs border border-carbon-30 focus:outline-none focus:border-fcc"
        >
        <input
          v-model="newDesc"
          type="text"
          placeholder="Short description (optional)"
          class="w-full h-8 px-2.5 text-xs border border-carbon-30 focus:outline-none focus:border-fcc"
        >
        <label class="flex items-center gap-2 text-xs text-carbon-80 cursor-pointer">
          <input v-model="newPublic" type="checkbox" class="accent-fcc">
          <span>Make public to other users</span>
        </label>
        <button
          type="button"
          class="w-full h-8 text-xs font-medium bg-fcc hover:bg-fcc-hover text-white cursor-pointer disabled:opacity-50"
          :disabled="!newName.trim() || creating"
          @click="handleCreate"
        >
          {{ creating ? "Saving..." : `Create Collection (${savedList.length} events)` }}
        </button>
        <p v-if="colMessage" class="text-[11px] font-mono text-carbon-80">{{ colMessage }}</p>
      </div>

      <div class="bg-white border border-carbon-20">
        <div class="px-4 py-2.5 border-b border-carbon-20 text-xs font-semibold uppercase tracking-wider text-carbon-100">
          Server Collections ({{ collections.length }})
        </div>
        <div v-if="collections.length === 0" class="p-4 text-xs text-carbon-60">
          No collections yet.
        </div>
        <div v-else class="divide-y divide-carbon-20 text-xs">
          <div
            v-for="col in collections"
            :key="col.id"
            class="px-4 py-2.5 flex items-center justify-between"
          >
            <div>
              <div class="font-medium text-carbon-100">{{ col.name }}</div>
              <div class="text-[11px] font-mono text-carbon-60">
                {{ col.memberCount }} events · {{ col.isPublic ? "public" : "private" }}
              </div>
            </div>
            <button
              type="button"
              class="text-[11px] text-carbon-60 hover:text-red-700 cursor-pointer"
              @click="removeCollection(col.id)"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { EntityRow } from "~/types/api";

const emit = defineEmits<{
  inspect: [row: EntityRow];
}>();

const {
  savedList,
  collections,
  toggleSave,
  clearSaved,
  createCollectionFromSaved,
  removeCollection,
} = useSavedEvents();

const newName = ref("");
const newDesc = ref("");
const newPublic = ref(false);
const creating = ref(false);
const colMessage = ref("");

const handleCreate = async () => {
  creating.value = true;
  colMessage.value = "";
  try {
    const created = await createCollectionFromSaved(newName.value.trim(), newDesc.value.trim(), newPublic.value);
    colMessage.value = `Saved collection '${created.name}'.`;
    newName.value = "";
    newDesc.value = "";
  } catch (e: unknown) {
    colMessage.value = (e as { message?: string })?.message || "Failed to save collection (sign in if auth is enabled).";
  } finally {
    creating.value = false;
  }
};

const exportSavedJson = () => {
  const blob = new Blob([JSON.stringify(savedList.value, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "umb_saved_events.json";
  a.click();
  URL.revokeObjectURL(url);
};
</script>
