<template>
  <section class="bg-white border border-carbon-20">
    <!-- Toolbar -->
    <div class="flex flex-wrap items-center justify-between gap-2 px-4 py-2 border-b border-carbon-20">
      <div class="flex items-center gap-4 text-xs">
        <span class="font-medium text-carbon-100 tabular">
          {{ rows.length }} {{ rows.length === 1 ? "entry" : "entries" }} shown
        </span>
        <span v-if="selectedIds.size > 0" class="text-fcc font-medium tabular">
          {{ selectedIds.size }} selected
        </span>
      </div>

      <div class="flex items-center gap-2">
        <button
          v-if="selectedIds.size > 0"
          type="button"
          class="px-2.5 py-1 text-xs bg-fcc text-white hover:bg-fcc-hover cursor-pointer"
          @click="saveSelected"
        >
          Save Selected ({{ selectedIds.size }})
        </button>

        <button
          v-if="hasMore"
          type="button"
          class="px-3 py-1 text-xs border border-carbon-30 text-carbon-100 hover:border-fcc cursor-pointer"
          @click="emit('nextPage')"
        >
          Load Next Page
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse text-xs">
        <thead>
          <tr class="border-b border-carbon-20 bg-carbon-10 text-carbon-60 uppercase text-[11px] tracking-wider">
            <th class="w-9 px-3 py-2">
              <input
                type="checkbox"
                :checked="rows.length > 0 && selectedIds.size === rows.length"
                class="accent-fcc cursor-pointer"
                @change="toggleAll"
              >
            </th>
            <th class="w-9 px-2 py-2" title="Save event">★</th>
            <th class="px-3 py-2 font-semibold">Name / ID</th>
            <th v-for="col in visibleColumns" :key="col" class="px-3 py-2 font-semibold font-mono">
              {{ col }}
            </th>
            <th class="w-16 px-3 py-2 text-right font-semibold">Inspect</th>
          </tr>
        </thead>

        <tbody>
          <tr v-if="loading">
            <td :colspan="visibleColumns.length + 4" class="px-4 py-8 text-center text-carbon-60">
              Querying catalog...
            </td>
          </tr>
          <tr v-else-if="rows.length === 0">
            <td :colspan="visibleColumns.length + 4" class="px-4 py-8 text-center text-carbon-60">
              No matching entries. Adjust your DSL clauses or drop a JSON batch into FileWatcher.
            </td>
          </tr>
          <tr
            v-for="row in rows"
            :key="row.id"
            class="border-b border-carbon-20 hover:bg-carbon-10/60 transition-colors"
          >
            <td class="px-3 py-2">
              <input
                type="checkbox"
                :checked="selectedIds.has(row.id)"
                class="accent-fcc cursor-pointer"
                @change="toggleRow(row.id)"
              >
            </td>
            <td class="px-2 py-2">
              <button
                type="button"
                class="text-sm leading-none cursor-pointer transition-colors"
                :class="isSaved(row.id) ? 'text-fcc' : 'text-carbon-30 hover:text-carbon-60'"
                :title="isSaved(row.id) ? 'Remove from Saved Events' : 'Save event'"
                @click="toggleSave(row)"
              >
                {{ isSaved(row.id) ? "★" : "☆" }}
              </button>
            </td>
            <td class="px-3 py-2">
              <button
                type="button"
                class="text-left hover:text-fcc cursor-pointer"
                @click="emit('inspect', row)"
              >
                <div class="font-medium text-carbon-100">
                  {{ displayName(row) }}
                </div>
                <div class="font-mono text-[10px] text-carbon-50">
                  {{ row.id }}
                </div>
              </button>
            </td>
            <td
              v-for="col in visibleColumns"
              :key="col"
              class="px-3 py-2 font-mono tabular text-carbon-80 max-w-56 truncate"
            >
              {{ formatValue(extractPath(row.metadata, col)) }}
            </td>
            <td class="px-3 py-2 text-right">
              <button
                type="button"
                class="text-xs text-fcc hover:underline cursor-pointer"
                @click="emit('inspect', row)"
              >
                View
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { EntityRow } from "~/types/api";

const props = defineProps<{
  rows: EntityRow[];
  takeColumns: string[];
  loading: boolean;
  hasMore: boolean;
}>();

const emit = defineEmits<{
  inspect: [row: EntityRow];
  nextPage: [];
}>();

const { isSaved, toggleSave, saveMany } = useSavedEvents();
const selectedIds = ref<Set<string>>(new Set());

watch(
  () => props.rows,
  () => {
    selectedIds.value = new Set();
  },
);

const visibleColumns = computed(() => {
  if (props.takeColumns.length > 0) return props.takeColumns;
  const preferred = ["process", "ecm", "campaign", "detector", "generator"];
  const discovered = new Set<string>();
  for (const row of props.rows.slice(0, 10)) {
    for (const key of Object.keys(row.metadata || {})) {
      if (key !== "name") discovered.add(key);
    }
  }
  const ordered = preferred.filter((k) => discovered.has(k));
  for (const k of discovered) {
    if (!ordered.includes(k) && ordered.length < 5) ordered.push(k);
  }
  return ordered;
});

const extractPath = (meta: Record<string, unknown>, dotPath: string): unknown => {
  let cur: unknown = meta;
  for (const seg of dotPath.split(".")) {
    if (cur && typeof cur === "object" && seg in (cur as Record<string, unknown>)) {
      cur = (cur as Record<string, unknown>)[seg];
    } else {
      return undefined;
    }
  }
  return cur;
};

const formatValue = (val: unknown): string => {
  if (val === undefined || val === null) return "—";
  if (typeof val === "object") return JSON.stringify(val);
  return String(val);
};

const displayName = (row: EntityRow): string => {
  const n = row.metadata?.name;
  return typeof n === "string" && n.length > 0 ? n : row.id.slice(0, 8);
};

const toggleRow = (id: string) => {
  const next = new Set(selectedIds.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  selectedIds.value = next;
};

const toggleAll = () => {
  if (selectedIds.value.size === props.rows.length) {
    selectedIds.value = new Set();
  } else {
    selectedIds.value = new Set(props.rows.map((r) => r.id));
  }
};

const saveSelected = () => {
  const chosen = props.rows.filter((r) => selectedIds.value.has(r.id));
  saveMany(chosen);
  selectedIds.value = new Set();
};
</script>
