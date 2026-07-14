import { useEffect, useState, useCallback } from "react";

/**
 * usePolling — a small reusable hook
 * Re-fetches `fetchFn` on a fixed interval and exposes a manual `refresh`.
 */
function usePolling(fetchFn, intervalMs = 8000) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const result = await fetchFn();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [fetchFn]);

  useEffect(() => {
    
    let id;
    const start = () => {
      refresh();
      id = setInterval(refresh, intervalMs);
    };
    const stop = () => {
      if (id) clearInterval(id);
    };
    const onVisibility = () => {
      if (document.visibilityState === "visible") start();
      else stop();
    };
    start();
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      stop();
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [refresh, intervalMs]);

  return { data, error, loading, refresh };
}

export default usePolling;