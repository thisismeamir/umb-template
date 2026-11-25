export type MetadataPathTree = Record<string, unknown>;
export type MetadataConditionTree = Record<string, unknown>;
export type ExportFormat = "csv" | "json" | "yaml" | "toml" | "python";
export type AggregateFn = "count" | "avg" | "min" | "max" | "sum";
export type JobStatus = "pending" | "running" | "done" | "failed";
export type JobTaskType = "export" | "analytics_histogram" | "analytics_summary";

export interface EntityRequest {
  contains?: MetadataPathTree;
  without?: MetadataPathTree;
  take?: MetadataPathTree;
  where?: MetadataConditionTree;
  search?: string;
  get?: { first?: number; last?: number; random?: number; uniform?: number };
  sort?: { by: MetadataPathTree; order?: "asc" | "desc" };
  page?: { size: number; cursor?: string };
  aggregate?: { by: MetadataPathTree; fn: AggregateFn };
  distinct?: MetadataPathTree;
  count?: boolean;
  entry_type?: string | string[];
  id?: string;
  version?: number;
  versions?: { last?: number; first?: number; by?: string; type?: string; before?: string; after?: string };
  snapshot?: string;
}

export interface EntityRow {
  id: string;
  metadata: Record<string, unknown>;
  entry_type?: string;
}

export interface VersionSummary {
  id: string;
  version: number;
  createdAt: string;
  createdBy: string;
  source: string;
}

export interface EntityResponse {
  apiInformation: { version: string; timestamp: string; requestId: string };
  validationResult: { valid: boolean; errors: string[]; warnings: string[] };
  status?: string;
  entities?: EntityRow[];
  returned?: number;
  total?: number;
  count?: number;
  aggregate?: { fn: string; path: string[]; value: number | null };
  distinct?: { path: string[]; values: unknown[] };
  versions?: VersionSummary[];
  nextCursor?: string | null;
  hasMore?: boolean | null;
}

export interface NavigationItem {
  name: string;
  count: number;
  entryTypes: string[];
}

export interface NavigationResponse {
  category: string;
  field: string;
  items: NavigationItem[];
  total: number;
}

export interface FieldRegistryEntry {
  entryType: string;
  key: string;
  valueType: string;
  source: string;
}

export interface FieldRegistryResponse {
  fields: FieldRegistryEntry[];
  total: number;
}

export interface SearchHit {
  id: string;
  entryType: string;
  score: number;
  matchedFields: string[];
  metadata: Record<string, unknown>;
}

export interface FulltextSearchResponse {
  query: string;
  hits: SearchHit[];
  total: number;
}

export interface SimilarSearchResponse {
  sourceId: string;
  hits: SearchHit[];
  total: number;
}

export interface SuggestResponse {
  field: string;
  prefix: string;
  suggestions: string[];
  total: number;
}

export interface HistogramResponse {
  path: string[];
  bins: Array<{ lower: number; upper: number; count: number }>;
  totalValues: number;
  min: number | null;
  max: number | null;
}

export interface SummaryResponse {
  groupBy: string[];
  metric: string[] | null;
  groups: Array<{
    group: unknown;
    count: number;
    sum?: number | null;
    mean?: number | null;
    min?: number | null;
    max?: number | null;
  }>;
  totalEntries: number;
}

export interface CompareResponse {
  countA: number;
  countB: number;
  deltas: Array<{
    path: string[];
    meanA: number | null;
    meanB: number | null;
    delta: number | null;
    ratio: number | null;
  }>;
}

export interface CoverageResponse {
  rowField: string[];
  colField: string[];
  cells: Array<{ row: unknown; col: unknown; count: number }>;
  totalEntries: number;
}

export interface TokenResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface AuthStatusResponse {
  authEnabled: boolean;
  authenticated: boolean;
  user: { username: string; roles: string[]; authenticated: boolean } | null;
}

export interface CollectionSummary {
  id: string;
  name: string;
  description: string;
  owner: string;
  isPublic: boolean;
  memberCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface CollectionDetail extends CollectionSummary {
  entryIds: string[];
}

export interface JobRecord {
  id: string;
  taskType: JobTaskType;
  status: JobStatus;
  owner: string;
  error?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface JobResultResponse {
  id: string;
  taskType: JobTaskType;
  status: JobStatus;
  result?: unknown;
  error?: string | null;
}
