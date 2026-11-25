<template>
  <section class="bg-white border border-carbon-20">
    <!-- Top Bar: Mode Switch + Actions -->
    <div class="flex items-center justify-between px-4 py-2 border-b border-carbon-20 bg-carbon-10/60">
      <div class="flex items-center gap-4">
        <span class="text-xs font-semibold uppercase tracking-wider text-carbon-80">Request DSL</span>
        <div class="flex border border-carbon-30 bg-white">
          <button
            type="button"
            class="px-2.5 py-1 text-[11px] font-medium cursor-pointer transition-colors"
            :class="mode === 'visual' ? 'bg-carbon-100 text-white' : 'text-carbon-80 hover:bg-carbon-10'"
            @click="mode = 'visual'"
          >
            Visual
          </button>
          <button
            type="button"
            class="px-2.5 py-1 text-[11px] font-medium cursor-pointer transition-colors border-l border-carbon-30"
            :class="mode === 'json' ? 'bg-carbon-100 text-white' : 'text-carbon-80 hover:bg-carbon-10'"
            @click="syncToJson(); mode = 'json'"
          >
            JSON
          </button>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          type="button"
          class="px-2.5 py-1 text-[11px] text-carbon-80 border border-carbon-30 bg-white hover:border-fcc cursor-pointer"
          @click="copySnippet('curl')"
        >
          {{ copiedKind === "curl" ? "Copied curl" : "Copy curl" }}
        </button>
        <button
          type="button"
          class="px-2.5 py-1 text-[11px] text-carbon-80 border border-carbon-30 bg-white hover:border-fcc cursor-pointer"
          @click="copySnippet('python')"
        >
          {{ copiedKind === "python" ? "Copied Python" : "Copy Python" }}
        </button>
        <button
          type="button"
          class="px-2.5 py-1 text-[11px] text-carbon-60 hover:text-carbon-100 cursor-pointer"
          @click="resetQuery"
        >
          Reset
        </button>
        <button
          type="button"
          class="px-4 py-1 text-xs font-medium bg-fcc hover:bg-fcc-hover text-white transition-colors cursor-pointer"
          :disabled="loading"
          @click="runQuery"
        >
          {{ loading ? "Running..." : "Run Query" }}
        </button>
      </div>
    </div>

    <!-- Visual Builder -->
    <div v-if="mode === 'visual'" class="p-4 space-y-3">
      <!-- Row 1: Entry Type, Sort, Get, Page Size -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div>
          <label class="block text-[11px] font-medium text-carbon-60 mb-1">Entry Type</label>
          <input
            v-model="entryType"
            type="text"
            placeholder="e.g. collision (or comma list)"
            class="w-full h-8 px-2.5 text-xs font-mono border border-carbon-30 focus:outline-none focus:border-fcc"
          >
        </div>

        <div>
          <label class="block text-[11px] font-medium text-carbon-60 mb-1">Sort By (dot path)</label>
          <div class="flex">
            <input
              v-model="sortBy"
              type="text"
              placeholder="e.g. ecm"
              class="w-full h-8 px-2.5 text-xs font-mono border border-carbon-30 focus:outline-none focus:border-fcc"
            >
            <select
              v-model="sortOrder"
              class="h-8 px-2 text-xs font-mono border border-l-0 border-carbon-30 bg-carbon-10 focus:outline-none"
            >
              <option value="asc">asc</option>
              <option value="desc">desc</option>
            </select>
          </div>
        </div>

        <div>
          <label class="block text-[11px] font-medium text-carbon-60 mb-1">Sample (`get`)</label>
          <div class="flex">
            <select
              v-model="getMode"
              class="h-8 px-2 text-xs font-mono border border-carbon-30 bg-carbon-10 focus:outline-none"
            >
              <option value="">none</option>
              <option value="first">first</option>
              <option value="last">last</option>
              <option value="random">random</option>
              <option value="uniform">uniform</option>
            </select>
            <input
              v-model.number="getCount"
              type="number"
              min="1"
              placeholder="N"
              :disabled="!getMode"
              class="w-full h-8 px-2 text-xs font-mono tabular border border-l-0 border-carbon-30 focus:outline-none focus:border-fcc disabled:bg-carbon-10"
            >
          </div>
        </div>

        <div>
          <label class="block text-[11px] font-medium text-carbon-60 mb-1">Page Size</label>
          <input
            v-model.number="pageSize"
            type="number"
            min="1"
            max="500"
            class="w-full h-8 px-2.5 text-xs font-mono tabular border border-carbon-30 focus:outline-none focus:border-fcc"
          >
        </div>
      </div>

      <!-- Row 2: Where Filter Rules -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <label class="text-[11px] font-medium text-carbon-60">
            Where Clauses <span class="font-mono text-carbon-50">(ANTLR4: =, !=, &gt;, &lt;, ~, :in [...], !in [...], * wildcard)</span>
          </label>
          <button
            type="button"
            class="text-[11px] text-fcc hover:underline cursor-pointer"
            @click="addWhereRule()"
          >
            + Add condition
          </button>
        </div>

        <div class="space-y-1.5">
          <div
            v-for="(rule, idx) in whereRules"
            :key="idx"
            class="flex items-center gap-2"
          >
            <input
              v-model="rule.path"
              type="text"
              list="umb-field-list"
              placeholder="path (e.g. ecm, parent.generator.version, *)"
              class="w-60 h-8 px-2.5 text-xs font-mono border border-carbon-30 focus:outline-none focus:border-fcc"
            >
            <input
              v-model="rule.expr"
              type="text"
              placeholder="expression (e.g. >=240 and <=365, :in [DIRAC, RUCIO])"
              class="flex-1 h-8 px-2.5 text-xs font-mono border border-carbon-30 focus:outline-none focus:border-fcc"
            >
            <button
              type="button"
              class="h-8 px-2.5 text-xs text-carbon-60 hover:text-carbon-100 border border-carbon-20 cursor-pointer"
              @click="whereRules.splice(idx, 1)"
            >
              ×
            </button>
          </div>
        </div>
        <datalist id="umb-field-list">
          <option v-for="k in fieldNames" :key="k" :value="k" />
          <option value="*" />
        </datalist>
      </div>

      <!-- Row 3: Fields (contains, without, take) -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label class="block text-[11px] font-medium text-carbon-60 mb-1">Contains (comma paths)</label>
          <input
            v-model="containsInput"
            type="text"
            placeholder="e.g. campaign, ecm"
            class="w-full h-8 px-2.5 text-xs font-mono border border-carbon-30 focus:outline-none focus:border-fcc"
          >
        </div>
        <div>
          <label class="block text-[11px] font-medium text-carbon-60 mb-1">Without (comma paths)</label>
          <input
            v-model="withoutInput"
            type="text"
            placeholder="e.g. simulation, private"
            class="w-full h-8 px-2.5 text-xs font-mono border border-carbon-30 focus:outline-none focus:border-fcc"
          >
        </div>
        <div>
          <label class="block text-[11px] font-medium text-carbon-60 mb-1">Take / Columns (comma paths)</label>
          <input
            v-model="takeInput"
            type="text"
            placeholder="e.g. name, process, ecm, campaign"
            class="w-full h-8 px-2.5 text-xs font-mono border border-carbon-30 focus:outline-none focus:border-fcc"
          >
        </div>
      </div>
    </div>

    <!-- Raw JSON Editor Mode -->
    <div v-else class="p-4">
      <textarea
        v-model="rawJson"
        rows="9"
        spellcheck="false"
        class="w-full p-3 text-xs font-mono bg-carbon-10 border border-carbon-30 focus:outline-none focus:border-fcc"
      />
      <p v-if="jsonError" class="mt-1.5 text-xs text-red-700 font-mono">{{ jsonError }}</p>
    </div>

    <!-- Inline Validation Errors & Warnings -->
    <div v-if="errors.length > 0 || warnings.length > 0" class="px-4 py-2 border-t border-carbon-20 space-y-1 text-xs">
      <div v-for="err in errors" :key="err" class="text-red-700 font-mono">
        ERROR: {{ err }}
      </div>
      <div v-for="warn in warnings" :key="warn" class="text-carbon-80 font-mono">
        NOTE: {{ warn }}
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { EntityRequest, MetadataConditionTree } from "~/types/api";
import { mergePathTrees, pathToTree, setConditionAtPath } from "~/composables/useUmbApi";

