<template>
  <section class="space-y-4">
    <!-- Mode Tabs -->
    <div class="bg-white border border-carbon-20 px-4 flex items-center gap-6 text-xs">
      <button
        v-for="m in modes"
        :key="m.id"
        type="button"
        class="py-3 border-b-2 font-medium cursor-pointer"
        :class="mode === m.id ? 'border-fcc text-carbon-100' : 'border-transparent text-carbon-60 hover:text-carbon-100'"
        @click="mode = m.id"
      >
        {{ m.label }}
      </button>
    </div>

    <!-- Histogram -->
    <div v-if="mode === 'histogram'" class="bg-white border border-carbon-20 p-5 space-y-4">
      <div class="flex flex-wrap items-end gap-3">
        <div>
          <label class="block text-[11px] font-medium text-carbon-60 mb-1">Numeric Field Path</label>
          <input
            v-model="histField"
            type="text"
            placeholder="e.g. ecm"
            class="w-56 h-8 px-2.5 text-xs font-mono border border-carbon-30 focus:outline-none focus:border-fcc"
          >
        </div>
        <div>
          <label class="block text-[11px] font-medium text-carbon-60 mb-1">Bins ({{ histBins }})</label>
          <input v-model.number="histBins" type="range" min="2" max="40" class="w-36 accent-fcc">
        </div>
        <button
          type="button"
          class="h-8 px-4 text-xs font-medium bg-fcc hover:bg-fcc-hover text-white cursor-pointer"
          @click="runHistogram"
        >
          Compute
        </button>
      </div>

      <div v-if="histogram" class="space-y-4">
        <div class="grid grid-cols-3 gap-3 text-xs">
          <div class="p-3 border border-carbon-20 bg-carbon-10/50">
            <div class="text-[11px] text-carbon-60">Total Values</div>
            <div class="font-mono tabular text-base font-semibold mt-0.5">{{ histogram.totalValues }}</div>
          </div>
          <div class="p-3 border border-carbon-20 bg-carbon-10/50">
            <div class="text-[11px] text-carbon-60">Min</div>
            <div class="font-mono tabular text-base font-semibold mt-0.5">{{ histogram.min ?? "—" }}</div>
          </div>
          <div class="p-3 border border-carbon-20 bg-carbon-10/50">
            <div class="text-[11px] text-carbon-60">Max</div>
            <div class="font-mono tabular text-base font-semibold mt-0.5">{{ histogram.max ?? "—" }}</div>
          </div>
        </div>

        <div v-if="histogram.bins.length > 0" class="border border-carbon-20 p-4">
          <div class="h-48 flex items-end gap-1">
            <div
              v-for="(bin, i) in histogram.bins"
              :key="i"
              class="flex-1 flex flex-col items-center justify-end h-full group"
              :title="`[${bin.lower}, ${bin.upper}]: ${bin.count}`"
            >
              <span class="text-[10px] font-mono tabular text-carbon-60 mb-1">{{ bin.count }}</span>
              <div
                class="w-full bg-fcc group-hover:bg-fcc-hover transition-colors"
                :style="{ height: `${Math.max((bin.count / maxBinCount) * 100, bin.count > 0 ? 4 : 0)}%` }"
              />
            </div>
          </div>
          <div class="flex justify-between text-[10px] font-mono tabular text-carbon-60 mt-2 pt-2 border-t border-carbon-20">
            <span>{{ histogram.bins[0]?.lower }}</span>
            <span>{{ histogram.path.join(".") }}</span>
            <span>{{ histogram.bins[histogram.bins.length - 1]?.upper }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Grouped Summary -->
    <div v-else-if="mode === 'summary'" class="bg-white border border-carbon-20 p-5 space-y-4">
      <div class="flex flex-wrap items-end gap-3">
        <div>
          <label class="block text-[11px] font-medium text-carbon-60 mb-1">Group By Path</label>
          <input
            v-model="summaryGroupBy"
            type="text"
            placeholder="e.g. process"
            class="w-48 h-8 px-2.5 text-xs font-mono border border-carbon-30 focus:outline-none focus:border-fcc"
          >
        </div>
        <div>
          <label class="block text-[11px] font-medium text-carbon-60 mb-1">Metric Path (optional)</label>
          <input
            v-model="summaryMetric"
            type="text"
            placeholder="e.g. cross_section_pb"
            class="w-52 h-8 px-2.5 text-xs font-mono border border-carbon-30 focus:outline-none focus:border-fcc"
          >
        </div>
        <button
          type="button"
          class="h-8 px-4 text-xs font-medium bg-fcc hover:bg-fcc-hover text-white cursor-pointer"
          @click="runSummary"
        >
          Summarize
        </button>
      </div>

      <table v-if="summary" class="w-full text-left border-collapse text-xs">
        <thead>
          <tr class="border-b border-carbon-20 bg-carbon-10 text-carbon-60 text-[11px] uppercase">
            <th class="px-3 py-2">Group</th>
            <th class="px-3 py-2 text-right">Count</th>
            <th class="px-3 py-2 text-right">Mean</th>
            <th class="px-3 py-2 text-right">Min</th>
            <th class="px-3 py-2 text-right">Max</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="g in summary.groups" :key="String(g.group)" class="border-b border-carbon-20">
            <td class="px-3 py-2 font-mono text-carbon-100">{{ g.group ?? "null" }}</td>
            <td class="px-3 py-2 font-mono tabular text-right">{{ g.count }}</td>
            <td class="px-3 py-2 font-mono tabular text-right">{{ g.mean ?? "—" }}</td>
            <td class="px-3 py-2 font-mono tabular text-right">{{ g.min ?? "—" }}</td>
            <td class="px-3 py-2 font-mono tabular text-right">{{ g.max ?? "—" }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Phase-Space Coverage Matrix -->
    <div v-else class="bg-white border border-carbon-20 p-5 space-y-4">
      <div class="flex flex-wrap items-end gap-3">
        <div>
          <label class="block text-[11px] font-medium text-carbon-60 mb-1">Row Field</label>
          <input
            v-model="covRow"
            type="text"
            class="w-44 h-8 px-2.5 text-xs font-mono border border-carbon-30 focus:outline-none focus:border-fcc"
          >
        </div>
        <div>
          <label class="block text-[11px] font-medium text-carbon-60 mb-1">Column Field</label>
          <input
            v-model="covCol"
            type="text"
            class="w-44 h-8 px-2.5 text-xs font-mono border border-carbon-30 focus:outline-none focus:border-fcc"
          >
        </div>
        <button
          type="button"
          class="h-8 px-4 text-xs font-medium bg-fcc hover:bg-fcc-hover text-white cursor-pointer"
          @click="runCoverage"
        >
          Build Matrix
        </button>
      </div>

      <div v-if="coverage" class="overflow-x-auto">
        <table class="text-xs border-collapse">
          <thead>
            <tr class="border-b border-carbon-20 bg-carbon-10">
              <th class="px-3 py-2 text-left font-mono text-carbon-60">{{ covRow }} \ {{ covCol }}</th>
              <th v-for="c in coverageCols" :key="c" class="px-3 py-2 font-mono tabular text-carbon-80">{{ c }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in coverageRows" :key="r" class="border-b border-carbon-20">
              <td class="px-3 py-2 font-mono font-medium text-carbon-100">{{ r }}</td>
              <td
                v-for="c in coverageCols"
                :key="c"
                class="px-3 py-2 text-center font-mono tabular border-l border-carbon-10"
                :class="cellCount(r, c) > 0 ? 'bg-fcc-soft text-carbon-100 font-semibold cursor-pointer hover:bg-fcc hover:text-white' : 'text-carbon-30'"
                @click="cellCount(r, c) > 0 && emit('drillCell', covRow, r, covCol, c)"
              >
                {{ cellCount(r, c) || "·" }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { CoverageResponse, HistogramResponse, SummaryResponse } from "~/types/api";
import { pathToTree } from "~/composables/useUmbApi";

const emit = defineEmits<{
  drillCell: [rowField: string, rowVal: string, colField: string, colVal: string];
}>();

const api = useUmbApi();
const modes = [
  { id: "histogram" as const, label: "Histogram" },
  { id: "summary" as const, label: "Grouped Summary" },
  { id: "coverage" as const, label: "Phase-Space Coverage" },
];
const mode = ref<"histogram" | "summary" | "coverage">("histogram");

const histField = ref("ecm");
const histBins = ref(10);
const histogram = ref<HistogramResponse | null>(null);

const summaryGroupBy = ref("process");
const summaryMetric = ref("cross_section_pb");
const summary = ref<SummaryResponse | null>(null);

const covRow = ref("process");
const covCol = ref("ecm");
const coverage = ref<CoverageResponse | null>(null);

const maxBinCount = computed(() =>
  Math.max(...(histogram.value?.bins.map((b) => b.count) || [1]), 1),
);

const coverageRows = computed(() =>
  Array.from(new Set((coverage.value?.cells || []).map((c) => String(c.row)))).sort(),
);
const coverageCols = computed(() =>
  Array.from(new Set((coverage.value?.cells || []).map((c) => String(c.col)))).sort(),
);

const cellCount = (r: string, c: string) =>
  coverage.value?.cells.find((x) => String(x.row) === r && String(x.col) === c)?.count || 0;

const runHistogram = async () => {
  if (!histField.value.trim()) return;
  histogram.value = await api.getHistogram(pathToTree(histField.value.trim()), histBins.value);
};

const runSummary = async () => {
  if (!summaryGroupBy.value.trim()) return;
  summary.value = await api.getSummary(
    pathToTree(summaryGroupBy.value.trim()),
    summaryMetric.value.trim() ? pathToTree(summaryMetric.value.trim()) : undefined,
  );
};

const runCoverage = async () => {
  coverage.value = await api.getCoverage(covRow.value.trim(), covCol.value.trim());
};
</script>
