<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-carbon-100/40 p-4" @click.self="emit('close')">
    <div class="w-full max-w-2xl bg-white border border-carbon-20">
      <div class="px-5 py-3 border-b border-carbon-20 flex items-center justify-between">
        <span class="text-xs font-semibold uppercase tracking-wider text-carbon-100">Export Current Query</span>
        <button type="button" class="text-sm text-carbon-60 hover:text-carbon-100 cursor-pointer" @click="emit('close')">×</button>
      </div>

      <div class="p-5 space-y-4 text-xs">
        <div class="flex flex-wrap items-center gap-2">
          <button
            v-for="fmt in formats"
            :key="fmt"
            type="button"
            class="px-3 py-1.5 font-mono uppercase border cursor-pointer"
            :class="selected === fmt ? 'border-fcc bg-fcc text-white' : 'border-carbon-30 text-carbon-80 hover:border-fcc'"
            @click="selected = fmt"
          >
            {{ fmt }}
          </button>
        </div>

        <div class="flex items-center gap-2">
          <button
            type="button"
            class="px-4 py-1.5 bg-fcc hover:bg-fcc-hover text-white font-medium cursor-pointer"
            :disabled="loading"
            @click="runDirectExport"
          >
            {{ loading ? "Exporting..." : "Preview & Download" }}
          </button>
          <button
            type="button"
            class="px-4 py-1.5 border border-carbon-30 text-carbon-100 hover:border-fcc cursor-pointer"
            :disabled="loading"
            @click="runAsRedisJob"
          >
            Queue as Redis Background Job
          </button>
        </div>

        <p v-if="statusMsg" class="font-mono text-[11px] text-carbon-80">{{ statusMsg }}</p>

        <pre
          v-if="preview"
          class="max-h-72 overflow-auto p-3 bg-carbon-10 border border-carbon-20 font-mono text-[11px]"
        >{{ preview }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { EntityRequest, ExportFormat } from "~/types/api";

const props = defineProps<{
  open: boolean;
  query: EntityRequest;
}>();

const emit = defineEmits<{
  close: [];
  jobQueued: [];
}>();

const api = useUmbApi();
const formats: ExportFormat[] = ["yaml", "python", "json", "csv", "toml"];
const selected = ref<ExportFormat>("yaml");
const loading = ref(false);
const preview = ref("");
const statusMsg = ref("");

const extMap: Record<ExportFormat, string> = {
  csv: "csv",
  json: "json",
  yaml: "yaml",
  toml: "toml",
  python: "py",
};

const runDirectExport = async () => {
  loading.value = true;
  statusMsg.value = "";
  try {
    const text = await api.exportData(props.query, selected.value);
    preview.value = text.slice(0, 6000);
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `umb_export.${extMap[selected.value]}`;
    a.click();
    URL.revokeObjectURL(url);
    statusMsg.value = `Downloaded umb_export.${extMap[selected.value]}`;
  } catch (e: unknown) {
    statusMsg.value = (e as { message?: string })?.message || "Export failed.";
  } finally {
    loading.value = false;
  }
};

const runAsRedisJob = async () => {
  loading.value = true;
  statusMsg.value = "";
  try {
    const rec = await api.submitJob("export", { format: selected.value, query: props.query });
    statusMsg.value = `Queued Redis job ${rec.id} (${rec.status}). Open Jobs drawer to monitor.`;
    emit("jobQueued");
  } catch (e: unknown) {
    statusMsg.value = (e as { message?: string })?.message || "Job submission failed.";
  } finally {
    loading.value = false;
  }
};
</script>
