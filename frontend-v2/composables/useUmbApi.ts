import type {
  AuthStatusResponse,
  CollectionDetail,
  CollectionSummary,
  CompareResponse,
  CoverageResponse,
  EntityRequest,
  EntityResponse,
  ExportFormat,
  FieldRegistryResponse,
  FulltextSearchResponse,
  HistogramResponse,
  JobRecord,
  JobResultResponse,
  JobTaskType,
  MetadataConditionTree,
  MetadataPathTree,
  NavigationResponse,
  SimilarSearchResponse,
  SuggestResponse,
  SummaryResponse,
  TokenResponse,
} from "~/types/api";

const ACCESS_KEY = "umb_v2_access_token";
const REFRESH_KEY = "umb_v2_refresh_token";

function readToken(key: string): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(key);
}

function writeToken(key: string, value: string | null): void {
  if (typeof window === "undefined") return;
  if (value === null) window.localStorage.removeItem(key);
  else window.localStorage.setItem(key, value);
}

export function pathToTree(dotPath: string): MetadataPathTree {
  const parts = dotPath.split(".").map((s) => s.trim()).filter(Boolean);
  const root: MetadataPathTree = {};
  let cur = root;
  for (const part of parts) {
    cur[part] = {};
    cur = cur[part] as MetadataPathTree;
  }
  return root;
}

export function mergePathTrees(paths: string[]): MetadataPathTree {
  const root: MetadataPathTree = {};
  for (const raw of paths) {
    const parts = raw.split(".").map((s) => s.trim()).filter(Boolean);
    let cur = root;
    for (const part of parts) {
      if (!cur[part] || typeof cur[part] !== "object") {
        cur[part] = {};
      }
      cur = cur[part] as MetadataPathTree;
    }
  }
  return root;
}

export function setConditionAtPath(
  root: MetadataConditionTree,
  dotPath: string,
  expr: string,
): void {
  const parts = dotPath.split(".").map((s) => s.trim()).filter(Boolean);
  if (parts.length === 0) return;
  let cur = root;
  for (let i = 0; i < parts.length - 1; i++) {
    const k = parts[i];
    if (!cur[k] || typeof cur[k] !== "object") cur[k] = {};
    cur = cur[k] as MetadataConditionTree;
  }
  cur[parts[parts.length - 1]] = expr;
}

