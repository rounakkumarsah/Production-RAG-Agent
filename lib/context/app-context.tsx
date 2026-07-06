"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

const ACTIVE_COLLECTION_KEY = "rag-active-collection";

interface AppContextValue {
  activeCollectionId: string | null;
  setActiveCollectionId: (id: string | null) => void;
  refreshKey: number;
  refresh: () => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [activeCollectionId, setActiveCollectionIdState] = useState<
    string | null
  >(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setActiveCollectionIdState(localStorage.getItem(ACTIVE_COLLECTION_KEY));
    setHydrated(true);
  }, []);

  const setActiveCollectionId = useCallback((id: string | null) => {
    setActiveCollectionIdState(id);
    if (id) localStorage.setItem(ACTIVE_COLLECTION_KEY, id);
    else localStorage.removeItem(ACTIVE_COLLECTION_KEY);
  }, []);

  const refresh = useCallback(() => {
    setRefreshKey((key) => key + 1);
  }, []);

  const value = useMemo(
    () => ({
      activeCollectionId: hydrated ? activeCollectionId : null,
      setActiveCollectionId,
      refreshKey,
      refresh,
    }),
    [
      activeCollectionId,
      hydrated,
      refresh,
      refreshKey,
      setActiveCollectionId,
    ]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within AppProvider");
  }
  return context;
}
