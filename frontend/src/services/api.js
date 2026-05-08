/**
 * API client — thin wrapper around fetch for the FastAPI backend.
 */
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  if (res.status === 204) return null;
  return res.json();
}

// ── Projects ──────────────────────────────────────────────────────────────────
export const api = {
  // Projects
  getProjects: () => request("/projects/"),
  getProject: (id) => request(`/projects/${id}`),
  createProject: (data) => request("/projects/", { method: "POST", body: JSON.stringify(data) }),
  updateProject: (id, data) => request(`/projects/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteProject: (id) => request(`/projects/${id}`, { method: "DELETE" }),

  // Tasks
  getTasks: (projectId) => request(`/projects/${projectId}/tasks/`),
  createTask: (projectId, data) =>
    request(`/projects/${projectId}/tasks/`, { method: "POST", body: JSON.stringify(data) }),
  updateTask: (projectId, taskId, data) =>
    request(`/projects/${projectId}/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteTask: (projectId, taskId) =>
    request(`/projects/${projectId}/tasks/${taskId}`, { method: "DELETE" }),

  // Updates
  getUpdates: (projectId) => request(`/projects/${projectId}/updates/`),
  createUpdate: (projectId, data) =>
    request(`/projects/${projectId}/updates/`, { method: "POST", body: JSON.stringify(data) }),

  // AI
  summarize: (projectId) => request(`/projects/${projectId}/ai/summarize`, { method: "POST" }),
  extractTasks: (projectId, text) =>
    request(`/projects/${projectId}/ai/extract-tasks`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  generateReport: (projectId) =>
    request(`/projects/${projectId}/ai/report`, { method: "POST" }),

  // Chat (RAG)
  chat: (projectId, message, history = []) =>
    request("/chat", {
      method: "POST",
      body: JSON.stringify({ project_id: projectId, message, conversation_history: history }),
    }),

  // Documents
  getDocuments: (projectId) => request(`/projects/${projectId}/documents`),
  uploadDocument: (projectId, file) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/projects/${projectId}/documents`, {
      method: "POST",
      body: form,
    }).then((r) => r.json());
  },
};
