import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";

type PaginatedResponse<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
};

export function usePaginatedApi<T>(
  url: string,
  search: string,
  pageSize = 50,
  deps: any[] = []
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
        ...(search ? { search } : {})
      });
      const res = await apiFetch(`${url}?${params.toString()}`);
      const data = await res.json();

      if (!cancelled) {
        setItems(data.items);
        setTotal(data.total);
      }

      setLoading(false);
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [page, pageSize, search,reloadKey]);

  return {
    items,
    page,
    pageSize,
    total,
    loading,
    setPage,
    refresh: () => setReloadKey(k => k + 1), // 👈 THIS
  };
}

