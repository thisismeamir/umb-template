<template>
  <aside class="w-60 bg-white border-r border-carbon-20 flex flex-col shrink-0 overflow-y-auto">
    <!-- Physics Navigation Facets -->
    <div class="p-3 border-b border-carbon-20">
      <div class="flex items-center justify-between mb-2">
        <span class="text-[11px] font-semibold uppercase tracking-wider text-carbon-60">Navigation Facets</span>
        <button
          type="button"
          class="text-[11px] text-fcc hover:underline cursor-pointer"
          @click="loadFacets"
        >
          Refresh
        </button>
      </div>

      <div v-for="cat in categories" :key="cat.key" class="mb-2.5">
        <button
          type="button"
          class="w-full flex items-center justify-between py-1 text-xs font-medium text-carbon-100 hover:text-fcc cursor-pointer"
          @click="toggleCat(cat.key)"
        >
          <span>{{ cat.label }}</span>
          <span class="font-mono text-[10px] text-carbon-60">
            {{ openCats[cat.key] ? "−" : "+" }}
          </span>
        </button>

        <div v-if="openCats[cat.key]" class="mt-1 space-y-0.5 pl-2 border-l border-carbon-20">
          <div v-if="(facets[cat.key] || []).length === 0" class="text-[11px] text-carbon-50 py-1">
            No entries
          </div>
          <button
            v-for="item in facets[cat.key] || []"
            :key="item.name"
            type="button"
            class="w-full flex items-center justify-between px-2 py-1 text-xs text-left transition-colors cursor-pointer"
            :class="
              activeFilterKey === `${cat.field}:${item.name}`
                ? 'bg-fcc-soft text-carbon-100 font-medium border-l-2 border-fcc -ml-[9px] pl-[15px]'
                : 'text-carbon-80 hover:bg-carbon-10'
            "
            @click="selectFacet(cat.field, item.name)"
          >
            <span class="truncate">{{ item.name }}</span>
            <span class="font-mono tabular text-[11px] text-carbon-60 ml-2">{{ item.count }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Discovered Field Registry -->
    <div class="p-3 border-b border-carbon-20">
      <div class="text-[11px] font-semibold uppercase tracking-wider text-carbon-60 mb-2">
        Field Registry ({{ fields.length }})
      </div>
      <div class="max-h-44 overflow-y-auto space-y-0.5">
        <button
          v-for="f in fields"
          :key="`${f.entryType}:${f.key}`"
          type="button"
          class="w-full flex items-center justify-between px-2 py-1 text-xs text-carbon-80 hover:bg-carbon-10 cursor-pointer"
          :title="`Click to add '${f.key}' to DSL filter`"
          @click="emit('pickField', f.key)"
        >
          <span class="font-mono truncate">{{ f.key }}</span>
          <span class="text-[10px] font-mono text-carbon-50">{{ f.valueType }}</span>
        </button>
      </div>
    </div>

    <!-- Saved Events & Collections Quick Access -->
    <div class="p-3 flex-1">
      <div class="flex items-center justify-between mb-2">
        <span class="text-[11px] font-semibold uppercase tracking-wider text-carbon-60">Collections</span>
        <span class="font-mono tabular text-[11px] text-carbon-60">{{ collections.length }}</span>
      </div>

      <button
        type="button"
        class="w-full flex items-center justify-between px-2 py-1.5 text-xs text-carbon-100 hover:bg-carbon-10 border border-carbon-20 mb-2 cursor-pointer"
        @click="emit('openSaved')"
      >
        <span class="font-medium">Saved Events</span>
        <span class="font-mono tabular text-[11px] text-fcc font-semibold">{{ savedCount }}</span>
      </button>

      <div class="space-y-0.5">
        <button
          v-for="col in collections"
          :key="col.id"
          type="button"
          class="w-full flex items-center justify-between px-2 py-1 text-xs text-carbon-80 hover:bg-carbon-10 cursor-pointer"
          @click="emit('openCollection', col.id)"
        >
          <span class="truncate">{{ col.name }}</span>
          <span class="font-mono tabular text-[11px] text-carbon-60">{{ col.memberCount }}</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import type { CollectionSummary, FieldRegistryEntry, NavigationItem } from "~/types/api";

defineProps<{
  fields: FieldRegistryEntry[];
  collections: CollectionSummary[];
  savedCount: number;
}>();

const emit = defineEmits<{
  filterFacet: [field: string, value: string];
  pickField: [fieldKey: string];
  openSaved: [];
  openCollection: [id: string];
}>();

const api = useUmbApi();

const categories = [
  { key: "campaigns" as const, field: "campaign", label: "Campaigns" },
  { key: "detectors" as const, field: "detector", label: "Detectors" },
  { key: "accelerators" as const, field: "accelerator", label: "Accelerators" },
  { key: "stages" as const, field: "stage", label: "Stages" },
];

const openCats = reactive<Record<string, boolean>>({
  campaigns: true,
  detectors: true,
  accelerators: false,
  stages: false,
});

const facets = reactive<Record<string, NavigationItem[]>>({});
const activeFilterKey = ref<string>("");

const toggleCat = (key: string) => {
  openCats[key] = !openCats[key];
};

const selectFacet = (field: string, value: string) => {
  const key = `${field}:${value}`;
  activeFilterKey.value = activeFilterKey.value === key ? "" : key;
  emit("filterFacet", field, activeFilterKey.value ? value : "");
};

const loadFacets = async () => {
  await Promise.all(
    categories.map(async (c) => {
      try {
        const res = await api.getNavigationCategory(c.key);
        facets[c.key] = res.items;
      } catch {
        facets[c.key] = [];
      }
    }),
  );
};

onMounted(loadFacets);
</script>
