/**
 * Typed API client targeting the Universal Metadata Browser /api/v1 backend.
 * Preserves compatibility with existing Vue composables while exposing all v1 domain APIs.
 */
import type {
  ApiError,
  CreateEntityPayload,
  Entity,
  SearchApiResponse,
  TypedFetchOptions,
  UpdateEntityPayload,
  V1AuthStatusResponse,
  V1CollectionDetail,
  V1CollectionListResponse,
  V1CompareRequest,
  V1CompareResponse,
  V1CoverageResponse,
  V1EntityRequest,
  V1ExportFormat,
  V1FieldRegistryResponse,
  V1FulltextSearchResponse,
  V1HistogramRequest,
  V1HistogramResponse,
  V1JobRecord,
  V1JobResultResponse,
  V1NavigationResponse,
  V1RawEntityRow,
  V1Response,
  V1SimilarSearchResponse,
  V1SuggestResponse,
  V1SummaryRequest,
  V1SummaryResponse,
  V1TokenResponse,
} from "~/types/api";
import type { SearchOptions } from "~/types/composables";
import { HttpStatusCode } from "~/types/api";

const ACCESS_TOKEN_KEY = "umb_access_token";
const REFRESH_TOKEN_KEY = "umb_refresh_token";
const NAV_CATEGORIES = new Set([
  "accelerators",
  "campaigns",
  "detectors",
  "stages",
]);

let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

function readStorage(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string | null): void {
  if (typeof window === "undefined") return;
  try {
    if (value === null) {
      window.localStorage.removeItem(key);
    } else {
      window.localStorage.setItem(key, value);
    }
  } catch {
    // Ignore storage errors in restricted browser contexts
  }
}

function pathToTree(dotPath: string): Record<string, unknown> {
  const segments = dotPath.split(".").filter(Boolean);
  const root: Record<string, unknown> = {};
  let cur = root;
  for (const seg of segments) {
    cur[seg] = {};
    cur = cur[seg] as Record<string, unknown>;
  }
  return root;
}

function normalizeRowToEntity(row: V1RawEntityRow, index: number): Entity {
  const meta = (
    row.metadata && typeof row.metadata === "object" ? row.metadata : {}
  ) as Record<string, unknown>;
  const name =
    typeof meta.name === "string" && meta.name.length > 0
      ? meta.name
      : String(row.id);
  const numericId = Number.parseInt(
    String(row.id).replace(/-/g, "").slice(0, 8),
    16,
  );
  return {
    entity_id: Number.isFinite(numericId) ? numericId : index + 1,
    uuid: String(row.id),
    name,
    metadata: meta,
    ...meta,
  };
}

