<template>
  <div v-if="open" class="fixed inset-0 z-50 flex justify-end bg-carbon-100/30" @click.self="emit('close')">
    <aside class="w-full max-w-md bg-white h-full border-l border-carbon-20 flex flex-col">
      <div class="px-5 py-3 border-b border-carbon-20 flex items-center justify-between">
        <span class="text-xs font-semibold uppercase tracking-wider text-carbon-100">Redis Async Jobs</span>
        <div class="flex items-center gap-3">
          <button type="button" class="text-[11px] text-fcc hover:underline cursor-pointer" @click="refresh">Refresh</button>
          <button type="button" class="text-sm text-carbon-60 hover:text-carbon-100 cursor-pointer" @click="emit('close')">×</button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-4 space-y-2 text-xs">
        <div v-if="jobs.length === 0" class="text-carbon-60 text-center py-8">
          No jobs submitted yet.
        </div>
        <div
          v-for="job in jobs"
          :key="job.id"
          class="p-3 border border-carbon-20 space-y-1.5"
        >
          <div class="flex items-center justify-between">
            <span class="font-mono font-medium text-carbon-100">{{ job.taskType }}</span>
            <span
              class="font-mono text-[10px] uppercase px-1.5 py-0.5 border"
              :class="
                job.status === 'done'
                  ? 'border-fcc text-fcc bg-fcc-soft'
                  : job.status === 'failed'
                  ? 'border-red-300 text-red-700 bg-red-50'
                  : 'border-carbon-30 text-carbon-80 bg-carbon-10'
              "
            >
              {{ job.status }}
            </span>
          </div>
          <div class="font-mono text-[10px] text-carbon-50 truncate">{{ job.id }}</div>
          <div v-if="job.error" class="font-mono text-[11px] text-red-700">{{ job.error }}</div>
          <div v-if="job.status === 'done'" class="pt-1">
            <button
              type="button"
              class="text-[11px] text-fcc hover:underline cursor-pointer"
              @click="downloadResult(job.id)"
            >
              Download Result
            </button>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import type { JobRecord } from "~/types/api";

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  close: [];
  "update:activeCount": [count: number];
}>();

const api = useUmbApi();
const jobs = ref<JobRecord[]>([]);

const refresh = async () => {
  try {
    const res = await api.listJobs();
    jobs.value = res.jobs;
    emit(
      "update:activeCount",
      res.jobs.filter((j) => j.status === "pending" || j.status === "running").length,
    );
  } catch {
    jobs.value = [];
  }
};

const downloadResult = async (jobId: string) => {
  const res = await api.getJobResult(jobId);
  const payload = res.result as { filename?: string; content?: string } | undefined;
  const text = typeof payload?.content === "string" ? payload.content : JSON.stringify(res.result, null, 2);
  const filename = payload?.filename || `job_${jobId}.json`;
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) refresh();
  },
);

defineExpose({ refresh });
</script>
