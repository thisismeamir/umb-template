/**
 * Modern API types for entity system
 * Compatible with the dynamic backend architecture
 */

/**
 * Standard HTTP status codes for API responses
 */
export enum HttpStatusCode {
    OK = 200,
    CREATED = 201,
    BAD_REQUEST = 400,
    UNAUTHORIZED = 401,
    FORBIDDEN = 403,
    NOT_FOUND = 404,
    INTERNAL_SERVER_ERROR = 500,
    NOT_IMPLEMENTED = 501,
}
/**
 * API Error response structure
 */
export interface ApiError {
    message: string;
    status: HttpStatusCode;
    details?: {
        error?: string;
        message?: string;
        error_type?: "network_error" | "server_error" | "authentication_error" | "api_error";
        [key: string]: unknown;
    };
    timestamp?: string;
}

/**
 * Extended error structure that handles different API error formats
 * Used for error handling in composables where error structure may vary
 */
export interface ExtendedApiError {
    message?: string;
    details?: {
        detail?: {
            message?: string;
        };
        message?: string;
        user_message?: string;
        [key: string]: unknown;
    };
    data?: {
        detail?: {
            message?: string;
        };
        message?: string;
        user_message?: string;
        details?: {
            message?: string;
        };
        [key: string]: unknown;
    };
    [key: string]: unknown;
}

/**
 * Entity from the backend (replaces hardcoded models)
 */
export interface Entity {
    entity_id: number;
    uuid?: string;
    name: string;
    created_at?: string;
    updated_at?: string;
    last_edited_at?: string;
    edited_by_name?: string;
    metadata?: Record<string, unknown>;
    [key: string]: unknown; // Allow any additional fields from dynamic schema
}

/**
 * Entity with populated relationship details
 */
export interface EntityWithDetails extends Entity {
    // Relationship fields will be dynamically populated based on schema
    [relationshipField: string]: unknown;
}

/**
 * Generic API response wrapper
 */
export interface ApiResponse<T = unknown> {
    data?: T;
    message?: string;
    error?: ApiError;
    success: boolean;
}

/**
 * Simplified response for infinite scroll
 */
export interface InfiniteScrollApiResponse<T = Entity> {
    data: T[];
    total: number;
    success: boolean;
}

/**
 * Search API response structure
 */
export interface SearchApiResponse<T = Entity> extends InfiniteScrollApiResponse<T> {
    query?: string;
    filters?: Record<string, unknown>;
    sortBy?: string;
    sortOrder?: "asc" | "desc";
}

/**
 * Utility types for API operations
 */
export type CreateEntityPayload = Omit<Entity, "entity_id" | "created_at" | "last_edited_at">;
export type UpdateEntityPayload = Partial<Omit<Entity, "entity_id" | "created_at">> & { entity_id: number };

/**
 * API endpoint configuration
 */
export interface ApiEndpoint {
    method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
    path: string;
    authenticated?: boolean;
}

/**
 * Typed fetch options for better type safety
 */
export interface TypedFetchOptions<T = unknown> {
    method?: string;
    body?: T;
    headers?: Record<string, string>;
    query?: Record<string, string | number | boolean>;
}

/**
 * Navigation dropdown option
 */
export interface DropdownOption {
    value: string | number;
    label: string;
    count?: number;
}

/**
 * Dynamic navigation configuration from backend
 */
export interface NavigationConfig {
    type: "dropdown" | "search" | "toggle";
    label: string;
    column: string;
    options?: DropdownOption[];
    placeholder?: string;
}

/**
 * Entity creation/update payload
 */
export interface EntityPayload {
    name: string;
    metadata?: Record<string, unknown>;
    [key: string]: unknown; // Dynamic fields based on schema
}

/**
 * Search and filter types
 */
export interface SearchParams {
    q?: string; // Search query
    page?: number;
    pageSize?: number;
    sortBy?: string;
    sortOrder?: "asc" | "desc";
    [filterKey: string]: unknown; // Dynamic filters
}

/**
 * Sort configuration
 */
export interface SortConfig {
    field: string;
    order: "asc" | "desc";
    label?: string;
}

/**
 * Filter configuration for dynamic entity types
 */
export interface FilterConfig {
    key: string;
    label: string;
    type: "select" | "text" | "date" | "number";
    options?: Array<{ id: number | string; name: string }>;
    placeholder?: string;
}

/**
 * Entity selection state
 */
export interface SelectionState {
    selectedIds: Set<number>;
    selectedEntities: Set<number>;
    expandedMetadata: Set<number>;
    selectAll: boolean;
    isIndeterminate: boolean;
    isDownloading: boolean;
}

/**
 * Entity metadata editing state
 */
export interface MetadataEditState {
    isEditing: boolean;
    editingEntityId: number | null;
    editingData: Record<string, unknown>;
    hasChanges: boolean;
    json: string;
    editedJson: string;
    originalMetadata?: Record<string, unknown>;
    isSaving?: boolean;
}

/**
 * Application state for entity management
 */
export interface EntityManagementState {
    entities: Entity[];
    loading: boolean;
    error: string | null;
    selection: SelectionState;
    metadata: MetadataEditState;
    totalCount: number;
    currentPage: number;
    pageSize: number;
}

/**
 * Bulk operation result
 */
export interface BulkOperationResult {
    success: boolean;
    successCount: number;
    failureCount: number;
    errors?: string[];
    message: string;
    data?: unknown;
    error?: string;
}

