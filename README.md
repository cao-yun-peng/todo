# Todo

一个 FastAPI + React 的小型待办应用，包含账户注册、登录和个人 Todo 管理。

## 启动后端

```powershell
.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8001
```

后端运行在 `http://127.0.0.1:8001`。

## 启动前端

另开一个终端：

```powershell
cd frontend
npm install
npm run dev
```

然后访问 `http://127.0.0.1:5173`。开发服务器已经配置代理，会将 API 请求转发到本地 FastAPI 服务。

如需连接其他地址的后端，可在 `frontend/.env.local` 中配置：

```text
VITE_API_BASE_URL=https://your-api.example.com
```

## 测试与构建

```powershell
pytest
cd frontend
npm run build
```