export function useApiClient() {
  const config = useRuntimeConfig();
  const rawBase = String(
    config.public.apiBaseUrl || "http://localhost:8000",
  ).replace(/\/+$/, "");
  const baseUrl = rawBase.endsWith("/api/v1") ? rawBase : `${rawBase}/api/v1`;

  const setTokens = (tokens: V1TokenResponse | null): void => {
    if (tokens === null) {
      writeStorage(ACCESS_TOKEN_KEY, null);
      writeStorage(REFRESH_TOKEN_KEY, null);
    } else {
      writeStorage(ACCESS_TOKEN_KEY, tokens.accessToken);
      writeStorage(REFRESH_TOKEN_KEY, tokens.refreshToken);
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    if (isRefreshing && refreshPromise) {
      return await refreshPromise;
    }
    const storedRefresh = readStorage(REFRESH_TOKEN_KEY);
    if (!storedRefresh) {
      return false;
    }

    isRefreshing = true;
    refreshPromise = (async (): Promise<boolean> => {
      try {
        const response = await $fetch<V1TokenResponse>(
          `${baseUrl}/auth/refresh`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: { refreshToken: storedRefresh },
          },
        );
        setTokens(response);
        return true;
      } catch {
        setTokens(null);
        return false;
      } finally {
        isRefreshing = false;
        refreshPromise = null;
      }
    })();

    return await refreshPromise;
  };

  const typedFetch = async <T>(
    endpoint: string,
    options: TypedFetchOptions = {},
  ): Promise<T> => {
    const executeRequest = async (isRetry = false): Promise<T> => {
      try {
        let fullUrl = `${baseUrl}${endpoint}`;
        if (options.query && Object.keys(options.query).length > 0) {
          const queryParams = new URLSearchParams();
          for (const [key, value] of Object.entries(options.query)) {
            if (value !== undefined && value !== null) {
              queryParams.append(key, String(value));
            }
          }
          fullUrl += `?${queryParams.toString()}`;
        }

        const accessToken = readStorage(ACCESS_TOKEN_KEY);
        const authHeader: Record<string, string> = accessToken
          ? { Authorization: `Bearer ${accessToken}` }
          : {};

        return await $fetch<T>(fullUrl, {
          method: (options.method || "GET") as
            "GET" | "POST" | "PUT" | "DELETE",
          body: options.body as Record<string, unknown> | undefined,
          headers: {
            "Content-Type": "application/json",
            ...authHeader,
            ...options.headers,
          },
          credentials: "include",
        });
      } catch (error: unknown) {
        const errorObj = error as Record<string, unknown>;
        const status =
          (errorObj.statusCode as number) || (errorObj.status as number) || 500;

        if (status === 401 && !isRetry) {
          const refreshed = await refreshToken();
          if (refreshed) {
            return executeRequest(true);
          }
        }

        const isNetworkError =
          error instanceof TypeError ||
          errorObj?.name === "NetworkError" ||
          errorObj?.code === "NETWORK_ERROR" ||
          (typeof navigator !== "undefined" && navigator.onLine === false);

        const isServerError = status >= 500 && status < 600;
        const isAuthError = status === 401 || status === 403;

        const apiError: ApiError = {
          message: (errorObj.message as string) || "API request failed",
          status,
          details: {
            ...((errorObj.data as Record<string, unknown>) || {}),
            error_type: isNetworkError
              ? "network_error"
              : isServerError
                ? "server_error"
                : isAuthError
                  ? "authentication_error"
                  : "api_error",
          },
        };
        throw apiError;
      }
    };

    return executeRequest();
  };

  // -------------------------------------------------------------------------
  // v1 Entities & Search
  // -------------------------------------------------------------------------

  const queryEntities = async (
    request: V1EntityRequest,
  ): Promise<V1Response> => {
    return typedFetch<V1Response>("/entity/", {
      method: "POST",
      body: request,
    });
  };

  const searchFulltext = async (
    q: string,
    entryType?: string,
    limit = 25,
  ): Promise<V1FulltextSearchResponse> => {
    const query: Record<string, string | number | boolean> = { q, limit };
    if (entryType) query.entry_type = entryType;
    return typedFetch<V1FulltextSearchResponse>("/search/", {
      method: "GET",
      query,
    });
  };

  const searchSimilar = async (
    entityId: string,
    limit = 10,
  ): Promise<V1SimilarSearchResponse> => {
    return typedFetch<V1SimilarSearchResponse>(
      `/search/similar/${encodeURIComponent(entityId)}`,
      {
        method: "GET",
        query: { limit },
      },
    );
  };

  const getSearchSuggestions = async (
    field: string,
    prefix = "",
    entryType?: string,
    limit = 15,
  ): Promise<V1SuggestResponse> => {
    const query: Record<string, string | number | boolean> = {
      field,
      prefix,
      limit,
    };
    if (entryType) query.entry_type = entryType;
    return typedFetch<V1SuggestResponse>("/search/suggest", {
      method: "GET",
      query,
    });
  };

  const searchEntities = async (
    options: SearchOptions = {},
  ): Promise<SearchApiResponse<Entity>> => {
    const pageSize = options.pageSize || 25;

    if (options.query && !options.sortBy) {
      const ft = await searchFulltext(options.query, undefined, pageSize);
      const items = ft.hits.map((hit, idx) =>
        normalizeRowToEntity(
          { id: hit.id, metadata: hit.metadata, entry_type: hit.entryType },
          idx,
        ),
      );
      return {
        data: items,
        total: ft.total,
        success: true,
        query: options.query,
        filters: options.filters,
        sortBy: options.sortBy,
        sortOrder: options.sortOrder,
      };
    }

    const req: V1EntityRequest = {
      page: { size: pageSize },
    };
    if (options.query) {
      req.search = options.query;
    }
    if (options.sortBy) {
      req.sort = {
        by: pathToTree(options.sortBy),
        order: options.sortOrder === "desc" ? "desc" : "asc",
      };
    }

    const resp = await typedFetch<V1Response>("/entity/query", {
      method: "POST",
      body: req,
    });
    const items = (resp.entities || []).map((row, idx) =>
      normalizeRowToEntity(row, idx),
    );
    return {
      data: items,
      total: resp.total ?? resp.returned ?? items.length,
      success: resp.status !== "error",
      query: options.query,
      filters: options.filters,
      sortBy: options.sortBy,
      sortOrder: options.sortOrder,
    };
  };

  const getEntityById = async (id: number | string): Promise<Entity> => {
    const resp = await typedFetch<V1Response>("/entity/get", {
      method: "POST",
      body: { id: String(id) },
    });
    const first = resp.entities?.[0];
    if (!first) {
      throw { message: `Entity ${id} not found`, status: 404 } as ApiError;
    }
    return normalizeRowToEntity(first, 0);
  };

  const getEntitiesByIds = async (
    ids: Array<number | string>,
  ): Promise<Entity[]> => {
    return Promise.all(ids.map((id) => getEntityById(id)));
  };

  const createEntity = async (
    _payload: CreateEntityPayload,
  ): Promise<Entity> => {
    throw {
      message:
        "Direct entity creation is handled by FileWatcher ingestion in v1",
      status: HttpStatusCode.NOT_IMPLEMENTED,
    } as ApiError;
  };
  const updateEntity = async (
    _id: number,
    _payload: UpdateEntityPayload,
  ): Promise<Entity> => {
    throw {
      message: "Direct entity update is not enabled in v1",
      status: HttpStatusCode.NOT_IMPLEMENTED,
    } as ApiError;
  };
  const updateMetadataLock = async (
    _entityId: number,
    _fieldName: string,
    _locked: boolean,
  ): Promise<{ success: boolean; message: string }> => {
    return { success: false, message: "Metadata lock is not enabled in v1" };
  };
  const deleteEntity = async (_id: number): Promise<undefined> => {
    throw {
      message: "Direct entity deletion is not enabled in v1",
      status: HttpStatusCode.NOT_IMPLEMENTED,
    } as ApiError;
  };
  const deleteEntities = async (
    _entityIds: number[],
  ): Promise<{
    success: boolean;
    deleted_count: number;
    not_found_count: number;
    message: string;
    deleted_ids?: number[];
    not_found_ids?: number[];
  }> => {
    return {
      success: false,
      deleted_count: 0,
      not_found_count: 0,
      message: "Direct entity deletion is not enabled in v1",
    };
  };

  // -------------------------------------------------------------------------
  // v1 Navigation & Field Registry
  // -------------------------------------------------------------------------

  const getRegisteredFields = async (
    entryType?: string,
  ): Promise<V1FieldRegistryResponse> => {
    const query: Record<string, string | number | boolean> = {};
    if (entryType) query.entry_type = entryType;
    return typedFetch<V1FieldRegistryResponse>("/navigation/fields", {
      method: "GET",
      query,
    });
  };

  const getSortingFields = async (): Promise<{
    fields: string[];
    count: number;
    info: string;
  }> => {
    const registry = await getRegisteredFields();
    const uniqueKeys = Array.from(
      new Set(registry.fields.map((f) => f.key)),
    ).sort();
    return {
      fields: uniqueKeys,
      count: uniqueKeys.length,
      info: "Loaded from /api/v1/navigation/fields",
    };
  };

  const getDropdownOptions = async (
    type: string,
  ): Promise<Array<{ entity_id: number; name: string; count?: number }>> => {
    const normalized = type.toLowerCase();
    const endpoint = NAV_CATEGORIES.has(normalized)
      ? `/navigation/${normalized}`
      : `/navigation/values/${encodeURIComponent(type)}`;
    const resp = await typedFetch<V1NavigationResponse>(endpoint, {
      method: "GET",
    });
    return resp.items.map((item, idx) => ({
      entity_id: idx + 1,
      name: item.name,
      count: item.count,
    }));
  };

  const getSchemaConfig = async (): Promise<Record<string, unknown>> => {
    const registry = await getRegisteredFields();
    const entryTypes = Array.from(
      new Set(registry.fields.map((f) => f.entryType)),
    );
    return {
      api_version: "v1",
      entry_types: entryTypes,
      fields: registry.fields,
      total_fields: registry.total,
    };
  };

  // -------------------------------------------------------------------------
  // v1 Analytics & Export
  // -------------------------------------------------------------------------

  const getAnalyticsHistogram = async (
    req: V1HistogramRequest,
  ): Promise<V1HistogramResponse> => {
    return typedFetch<V1HistogramResponse>("/analytics/histogram", {
      method: "POST",
      body: req,
    });
  };

  const getAnalyticsSummary = async (
    req: V1SummaryRequest,
  ): Promise<V1SummaryResponse> => {
    return typedFetch<V1SummaryResponse>("/analytics/summary", {
      method: "POST",
      body: req,
    });
  };

  const getAnalyticsCompare = async (
    req: V1CompareRequest,
  ): Promise<V1CompareResponse> => {
    return typedFetch<V1CompareResponse>("/analytics/compare", {
      method: "POST",
      body: req,
    });
  };

  const getAnalyticsCoverage = async (
    rowField = "process",
    colField = "ecm",
    entryType?: string,
  ): Promise<V1CoverageResponse> => {
    const query: Record<string, string | number | boolean> = {
      row_field: rowField,
      col_field: colField,
    };
    if (entryType) query.entry_type = entryType;
    return typedFetch<V1CoverageResponse>("/analytics/coverage", {
      method: "GET",
      query,
    });
  };

  const exportEntities = async (
    request: V1EntityRequest,
    format: V1ExportFormat = "json",
  ): Promise<string> => {
    return typedFetch<string>(`/export/${format}`, {
      method: "POST",
      body: request,
    });
  };

  const downloadEntitiesByIds = async (
    ids: Array<number | string>,
  ): Promise<Entity[]> => {
    return getEntitiesByIds(ids);
  };

  const downloadFilteredEntities = async (
    options: SearchOptions = {},
  ): Promise<Entity[]> => {
    const res = await searchEntities({
      ...options,
      pageSize: options.pageSize || 1000,
    });
    return res.data;
  };

  // -------------------------------------------------------------------------
  // v1 Auth, Collections & Redis-Backed Jobs
  // -------------------------------------------------------------------------

  const loginWithCredentials = async (
    username: string,
    password: string,
  ): Promise<V1TokenResponse> => {
    const tokens = await typedFetch<V1TokenResponse>("/auth/login", {
      method: "POST",
      body: { username, password },
    });
    setTokens(tokens);
    return tokens;
  };

  const initiateLogin = (): void => {
    window.location.href = `${baseUrl}/auth/me`;
  };

  const logoutUser = async (): Promise<{ logout_url: string }> => {
    setTokens(null);
    return { logout_url: "/" };
  };

  const getSessionStatus = async (): Promise<{
    authenticated: boolean;
    user?: Record<string, unknown>;
  }> => {
    const status = await typedFetch<V1AuthStatusResponse>("/auth/me", {
      method: "GET",
    });
    if (!status.authEnabled) {
      return {
        authenticated: true,
        user: {
          preferred_username: status.user?.username || "anonymous",
          roles: status.user?.roles || ["reader", "writer"],
          auth_disabled: true,
        },
      };
    }
    return {
      authenticated: status.authenticated,
      user: status.user
        ? {
            preferred_username: status.user.username,
            roles: status.user.roles,
          }
        : undefined,
    };
  };

  const manualRefreshToken = async (): Promise<boolean> => {
    return refreshToken();
  };

  const listCollections = async (): Promise<V1CollectionListResponse> => {
    return typedFetch<V1CollectionListResponse>("/collections/", {
      method: "GET",
    });
  };

  const createCollection = async (
    name: string,
    description = "",
    isPublic = false,
  ): Promise<V1CollectionDetail> => {
    return typedFetch<V1CollectionDetail>("/collections/", {
      method: "POST",
      body: { name, description, isPublic },
    });
  };

  const getCollection = async (
    collectionId: string,
  ): Promise<V1CollectionDetail> => {
    return typedFetch<V1CollectionDetail>(
      `/collections/${encodeURIComponent(collectionId)}`,
      { method: "GET" },
    );
  };

  const updateCollectionMembership = async (
    collectionId: string,
    add: string[],
    remove: string[] = [],
  ): Promise<{
    collectionId: string;
    added: number;
    removed: number;
    entryIds: string[];
  }> => {
    return typedFetch(
      `/collections/${encodeURIComponent(collectionId)}/events`,
      {
        method: "POST",
        body: { add, remove },
      },
    );
  };

  const submitJob = async (
    taskType: "export" | "analytics_histogram" | "analytics_summary",
    payload: Record<string, unknown>,
  ): Promise<V1JobRecord> => {
    return typedFetch<V1JobRecord>("/jobs/", {
      method: "POST",
      body: { taskType, payload },
    });
  };

  const getJobStatus = async (jobId: string): Promise<V1JobRecord> => {
    return typedFetch<V1JobRecord>(`/jobs/${encodeURIComponent(jobId)}`, {
      method: "GET",
    });
  };

  const getJobResult = async (jobId: string): Promise<V1JobResultResponse> => {
    return typedFetch<V1JobResultResponse>(
      `/jobs/${encodeURIComponent(jobId)}/result`,
      { method: "GET" },
    );
  };

  const apiGet = async <T>(
    url: string,
    query?: Record<string, string | number | boolean>,
  ): Promise<T> => {
    return typedFetch<T>(url, { method: "GET", query });
  };

  return {
    // Core
    typedFetch,
    apiGet,
    baseUrl,

    // Entities & Search
    queryEntities,
    searchEntities,
    searchFulltext,
    searchSimilar,
    getSearchSuggestions,
    getEntityById,
    getEntitiesByIds,
    createEntity,
    updateEntity,
    updateMetadataLock,
    deleteEntity,
    deleteEntities,

    // Navigation & Schema
    getRegisteredFields,
    getSortingFields,
    getDropdownOptions,
    getSchemaConfig,

    // Analytics & Export
    getAnalyticsHistogram,
    getAnalyticsSummary,
    getAnalyticsCompare,
    getAnalyticsCoverage,
    exportEntities,
    downloadEntitiesByIds,
    downloadFilteredEntities,

    // Auth, Collections & Jobs
    loginWithCredentials,
    initiateLogin,
    logoutUser,
    getSessionStatus,
    manualRefreshToken,
    listCollections,
    createCollection,
    getCollection,
    updateCollectionMembership,
    submitJob,
    getJobStatus,
    getJobResult,
  };
}