const props = defineProps<{
  fieldNames: string[];
  loading: boolean;
  errors: string[];
  warnings: string[];
  apiBase: string;
}>();

const emit = defineEmits<{
  execute: [request: EntityRequest, takeColumns: string[]];
}>();

const mode = ref<"visual" | "json">("visual");
const entryType = ref("");
const sortBy = ref("");
const sortOrder = ref<"asc" | "desc">("asc");
const getMode = ref<"" | "first" | "last" | "random" | "uniform">("");
const getCount = ref<number | undefined>(20);
const pageSize = ref<number>(25);
const whereRules = ref<Array<{ path: string; expr: string }>>([]);
const containsInput = ref("");
const withoutInput = ref("");
const takeInput = ref("");
const rawJson = ref("{}");
const jsonError = ref("");
const copiedKind = ref<"" | "curl" | "python">("");

const parseCommaList = (s: string) =>
  s.split(",").map((x) => x.trim()).filter(Boolean);

const buildRequestFromVisual = (): EntityRequest => {
  const req: EntityRequest = {};
  const types = parseCommaList(entryType.value);
  if (types.length === 1) req.entry_type = types[0];
  else if (types.length > 1) req.entry_type = types;

  const whereTree: MetadataConditionTree = {};
  for (const r of whereRules.value) {
    if (r.path.trim() && r.expr.trim()) {
      setConditionAtPath(whereTree, r.path.trim(), r.expr.trim());
    }
  }
  if (Object.keys(whereTree).length > 0) req.where = whereTree;

  const containsList = parseCommaList(containsInput.value);
  if (containsList.length > 0) req.contains = mergePathTrees(containsList);

  const withoutList = parseCommaList(withoutInput.value);
  if (withoutList.length > 0) req.without = mergePathTrees(withoutList);

  const takeList = parseCommaList(takeInput.value);
  if (takeList.length > 0) req.take = mergePathTrees(takeList);

  if (sortBy.value.trim()) {
    req.sort = { by: pathToTree(sortBy.value.trim()), order: sortOrder.value };
  }
  if (getMode.value && getCount.value && getCount.value > 0) {
    req.get = { [getMode.value]: getCount.value };
  }
  if (pageSize.value > 0) {
    req.page = { size: pageSize.value };
  }
  return req;
};

