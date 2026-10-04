const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

function messageFrom(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).filter(Boolean).join("；");
  }
  return "请求失败，请稍后重试";
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const error = new Error(messageFrom(body.detail));
    error.status = response.status;
    throw error;
  }

  return response.status === 204 ? null : response.json();
}

function authHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

export const api = {
  register(username, password) {
    return request("/users/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
  },

  login(username, password) {
    const body = new URLSearchParams({ username, password });
    return request("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
  },

  me(token) {
    return request("/users/me", { headers: authHeaders(token) });
  },

  listTodos(token) {
    return request("/todos", { headers: authHeaders(token) });
  },

  createTodo(token, data) {
    return request("/todos", {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify(data),
    });
  },

  updateTodo(token, id, data) {
    return request(`/todos/${id}`, {
      method: "PUT",
      headers: authHeaders(token),
      body: JSON.stringify(data),
    });
  },

  deleteTodo(token, id) {
    return request(`/todos/${id}`, {
      method: "DELETE",
      headers: authHeaders(token),
    });
  },
};
