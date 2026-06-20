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

// ---- User management (admin) ----
export async function listUsers(params = {}) {
  const { data } = await api.get("/auth/users/", { params });
  return data; // { count, next, previous, results }
}

export async function createUser(payload) {
  const { data } = await api.post("/auth/users/", payload);
  return data;
}

export async function updateUser(id, payload) {
  const { data } = await api.patch(`/auth/users/${id}/`, payload);
  return data;
}

export async function listDepartments() {
  const { data } = await api.get("/auth/departments/");
  return data;
}

// ---- Helpdesk (module 2) ----
export async function listTickets(params = {}) {
  const { data } = await api.get("/helpdesk/tickets/", { params });
  return data; // { count, next, previous, results }
}

export async function getTicket(id) {
  const { data } = await api.get(`/helpdesk/tickets/${id}/`);
  return data;
}

export async function createTicket(payload) {
  const { data } = await api.post("/helpdesk/tickets/", payload);
  return data;
}

export async function rateTicket(id, payload) {
  // General users may only PATCH satisfaction fields on their own ticket.
  const { data } = await api.patch(`/helpdesk/tickets/${id}/`, payload);
  return data;
}

export async function assignTicket(id, assignee) {
  const { data } = await api.post(`/helpdesk/tickets/${id}/assign/`, { assignee });
  return data;
}

export async function resolveTicket(id) {
  const { data } = await api.post(`/helpdesk/tickets/${id}/resolve/`);
  return data;
}

export async function listTicketCategories() {
  const { data } = await api.get("/helpdesk/categories/");
  return data;
}

export async function listAssignees() {
  // Staff-scoped list of assignable users (avoids the admin-only users endpoint).
  const { data } = await api.get("/helpdesk/tickets/assignees/");
  return data; // array of {id, email, role, ...}
}

export async function addTicketComment(payload) {
  const { data } = await api.post("/helpdesk/comments/", payload);
  return data;
}

// ---- Assets (module 3) ----
export async function listAssets(params = {}) {
  const { data } = await api.get("/assets/items/", { params });
  return data; // { count, next, previous, results }
}

export async function getAsset(id) {
  const { data } = await api.get(`/assets/items/${id}/`);
  return data;
}

export async function createAsset(payload) {
  const { data } = await api.post("/assets/items/", payload);
  return data;
}

export async function updateAsset(id, payload) {
  const { data } = await api.patch(`/assets/items/${id}/`, payload);
  return data;
}

export async function assignAsset(id, holder, note = "") {
  const { data } = await api.post(`/assets/items/${id}/assign/`, { holder, note });
  return data;
}

export async function returnAsset(id) {
  const { data } = await api.post(`/assets/items/${id}/return/`);
  return data;
}

export async function lookupAsset(tag) {
  const { data } = await api.get("/assets/items/lookup/", { params: { tag } });
  return data;
}

export async function listAssetCategories() {
  const { data } = await api.get("/assets/categories/");
  return data;
}

export async function listAssetHolders(search = "") {
  // Staff-scoped, search-filtered, capped list of assignable users.
  const { data } = await api.get("/assets/items/holders/", {
    params: search ? { search } : {},
  });
  return data; // array of {id, email, role, ...}
}

export async function addMaintenanceRecord(payload) {
  const { data } = await api.post("/assets/maintenance/", payload);
  return data;
}