const syncToJson = () => {
  jsonError.value = "";
  rawJson.value = JSON.stringify(buildRequestFromVisual(), null, 2);
};

const addWhereRule = (path = "", expr = "") => {
  whereRules.value.push({ path, expr });
};

const setFacetRule = (field: string, value: string) => {
  const existing = whereRules.value.find((r) => r.path === field);
  if (!value) {
    whereRules.value = whereRules.value.filter((r) => r.path !== field);
  } else if (existing) {
    existing.expr = `=${value}`;
  } else {
    whereRules.value.push({ path: field, expr: `=${value}` });
  }
  runQuery();
};

const appendTakePath = (dotPath: string) => {
  const cur = parseCommaList(takeInput.value);
  if (!cur.includes(dotPath)) {
    cur.push(dotPath);
    takeInput.value = cur.join(", ");
  }
};

const getCurrentRequest = (): EntityRequest | null => {
  if (mode.value === "json") {
    try {
      jsonError.value = "";
      return JSON.parse(rawJson.value) as EntityRequest;
    } catch (e: unknown) {
      jsonError.value = (e as Error).message;
      return null;
    }
  }
  return buildRequestFromVisual();
};

const runQuery = () => {
  const req = getCurrentRequest();
  if (!req) return;
  emit("execute", req, parseCommaList(takeInput.value));
};

const resetQuery = () => {
  entryType.value = "";
  sortBy.value = "";
  sortOrder.value = "asc";
  getMode.value = "";
  pageSize.value = 25;
  whereRules.value = [];
  containsInput.value = "";
  withoutInput.value = "";
  takeInput.value = "";
  rawJson.value = JSON.stringify({ page: { size: 25 } }, null, 2);
  runQuery();
};

const copySnippet = async (kind: "curl" | "python") => {
  const req = getCurrentRequest();
  if (!req) return;
  const payload = JSON.stringify(req, null, 2);
  const text =
    kind === "curl"
      ? `curl -sS -X POST "${props.apiBase}/entity/" \\\n  -H "Content-Type: application/json" \\\n  -d '${JSON.stringify(req)}'`
      : `import httpx\n\nresp = httpx.post("${props.apiBase}/entity/", json=${payload})\nprint(resp.json())`;
  await navigator.clipboard.writeText(text);
  copiedKind.value = kind;
  setTimeout(() => { copiedKind.value = ""; }, 1600);
};

defineExpose({ addWhereRule, setFacetRule, appendTakePath, getCurrentRequest, runQuery });
</script>
