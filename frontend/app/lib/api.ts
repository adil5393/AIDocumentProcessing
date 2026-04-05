export async function apiFetch(url: string, options: RequestInit = {}) {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const defaultBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  if (!url) {
    throw new Error("apiFetch: url is required");
  }

  if (url.startsWith("undefined")) {
    url = url.replace(/^undefined/, defaultBase);
  } else if (url.startsWith("/api") || url.startsWith("api/")) {
    url = `${defaultBase}${url.startsWith("/") ? "" : "/"}${url}`;
  }

  const isFormData = options.body instanceof FormData;
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    localStorage.removeItem("token");
    window.location.href = "/Login";
  }

  return res;
}