export function useUmbApi() {
  const config = useRuntimeConfig();
  const rawBase = String(config.public.apiBaseUrl || "http://localhost:8000").replace(/\/+$/, "");
  const apiBase = rawBase.endsWith("/api/v1") ? rawBase : `${rawBase}/api/v1`;

  const setTokens = (tokens: TokenResponse | null) => {
    writeToken(ACCESS_KEY, tokens?.accessToken ?? null);
    writeToken(REFRESH_KEY, tokens?.refreshToken ?? null);
  };

  const refreshTokens = async (): Promise<boolean> => {
    const rt = readToken(REFRESH_KEY);
    if (!rt) return false;
    try {
      const res = await $fetch<TokenResponse>(`${apiBase}/auth/refresh`, {
        method: "POST",
        body: { refreshToken: rt },
      });
      setTokens(res);
      return true;
    } catch {
      setTokens(null);
      return false;
    }
  };

  const request = async <T>(
    path: string,
    opts: {
      method?: "GET" | "POST" | "PUT" | "DELETE";
      body?: unknown;
      query?: Record<string, string | number | boolean | undefined>;
      responseType?: "json" | "text";
    } = {},
    retried = false,
  ): Promise<T> => {
    const token = readToken(ACCESS_KEY);
    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;

    const cleanQuery: Record<string, string | number | boolean> = {};
    if (opts.query) {
      for (const [k, v] of Object.entries(opts.query)) {
        if (v !== undefined && v !== "") cleanQuery[k] = v;
      }
    }

    try {
      return await $fetch<T>(`${apiBase}${path}`, {
        method: opts.method ?? "GET",
        body: opts.body as Record<string, unknown> | undefined,
        query: Object.keys(cleanQuery).length ? cleanQuery : undefined,
        headers,
        responseType: opts.responseType,
      });
    } catch (err: unknown) {
      const status = (err as { statusCode?: number; status?: number })?.statusCode
        ?? (err as { status?: number })?.status;
      if (status === 401 && !retried && (await refreshTokens())) {
        return request<T>(path, opts, true);
      }
      throw err;
    }
  };

  return {
    apiBase,
    // Health
    checkHealth: () => request<EntityResponse>("/check/"),
    // Entities
    queryEntities: (body: EntityRequest) =>
      request<EntityResponse>("/entity/", { method: "POST", body }),
    statEntities: (body: EntityRequest) =>
      request<EntityResponse>("/entity/stat", { method: "POST", body }),
    getEntity: (body: EntityRequest) =>
      request<EntityResponse>("/entity/get", { method: "POST", body }),
    randomEntities: (n = 5, entryType?: string) =>
      request<EntityResponse>("/entity/rand", { query: { n, entry_type: entryType } }),
    // Navigation
    getNavigationCategory: (category: "accelerators" | "campaigns" | "detectors" | "stages", entryType?: string) =>
      request<NavigationResponse>(`/navigation/${category}`, { query: { entry_type: entryType } }),
    getFieldRegistry: (entryType?: string) =>
      request<FieldRegistryResponse>("/navigation/fields", { query: { entry_type: entryType } }),
    getFieldValues: (fieldName: string, entryType?: string) =>
      request<NavigationResponse>(`/navigation/values/${encodeURIComponent(fieldName)}`, {
        query: { entry_type: entryType },
      }),
    // Search
    searchFulltext: (q: string, entryType?: string, limit = 25) =>
      request<FulltextSearchResponse>("/search/", { query: { q, entry_type: entryType, limit } }),
    searchSimilar: (entityId: string, limit = 10) =>
      request<SimilarSearchResponse>(`/search/similar/${encodeURIComponent(entityId)}`, {
        query: { limit },
      }),
    suggestField: (field: string, prefix = "", entryType?: string, limit = 15) =>
      request<SuggestResponse>("/search/suggest", {
        query: { field, prefix, entry_type: entryType, limit },
      }),
    // Analytics
    getHistogram: (field: MetadataPathTree, bins = 10, entryType?: string, where?: MetadataConditionTree) =>
      request<HistogramResponse>("/analytics/histogram", {
        method: "POST",
        body: { field, bins, entry_type: entryType || undefined, where },
      }),
    getSummary: (groupBy: MetadataPathTree, metric?: MetadataPathTree, entryType?: string, where?: MetadataConditionTree) =>
      request<SummaryResponse>("/analytics/summary", {
        method: "POST",
        body: { groupBy, metric, entry_type: entryType || undefined, where },
      }),
    compareGroups: (groupA: EntityRequest, groupB: EntityRequest, metrics: MetadataPathTree[]) =>
      request<CompareResponse>("/analytics/compare", {
        method: "POST",
        body: { groupA, groupB, metrics },
      }),
    getCoverage: (rowField = "process", colField = "ecm", entryType?: string) =>
      request<CoverageResponse>("/analytics/coverage", {
        query: { row_field: rowField, col_field: colField, entry_type: entryType },
      }),
    // Export
    exportData: (body: EntityRequest, format: ExportFormat) =>
      request<string>(`/export/${format}`, { method: "POST", body, responseType: "text" }),
    // Auth
    getAuthStatus: () => request<AuthStatusResponse>("/auth/me"),
    login: async (username: string, password: string) => {
      const tokens = await request<TokenResponse>("/auth/login", {
        method: "POST",
        body: { username, password },
      });
      setTokens(tokens);
      return tokens;
    },
    logout: () => setTokens(null),
    // Collections
    listCollections: () =>
      request<{ collections: CollectionSummary[]; total: number }>("/collections/"),
    createCollection: (name: string, description = "", isPublic = false) =>
      request<CollectionDetail>("/collections/", {
        method: "POST",
        body: { name, description, isPublic },
      }),
    getCollection: (id: string) =>
      request<CollectionDetail>(`/collections/${encodeURIComponent(id)}`),
    deleteCollection: (id: string) =>
      request<{ deleted: boolean; id: string }>(`/collections/${encodeURIComponent(id)}`, {
        method: "DELETE",
      }),
    updateCollectionEvents: (id: string, add: string[], remove: string[] = []) =>
      request<{ collectionId: string; added: number; removed: number; entryIds: string[] }>(
        `/collections/${encodeURIComponent(id)}/events`,
        { method: "POST", body: { add, remove } },
      ),
    // Jobs
    submitJob: (taskType: JobTaskType, payload: Record<string, unknown>) =>
      request<JobRecord>("/jobs/", { method: "POST", body: { taskType, payload } }),
    listJobs: () => request<{ jobs: JobRecord[]; total: number }>("/jobs/"),
    getJobStatus: (id: string) => request<JobRecord>(`/jobs/${encodeURIComponent(id)}`),
    getJobResult: (id: string) =>
      request<JobResultResponse>(`/jobs/${encodeURIComponent(id)}/result`),
  };
}
