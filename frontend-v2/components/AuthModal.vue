<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center bg-carbon-100/40 p-4" @click.self="emit('close')">
    <div class="w-full max-w-sm bg-white border border-carbon-20">
      <div class="px-5 py-3 border-b border-carbon-20 flex items-center justify-between">
        <span class="text-xs font-semibold uppercase tracking-wider text-carbon-100">Session</span>
        <button type="button" class="text-sm text-carbon-60 hover:text-carbon-100 cursor-pointer" @click="emit('close')">×</button>
      </div>

      <div class="p-5 text-xs space-y-3">
        <div v-if="authStatus && !authStatus.authEnabled" class="text-carbon-80 space-y-2">
          <p>Authentication is disabled on the backend (<span class="font-mono">METADATA_BROWSER_AUTH_ENABLED=false</span>).</p>
          <p class="text-carbon-60">You are browsing in public mode.</p>
        </div>

        <div v-else-if="authStatus?.authenticated" class="space-y-3">
          <div>
            Signed in as <span class="font-mono font-semibold text-carbon-100">{{ authStatus.user?.username }}</span>
          </div>
          <div class="font-mono text-[11px] text-carbon-60">
            Roles: {{ authStatus.user?.roles.join(", ") }}
          </div>
          <button
            type="button"
            class="w-full h-8 border border-carbon-30 text-carbon-100 hover:border-fcc cursor-pointer"
            @click="handleLogout"
          >
            Sign Out
          </button>
        </div>

        <form v-else class="space-y-3" @submit.prevent="handleLogin">
          <div>
            <label class="block text-[11px] text-carbon-60 mb-1">Username</label>
            <input
              v-model="username"
              type="text"
              required
              class="w-full h-8 px-2.5 border border-carbon-30 focus:outline-none focus:border-fcc"
            >
          </div>
          <div>
            <label class="block text-[11px] text-carbon-60 mb-1">Password</label>
            <input
              v-model="password"
              type="password"
              required
              class="w-full h-8 px-2.5 border border-carbon-30 focus:outline-none focus:border-fcc"
            >
          </div>
          <p v-if="errorMsg" class="text-red-700 font-mono text-[11px]">{{ errorMsg }}</p>
          <button
            type="submit"
            class="w-full h-8 bg-fcc hover:bg-fcc-hover text-white font-medium cursor-pointer"
          >
            Sign In
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AuthStatusResponse } from "~/types/api";

defineProps<{
  open: boolean;
  authStatus: AuthStatusResponse | null;
}>();

const emit = defineEmits<{
  close: [];
  updated: [];
}>();

const api = useUmbApi();
const username = ref("");
const password = ref("");
const errorMsg = ref("");

const handleLogin = async () => {
  errorMsg.value = "";
  try {
    await api.login(username.value.trim(), password.value);
    username.value = "";
    password.value = "";
    emit("updated");
    emit("close");
  } catch {
    errorMsg.value = "Invalid credentials or auth service unavailable.";
  }
};

const handleLogout = () => {
  api.logout();
  emit("updated");
  emit("close");
};
</script>
