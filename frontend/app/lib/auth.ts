export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function isLoggedIn() {
  return getToken();
}

export function logout() {
  localStorage.removeItem("token");
  window.location.href = "/login";
}
