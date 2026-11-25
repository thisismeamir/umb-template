<template>
  <div v-if="entity" class="fixed inset-0 z-40 flex justify-end bg-carbon-100/30" @click.self="emit('close')">
    <aside class="w-full max-w-xl bg-white h-full border-l border-carbon-20 flex flex-col">
      <!-- Header -->
      <div class="px-5 py-3.5 border-b border-carbon-20 flex items-start justify-between gap-4">
        <div class="min-w-0">
          <div class="text-sm font-semibold text-carbon-100 truncate">
            {{ entity.metadata?.name || entity.id }}
          </div>
          <div class="font-mono text-[11px] text-carbon-60 truncate mt-0.5">
            {{ entity.id }}
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button
            type="button"
            class="px-2.5 py-1 text-xs border cursor-pointer transition-colors"
            :class="
              isSaved(entity.id)
                ? 'border-fcc bg-fcc-soft text-carbon-100'
                : 'border-carbon-30 text-carbon-80 hover:border-fcc'
            "
            @click="toggleSave(entity)"
          >
            {{ isSaved(entity.id) ? "★ Saved" : "☆ Save" }}
          </button>
          <button
            type="button"
            class="px-2 py-1 text-sm text-carbon-60 hover:text-carbon-100 cursor-pointer"
            @click="emit('close')"
          >
            ×
          </button>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex border-b border-carbon-20 px-5 text-xs">
        <button
          v-for="t in ['metadata', 'versions', 'similar'] as const"
          :key="t"
          type="button"
          class="py-2.5 mr-6 border-b-2 capitalize font-medium cursor-pointer"
          :class="tab === t ? 'border-fcc text-carbon-100' : 'border-transparent text-carbon-60 hover:text-carbon-100'"
          @click="selectTab(t)"
        >
          {{ t }}
        </button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto p-5 text-xs">
        <!-- Metadata Leaf Explorer -->
        <div v-if="tab === 'metadata'" class="space-y-1.5">
          <p class="text-[11px] text-carbon-60 mb-3">
            Click <span class="font-mono text-fcc">+where</span> or <span class="font-mono text-fcc">+take</span> on any field to add it directly to the DSL workbench.
          </p>
          <div
            v-for="item in flatLeaves"
            :key="item.path"
            class="flex items-start justify-between gap-3 py-1.5 border-b border-carbon-10"
          >
            <div class="min-w-0">
              <div class="font-mono text-[11px] text-carbon-60">{{ item.path }}</div>
              <div class="font-mono text-xs text-carbon-100 break-all mt-0.5">{{ item.value }}</div>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <button
                type="button"
                class="px-1.5 py-0.5 text-[10px] font-mono border border-carbon-20 text-carbon-80 hover:border-fcc hover:text-fcc cursor-pointer"
                @click="emit('addWhere', item.path, `=${item.value}`)"
              >
                +where
              </button>
              <button
                type="button"
                class="px-1.5 py-0.5 text-[10px] font-mono border border-carbon-20 text-carbon-80 hover:border-fcc hover:text-fcc cursor-pointer"
                @click="emit('addTake', item.path)"
              >
                +take
              </button>
            </div>
          </div>
        </div>

        <!-- Version History -->
        <div v-else-if="tab === 'versions'" class="space-y-2">
          <div v-if="loadingTab" class="text-carbon-60">Loading versions...</div>
          <div v-else-if="versions.length === 0" class="text-carbon-60">No version history returned.</div>
          <div
            v-for="v in versions"
            :key="v.version"
            class="p-3 border border-carbon-20 flex items-center justify-between"
          >
            <div>
              <div class="font-mono font-medium text-carbon-100">v{{ v.version }} · {{ v.source }}</div>
              <div class="text-[11px] text-carbon-60 mt-0.5">by {{ v.createdBy }}</div>
            </div>
            <div class="font-mono text-[11px] text-carbon-60 tabular">{{ v.createdAt }}</div>
          </div>
        </div>

        <!-- Similar Datasets -->
        <div v-else class="space-y-2">
          <div v-if="loadingTab" class="text-carbon-60">Finding similar entries...</div>
          <div v-else-if="similarHits.length === 0" class="text-carbon-60">No similar entries found.</div>
          <div
            v-for="hit in similarHits"
            :key="hit.id"
            class="p-3 border border-carbon-20 hover:border-fcc cursor-pointer"
            @click="emit('selectEntity', { id: hit.id, metadata: hit.metadata, entry_type: hit.entryType })"
          >
            <div class="flex items-center justify-between">
              <span class="font-medium text-carbon-100">{{ hit.metadata?.name || hit.id }}</span>
              <span class="font-mono tabular text-fcc">{{ hit.score.toFixed(2) }}</span>
            </div>
            <div class="text-[11px] font-mono text-carbon-60 mt-1">
              Matched: {{ hit.matchedFields.join(", ") || "—" }}
            </div>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import type { EntityRow, SearchHit, VersionSummary } from "~/types/api";

const props = defineProps<{
  entity: EntityRow | null;
}>();

const emit = defineEmits<{
  close: [];
  addWhere: [path: string, expr: string];
  addTake: [path: string];
  selectEntity: [row: EntityRow];
}>();

const api = useUmbApi();
const { isSaved, toggleSave } = useSavedEvents();

const tab = ref<"metadata" | "versions" | "similar">("metadata");
const loadingTab = ref(false);
const versions = ref<VersionSummary[]>([]);
const similarHits = ref<SearchHit[]>([]);

watch(
  () => props.entity?.id,
  () => {
    tab.value = "metadata";
    versions.value = [];
    similarHits.value = [];
  },
);

const flatten = (obj: unknown, prefix = ""): Array<{ path: string; value: string }> => {
  if (!obj || typeof obj !== "object") return [];
  const out: Array<{ path: string; value: string }> = [];
  for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
    const p = prefix ? `${prefix}.${k}` : k;
    if (v !== null && typeof v === "object" && !Array.isArray(v)) {
      out.push(...flatten(v, p));
    } else {
      out.push({ path: p, value: Array.isArray(v) ? JSON.stringify(v) : String(v ?? "null") });
    }
  }
  return out;
};

const flatLeaves = computed(() => flatten(props.entity?.metadata || {}));

const selectTab = async (next: "metadata" | "versions" | "similar") => {
  tab.value = next;
  if (!props.entity) return;
  if (next === "versions" && versions.value.length === 0) {
    loadingTab.value = true;
    try {
      const res = await api.getEntity({ id: props.entity.id, versions: { last: 20 } });
      versions.value = res.versions || [];
    } catch {
      versions.value = [];
    } finally {
      loadingTab.value = false;
    }
  } else if (next === "similar" && similarHits.value.length === 0) {
    loadingTab.value = true;
    try {
      const res = await api.searchSimilar(props.entity.id, 10);
      similarHits.value = res.hits;
    } catch {
      similarHits.value = [];
    } finally {
      loadingTab.value = false;
    }
  }
};
</script>
