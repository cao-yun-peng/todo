import { useEffect, useMemo, useState } from "react";

import { api } from "./api.js";

const TOKEN_KEY = "todo_access_token";

function AuthView({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);

    try {
      if (mode === "register") {
        await api.register(username.trim(), password);
      }
      const result = await api.login(username.trim(), password);
      onAuthenticated(result.access_token);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  function switchMode(nextMode) {
    setMode(nextMode);
    setError("");
  }

  return (
    <main className="auth-shell">
      <section className="brand-panel" aria-label="产品介绍">
        <div className="brand-mark">✓</div>
        <p className="eyebrow">轻装上阵</p>
        <h1>把今天，<br />整理得刚刚好。</h1>
        <p className="brand-copy">
          写下重要的小事，完成一项，离轻松更近一点。
        </p>
        <div className="soft-orb" aria-hidden="true" />
      </section>

      <section className="auth-panel">
        <div className="auth-card">
          <p className="eyebrow">欢迎回来</p>
          <h2>{mode === "login" ? "登录你的清单" : "创建一个账户"}</h2>

          <div className="mode-switch" aria-label="账户操作">
            <button
              type="button"
              className={mode === "login" ? "active" : ""}
              onClick={() => switchMode("login")}
            >
              登录
            </button>
            <button
              type="button"
              className={mode === "register" ? "active" : ""}
              onClick={() => switchMode("register")}
            >
              注册
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <label>
              用户名
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                minLength="3"
                maxLength="50"
                autoComplete="username"
                placeholder="至少 3 个字符"
                required
              />
            </label>
            <label>
              密码
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                minLength="8"
                maxLength="128"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                placeholder="至少 8 个字符"
                required
              />
            </label>

            {error && <p className="form-error" role="alert">{error}</p>}

            <button className="primary-button" type="submit" disabled={busy}>
              {busy ? "请稍候…" : mode === "login" ? "进入清单" : "注册并登录"}
            </button>
          </form>
        </div>
      </section>
    </main>
  );
}

function TodoItem({ todo, token, onChanged, onRemoved, onUnauthorized }) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(todo.title);
  const [description, setDescription] = useState(todo.description ?? "");
  const [busy, setBusy] = useState(false);

  async function update(patch) {
    setBusy(true);
    try {
      const updated = await api.updateTodo(token, todo.id, {
        title: patch.title ?? todo.title,
        description: patch.description ?? todo.description,
        completed: patch.completed ?? todo.completed,
      });
      onChanged(updated);
      return true;
    } catch (error) {
      if (error.status === 401) onUnauthorized();
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function saveTitle(event) {
    event.preventDefault();
    const nextTitle = title.trim();
    if (!nextTitle) return;
    if (await update({ title: nextTitle, description: description.trim() || null })) {
      setEditing(false);
    }
  }

  async function remove() {
    setBusy(true);
    try {
      await api.deleteTodo(token, todo.id);
      onRemoved(todo.id);
    } catch (error) {
      if (error.status === 401) onUnauthorized();
    } finally {
      setBusy(false);
    }
  }

  return (
    <li className={`todo-item ${todo.completed ? "completed" : ""}`}>
      <button
        className="check-button"
        type="button"
        aria-label={todo.completed ? "标记为未完成" : "标记为已完成"}
        aria-pressed={todo.completed}
        disabled={busy}
        onClick={() => update({ completed: !todo.completed })}
      >
        {todo.completed && "✓"}
      </button>

      <div className="todo-content">
        {editing ? (
          <form className="edit-form" onSubmit={saveTitle}>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              maxLength="200"
              autoFocus
              required
            />
            <input
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              maxLength="500"
              placeholder="补充说明（可选）"
              aria-label="待办说明"
            />
            <button type="submit" disabled={busy}>保存</button>
            <button type="button" onClick={() => {
              setTitle(todo.title);
              setDescription(todo.description ?? "");
              setEditing(false);
            }}>
              取消
            </button>
          </form>
        ) : (
          <>
            <p className="todo-title">{todo.title}</p>
            {todo.description && <p className="todo-description">{todo.description}</p>}
          </>
        )}
      </div>

      {!editing && (
        <div className="todo-actions">
          <button type="button" onClick={() => {
            setTitle(todo.title);
            setDescription(todo.description ?? "");
            setEditing(true);
          }} disabled={busy} aria-label="编辑">
            编辑
          </button>
          <button className="danger" type="button" onClick={remove} disabled={busy} aria-label="删除">
            删除
          </button>
        </div>
      )}
    </li>
  );
}

function TodoView({ token, onLogout }) {
  const [user, setUser] = useState(null);
  const [todos, setTodos] = useState([]);
  const [filter, setFilter] = useState("all");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([api.me(token), api.listTodos(token)])
      .then(([currentUser, todoList]) => {
        if (!active) return;
        setUser(currentUser);
        setTodos(todoList);
      })
      .catch((requestError) => {
        if (!active) return;
        if (requestError.status === 401) onLogout();
        else setError(requestError.message);
      })
      .finally(() => active && setBusy(false));
    return () => { active = false; };
  }, [token, onLogout]);

  const visibleTodos = useMemo(() => {
    if (filter === "active") return todos.filter((todo) => !todo.completed);
    if (filter === "done") return todos.filter((todo) => todo.completed);
    return todos;
  }, [filter, todos]);

  const openCount = todos.filter((todo) => !todo.completed).length;

  async function createTodo(event) {
    event.preventDefault();
    const cleanTitle = title.trim();
    if (!cleanTitle) return;
    setBusy(true);
    setError("");
    try {
      const created = await api.createTodo(token, {
        title: cleanTitle,
        description: description.trim() || null,
      });
      setTodos((current) => [created, ...current]);
      setTitle("");
      setDescription("");
    } catch (requestError) {
      if (requestError.status === 401) onLogout();
      else setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  function replaceTodo(updated) {
    setTodos((current) => current.map((todo) => todo.id === updated.id ? updated : todo));
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="wordmark" href="#top" aria-label="今日清单首页">
          <span>✓</span> 今日清单
        </a>
        <div className="user-area">
          <span>{user?.username ?? "加载中…"}</span>
          <button type="button" onClick={onLogout}>退出</button>
        </div>
      </header>

      <section className="workspace" id="top">
        <div className="intro-row">
          <div>
            <p className="eyebrow">今天也值得认真对待</p>
            <h1>我的待办</h1>
          </div>
          <div className="count-card">
            <strong>{openCount}</strong>
            <span>项待完成</span>
          </div>
        </div>

        <form className="create-card" onSubmit={createTodo}>
          <div className="create-fields">
            <input
              className="title-input"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              maxLength="200"
              placeholder="接下来要做什么？"
              aria-label="待办标题"
              required
            />
            <input
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              maxLength="500"
              placeholder="补充说明（可选）"
              aria-label="待办说明"
            />
          </div>
          <button className="add-button" type="submit" disabled={busy}>＋ 添加</button>
        </form>

        {error && <p className="notice-error" role="alert">{error}</p>}

        <div className="list-toolbar">
          <div className="filters" aria-label="筛选待办">
            {[["all", "全部"], ["active", "进行中"], ["done", "已完成"]].map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={filter === value ? "active" : ""}
                onClick={() => setFilter(value)}
              >
                {label}
              </button>
            ))}
          </div>
          <span>共 {todos.length} 项</span>
        </div>

        {busy && !user ? (
          <div className="empty-state"><div className="loader" /><p>正在整理清单…</p></div>
        ) : visibleTodos.length > 0 ? (
          <ul className="todo-list">
            {visibleTodos.map((todo) => (
              <TodoItem
                key={todo.id}
                todo={todo}
                token={token}
                onChanged={replaceTodo}
                onRemoved={(id) => setTodos((current) => current.filter((item) => item.id !== id))}
                onUnauthorized={onLogout}
              />
            ))}
          </ul>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">○</div>
            <h2>{filter === "all" ? "清单还是空的" : "这里暂时没有事项"}</h2>
            <p>写下第一件想完成的小事吧。</p>
          </div>
        )}
      </section>
    </main>
  );
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));

  function authenticate(nextToken) {
    localStorage.setItem(TOKEN_KEY, nextToken);
    setToken(nextToken);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
  }

  return token
    ? <TodoView token={token} onLogout={logout} />
    : <AuthView onAuthenticated={authenticate} />;
}
