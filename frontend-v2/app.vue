<template>
  <div class="min-h-screen flex flex-col bg-carbon-10 text-carbon-100">
    <AppHeader
      v-model:active-view="activeView"
      :saved-count="savedCount"
      :active-jobs-count="activeJobsCount"
      :auth-status="authStatus"
      @search="runGlobalSearch"
      @open-export="exportOpen = true"
      @open-jobs="jobsOpen = true"
      @open-auth="authOpen = true"
    />

    <div class="flex flex-1 min-h-0">
      <FacetSidebar
        :fields="fields"
        :collections="collections"
        :saved-count="savedCount"
        @filter-facet="onFacetFilter"
        @pick-field="onPickField"
        @open-saved="activeView = 'saved'"
        @open-collection="onOpenCollection"
      />

      <main class="flex-1 p-5 space-y-4 overflow-y-auto min-w-0">
        <!-- Catalog View -->
        <template v-if="activeView === 'catalog'">
          <DslWorkbench
            ref="workbenchRef"
            :field-names="fieldNames"
            :loading="loading"
            :errors="validationErrors"
            :warnings="validationWarnings"
            :api-base="api.apiBase"
            @execute="executeDsl"
          />

          <ResultsTable
            :rows="rows"
            :take-columns="takeColumns"
            :loading="loading"
            :has-more="Boolean(hasMore && nextCursor)"
            @inspect="inspectedEntity = $event"
            @next-page="loadNextPage"
          />
        </template>

        <!-- Saved Events & Collections View -->
        <SavedCollectionsView
          v-else-if="activeView === 'saved'"
          @inspect="inspectedEntity = $event"
        />

        <!-- Analytics View -->
        <AnalyticsPanel
          v-else
          @drill-cell="onDrillCoverageCell"
        />
      </main>
    </div>

    <EntityDrawer
      :entity="inspectedEntity"
      @close="inspectedEntity = null"
      @add-where="onDrawerAddWhere"
      @add-take="onDrawerAddTake"
      @select-entity="inspectedEntity = $event"
    />

    <ExportModal
      :open="exportOpen"
      :query="lastRequest"
      @close="exportOpen = false"
      @job-queued="jobsDrawerRef?.refresh()"
    />

    <JobsDrawer
      ref="jobsDrawerRef"
      :open="jobsOpen"
      @close="jobsOpen = false"
      @update:active-count="activeJobsCount = $event"
    />

    <AuthModal
      :open="authOpen"
      :auth-status="authStatus"
      @close="authOpen = false"
      @updated="loadAuth"
    />
  </div>
</template>

<script setup lang="ts">
import type {
  AuthStatusResponse,
  EntityRequest,
  EntityRow,
  FieldRegistryEntry,
} from "~/types/api";

const api = useUmbApi();
const { savedCount, collections, refreshCollections, openCollection } = useSavedEvents();

const activeView = ref<"catalog" | "saved" | "analytics">("catalog");
const fields = ref<FieldRegistryEntry[]>([]);
const rows = ref<EntityRow[]>([]);
const takeColumns = ref<string[]>([]);
const loading = ref(false);
const validationErrors = ref<string[]>([]);
const validationWarnings = ref<string[]>([]);
const lastRequest = ref<EntityRequest>({ page: { size: 25 } });
const nextCursor = ref<string | null>(null);
const hasMore = ref(false);

const inspectedEntity = ref<EntityRow | null>(null);
const exportOpen = ref(false);
const jobsOpen = ref(false);
const authOpen = ref(false);
const activeJobsCount = ref(0);
const authStatus = ref<AuthStatusResponse | null>(null);

const workbenchRef = ref<{
  addWhereRule: (path?: string, expr?: string) => void;
  setFacetRule: (field: string, value: string) => void;
  appendTakePath: (dotPath: string) => void;
  runQuery: () => void;
} | null>(null);

const jobsDrawerRef = ref<{ refresh: () => Promise<void> } | null>(null);

const fieldNames = computed(() =>
  Array.from(new Set(fields.value.map((f) => f.key))).sort(),
);

const executeDsl = async (req: EntityRequest, cols: string[]) => {
  loading.value = true;
  validationErrors.value = [];
  validationWarnings.value = [];
  lastRequest.value = req;
  takeColumns.value = cols;
  try {
    const res = await api.queryEntities(req);
    validationErrors.value = res.validationResult?.errors || [];
    validationWarnings.value = res.validationResult?.warnings || [];
    rows.value = res.entities || [];
    nextCursor.value = res.nextCursor ?? null;
    hasMore.value = Boolean(res.hasMore);
  } catch (e: unknown) {
    validationErrors.value = [(e as { message?: string })?.message || "Backend request failed."];
  } finally {
    loading.value = false;
  }
};

const loadNextPage = async () => {
  if (!nextCursor.value) return;
  loading.value = true;
  try {
    const nextReq: EntityRequest = {
      ...lastRequest.value,
      page: { size: lastRequest.value.page?.size || 25, cursor: nextCursor.value },
    };
    const res = await api.queryEntities(nextReq);
    rows.value = [...rows.value, ...(res.entities || [])];
    nextCursor.value = res.nextCursor ?? null;
    hasMore.value = Boolean(res.hasMore);
  } finally {
    loading.value = false;
  }
};

const runGlobalSearch = async (q: string) => {
  activeView.value = "catalog";
  if (!q) {
    workbenchRef.value?.runQuery();
    return;
  }
  loading.value = true;
  validationErrors.value = [];
  try {
    const res = await api.searchFulltext(q, undefined, 50);
    rows.value = res.hits.map((h) => ({ id: h.id, metadata: h.metadata, entry_type: h.entryType }));
    hasMore.value = false;
    nextCursor.value = null;
  } finally {
    loading.value = false;
  }
};

const onFacetFilter = (field: string, value: string) => {
  activeView.value = "catalog";
  workbenchRef.value?.setFacetRule(field, value);
};

const onPickField = (fieldKey: string) => {
  activeView.value = "catalog";
  workbenchRef.value?.addWhereRule(fieldKey, "=");
};

const onDrawerAddWhere = (path: string, expr: string) => {
  activeView.value = "catalog";
  workbenchRef.value?.addWhereRule(path, expr);
};

const onDrawerAddTake = (path: string) => {
  activeView.value = "catalog";
  workbenchRef.value?.appendTakePath(path);
};

const onDrillCoverageCell = (rowField: string, rowVal: string, colField: string, colVal: string) => {
  activeView.value = "catalog";
  nextTick(() => {
    workbenchRef.value?.addWhereRule(rowField, `=${rowVal}`);
    workbenchRef.value?.addWhereRule(colField, `=${colVal}`);
    workbenchRef.value?.runQuery();
  });
};

const onOpenCollection = async (id: string) => {
  await openCollection(id);
  activeView.value = "saved";
};

const loadAuth = async () => {
  try {
    authStatus.value = await api.getAuthStatus();
  } catch {
    authStatus.value = null;
  }
};

onMounted(async () => {
  await Promise.all([
    loadAuth(),
    refreshCollections(),
    api.getFieldRegistry().then((r) => { fields.value = r.fields; }).catch(() => {}),
  ]);
  executeDsl({ page: { size: 25 } }, []);
});
</script>