// Export Entity as primary interface


// -----------------------------------------------------------------------------
// API v1 Contracts (/api/v1/*)
// -----------------------------------------------------------------------------

export type V1MetadataPathTree = Record<string, unknown>;
export type V1MetadataConditionTree = Record<string, unknown>;
export type V1ExportFormat = "csv" | "json" | "yaml" | "toml" | "python";

export interface V1EntityRequest {
    contains?: V1MetadataPathTree;
    without?: V1MetadataPathTree;
    take?: V1MetadataPathTree;
    where?: V1MetadataConditionTree;
    search?: string;
    get?: { first?: number; last?: number; random?: number; uniform?: number };
    sort?: { by: V1MetadataPathTree; order?: "asc" | "desc" };
    page?: { size: number; cursor?: string };
    aggregate?: { by: V1MetadataPathTree; fn: "count" | "avg" | "min" | "max" | "sum" };
    distinct?: V1MetadataPathTree;
    count?: boolean;
    entry_type?: string | string[];
    id?: string;
    version?: number;
    versions?: { last?: number; first?: number; by?: string; type?: string; before?: string; after?: string };
    snapshot?: string;
}

export interface V1RawEntityRow {
    id: string;
    metadata: Record<string, unknown>;
    entry_type?: string;
    [key: string]: unknown;
}

export interface V1Response {
    apiInformation: { version: string; timestamp: string; requestId: string };
    validationResult: { valid: boolean; errors: string[]; warnings: string[] };
    status?: string;
    entities?: V1RawEntityRow[];
    returned?: number;
    total?: number;
    count?: number;
    aggregate?: { fn: string; path: string[]; value: number | null };
    distinct?: { path: string[]; values: unknown[] };
    versions?: Array<{ id: string; version: number; createdAt: string; createdBy: string; source: string }>;
    nextCursor?: string | null;
    hasMore?: boolean | null;
}

export interface V1NavigationItem {
    name: string;
    count: number;
    entryTypes: string[];
}

export interface V1NavigationResponse {
    category: string;
    field: string;
    items: V1NavigationItem[];
    total: number;
}

export interface V1FieldRegistryEntry {
    entryType: string;
    key: string;
    valueType: string;
    source: string;
}

export interface V1FieldRegistryResponse {
    fields: V1FieldRegistryEntry[];
    total: number;
}

export interface V1SearchHit {
    id: string;
    entryType: string;
    score: number;
    matchedFields: string[];
    metadata: Record<string, unknown>;
}

export interface V1FulltextSearchResponse {
    query: string;
    hits: V1SearchHit[];
    total: number;
}

export interface V1SimilarSearchResponse {
    sourceId: string;
    hits: V1SearchHit[];
    total: number;
}

export interface V1SuggestResponse {
    field: string;
    prefix: string;
    suggestions: string[];
    total: number;
}

export interface V1HistogramRequest {
    field: V1MetadataPathTree;
    bins?: number;
    entry_type?: string | string[];
    where?: V1MetadataConditionTree;
}

export interface V1HistogramResponse {
    path: string[];
    bins: Array<{ lower: number; upper: number; count: number }>;
    totalValues: number;
    min: number | null;
    max: number | null;
}

export interface V1SummaryRequest {
    groupBy: V1MetadataPathTree;
    metric?: V1MetadataPathTree;
    entry_type?: string | string[];
    where?: V1MetadataConditionTree;
}

export interface V1SummaryResponse {
    groupBy: string[];
    metric: string[] | null;
    groups: Array<{ group: unknown; count: number; sum?: number | null; mean?: number | null; min?: number | null; max?: number | null }>;
    totalEntries: number;
}

export interface V1CompareRequest {
    groupA: V1EntityRequest;
    groupB: V1EntityRequest;
    metrics: V1MetadataPathTree[];
}

export interface V1CompareResponse {
    countA: number;
    countB: number;
    deltas: Array<{ path: string[]; meanA: number | null; meanB: number | null; delta: number | null; ratio: number | null }>;
}

export interface V1CoverageResponse {
    rowField: string[];
    colField: string[];
    cells: Array<{ row: unknown; col: unknown; count: number }>;
    totalEntries: number;
}

export interface V1TokenResponse {
    accessToken: string;
    refreshToken: string;
    tokenType: string;
    expiresIn: number;
}

export interface V1UserPrincipal {
    username: string;
    roles: string[];
    authenticated: boolean;
}

export interface V1AuthStatusResponse {
    authEnabled: boolean;
    authenticated: boolean;
    user: V1UserPrincipal | null;
}

export interface V1CollectionSummary {
    id: string;
    name: string;
    description: string;
    owner: string;
    isPublic: boolean;
    memberCount: number;
    createdAt: string;
    updatedAt: string;
}

export interface V1CollectionDetail extends V1CollectionSummary {
    entryIds: string[];
}

export interface V1CollectionListResponse {
    collections: V1CollectionSummary[];
    total: number;
}

export interface V1JobRecord {
    id: string;
    taskType: "export" | "analytics_histogram" | "analytics_summary";
    status: "pending" | "running" | "done" | "failed";
    owner: string;
    error?: string | null;
    createdAt: string;
    updatedAt: string;
}

export interface V1JobResultResponse {
    id: string;
    taskType: "export" | "analytics_histogram" | "analytics_summary";
    status: "pending" | "running" | "done" | "failed";
    result?: unknown;
    error?: string | null;
}
