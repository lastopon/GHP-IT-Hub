import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

const ACCESS_KEY = "ghp_access";
const REFRESH_KEY = "ghp_refresh";

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set({ access, refresh }) {
    if (access) localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

// Attach the access token to every request.
api.interceptors.request.use((config) => {
  const token = tokenStore.access;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401, try a single refresh, then replay the original request.
let refreshing = null;
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retried && tokenStore.refresh) {
      original._retried = true;
      try {
        refreshing =
          refreshing ||
          axios.post(`${API_BASE}/auth/token/refresh/`, {
            refresh: tokenStore.refresh,
          });
        const { data } = await refreshing;
        refreshing = null;
        tokenStore.set({ access: data.access });
        original.headers.Authorization = `Bearer ${data.access}`;
        return api(original);
      } catch (e) {
        refreshing = null;
        tokenStore.clear();
        window.location.href = "/login";
        return Promise.reject(e);
      }
    }
    return Promise.reject(error);
  },
);

export async function login(email, password) {
  const { data } = await api.post("/auth/login/", { email, password });
  tokenStore.set({ access: data.access, refresh: data.refresh });
  return data.user;
}

export async function fetchMe() {
  const { data } = await api.get("/auth/users/me/");
  return data;
}

export function logout() {
  tokenStore.clear();
}
