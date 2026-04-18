# Web Rebuild V2（全新独立项目）

这是按你的要求新建的独立重写项目，和 `web_migration` 完全隔离。

## 目录

- `backend/`：FastAPI 后端（重写）
- `frontend/`：Vue + Element Plus 前端（重写）

## 后端启动

```bash
cd web_rebuild_v2/backend
py -3 -m uvicorn app.main:app --host 127.0.0.1 --port 18081 --reload
```

## 前端访问

后端启动后访问：

- `http://127.0.0.1:18081/`
