import type { CollectionDetail, CollectionSummary, EntityRow } from "~/types/api";

const LOCAL_SAVED_KEY = "umb_v2_saved_events";

export function useSavedEvents() {
  const api = useUmbApi();

  const savedMap = useState<Record<string, EntityRow>>("umb-saved-events", () => {
    if (typeof window === "undefined") return {};
    try {
      return JSON.parse(window.localStorage.getItem(LOCAL_SAVED_KEY) || "{}");
    } catch {
      return {};
    }
  });

  const collections = useState<CollectionSummary[]>("umb-collections", () => []);
  const activeCollection = useState<CollectionDetail | null>("umb-active-collection", () => null);

  const persistLocal = () => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(LOCAL_SAVED_KEY, JSON.stringify(savedMap.value));
  };

  const savedList = computed(() => Object.values(savedMap.value));
  const savedCount = computed(() => savedList.value.length);
  const isSaved = (id: string) => Boolean(savedMap.value[id]);

  const toggleSave = (row: EntityRow) => {
    if (savedMap.value[row.id]) {
      const next = { ...savedMap.value };
      delete next[row.id];
      savedMap.value = next;
    } else {
      savedMap.value = { ...savedMap.value, [row.id]: row };
    }
    persistLocal();
  };

  const saveMany = (rows: EntityRow[]) => {
    const next = { ...savedMap.value };
    for (const r of rows) next[r.id] = r;
    savedMap.value = next;
    persistLocal();
  };

  const clearSaved = () => {
    savedMap.value = {};
    persistLocal();
  };

  const refreshCollections = async () => {
    try {
      const res = await api.listCollections();
      collections.value = res.collections;
    } catch {
      // Keep local saved list usable even if auth is required
    }
  };

  const createCollectionFromSaved = async (name: string, description = "", isPublic = false) => {
    const created = await api.createCollection(name, description, isPublic);
    const ids = Object.keys(savedMap.value);
    if (ids.length > 0) {
      await api.updateCollectionEvents(created.id, ids);
    }
    await refreshCollections();
    return created;
  };

  const openCollection = async (id: string) => {
    activeCollection.value = await api.getCollection(id);
    return activeCollection.value;
  };

  const addToCollection = async (collectionId: string, entryIds: string[]) => {
    const res = await api.updateCollectionEvents(collectionId, entryIds);
    await refreshCollections();
    if (activeCollection.value?.id === collectionId) {
      activeCollection.value = { ...activeCollection.value, entryIds: res.entryIds, memberCount: res.entryIds.length };
    }
    return res;
  };

  const removeFromCollection = async (collectionId: string, entryId: string) => {
    const res = await api.updateCollectionEvents(collectionId, [], [entryId]);
    await refreshCollections();
    if (activeCollection.value?.id === collectionId) {
      activeCollection.value = { ...activeCollection.value, entryIds: res.entryIds, memberCount: res.entryIds.length };
    }
    return res;
  };

  const removeCollection = async (collectionId: string) => {
    await api.deleteCollection(collectionId);
    if (activeCollection.value?.id === collectionId) activeCollection.value = null;
    await refreshCollections();
  };

  return {
    savedList,
    savedCount,
    isSaved,
    toggleSave,
    saveMany,
    clearSaved,
    collections,
    activeCollection,
    refreshCollections,
    createCollectionFromSaved,
    openCollection,
    addToCollection,
    removeFromCollection,
    removeCollection,
  };
}
