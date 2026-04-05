import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../../Lib/Api";

export function usePaginatedApi<T>(
  url: string,
  search: string,
  pageSize = 50,
  deps: any[] = [],
  extraParams: Record<string, string | null> = {}
) {
  const [items, setItems] = useState<T[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);

      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        ...(search ? { search } : {}),
        ...Object.fromEntries(
          Object.entries(extraParams).filter(([_, v]) => v !== null)
        ),
      });

      const separator = url.includes("?") ? "&" : "?";
      const res = await apiFetch(`${url}${separator}${params.toString()}`);
      const data = await res.json();

      if (!cancelled) {
        setItems(data.items);
        setTotal(data.total);
        setLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [page, pageSize, search, reloadKey, url, ...deps]);

  return {
    items,
    page,
    pageSize,
    total,
    loading,
    setPage,
    refresh: useCallback(() => setReloadKey(k => k + 1), []),
  };
}
