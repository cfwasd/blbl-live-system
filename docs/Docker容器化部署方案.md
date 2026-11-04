# 虚拟AI人物直播系统 —— Docker 容器化部署方案

| 部署形态 | 适用场景 | 优势特点 |
| :--- | :--- | :--- |
| **方案 A：All-in-One 单镜像容器（强烈推荐）** | 本地个人电脑 (Docker Desktop)、轻量云服务器 | 多阶段构建，单个容器包含后端 + 前端打包，一键启动，零网络配置烦恼 |
| **方案 B：Docker Compose 动静分离容器组** | 生产级云主机、反向代理集群 | Nginx 独立托管前端与 Live2D 大模型静态资源，FastAPI 专注于后端处理 |

---

## 1. 方案 A：All-in-One 多阶段构建（统一镜像）

### 1.1 架构拓扑
```text
┌────────────────────────────────────────────────────────┐
│               Docker 容器 (Port 8000)                   │
│                                                        │
│   FastAPI (Python 3.11-slim)                           │
│   ├── /api/*          ➔ RESTful 配置与控制接口          │
│   ├── /api/stream     ➔ SSE 弹幕与动作数据流            │
│   ├── /admin          ➔ 托管管理控制台静态资源          │
│   ├── /live           ➔ 托管编译后的 Vue3+Live2D 页面   │
│   └── /models         ➔ 挂载外部 Live2D 模型资产        │
└────────────────────────────────────────────────────────┘
```

### 1.2 Multi-stage Dockerfile 实现规范
```dockerfile
# ==========================================
# 阶段 1：构建 Vue 3 + Live2D 前端静态资源
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /build

# 安装依赖
COPY frontend/package*.json ./
RUN npm ci

# 复制前端源码并构建
COPY frontend/ ./
RUN npm run build

# ==========================================
# 阶段 2：构建 Python 生产环境
# ==========================================
FROM python:3.11-slim AS final

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# 安装必要的编译组件 (针对部分需要 C 扩展的包如 pyahocorasick)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 拷贝后端代码
COPY admin/ ./admin/
COPY configs/ ./configs/

# 从阶段 1 拷贝前端编译产物到静态托管目录
COPY --from=frontend-builder /build/dist ./admin/static/live

# 暴露端口
EXPOSE 8000

# 挂载卷声明 (用于持久化配置文件与 Live2D 模型)
VOLUME ["/app/configs", "/app/models"]

# 启动命令
CMD ["uvicorn", "admin.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 2. 方案 B：Docker Compose 编排方案

对于需要通过独立 Nginx 提供高性能静态资源缓存与 HTTPS 加密的场景，提供 `docker-compose.yml` 方案：

### 2.1 目录结构
```text
.
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── ... (FastAPI源码)
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── ... (Vue3源码)
├── models/             # 存放 Live2D 模型文件 (.model3.json 等)
└── configs/            # 存放 config.yaml, banned_words.txt
```

### 2.2 docker-compose.yml
```yaml
version: '3.8'

services:
  # Python 管理端与弹幕接入
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: live-ai-backend
    restart: unless-stopped
    environment:
      - ROOM_ID=123456
      - APP_ENV=production
      - ADMIN_TOKEN=my_secret_token_2026
    volumes:
      - ./configs:/app/configs
    ports:
      - "8000:8000"

  # 前端直播大屏与静态资源 (Nginx)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: live-ai-frontend
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ./models:/usr/share/nginx/html/models:ro
    depends_on:
      - backend
```

### 2.3 前端 Nginx 配置要点（支持 SSE 不缓冲与跨域）
```nginx
server {
    listen 80;
    server_name localhost;

    # 静态前端与 Live2D 模型
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # SSE 流式代理关键设置：禁止一切缓冲！
    location /api/stream {
        proxy_pass http://backend:8000/api/stream;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        
        # 核心防卡死参数：
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
        
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # RESTful API 代理
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 3. 极速启动与运维指令

### 3.1 本地一键构建与启动（基于方案 A）
```bash
# 1. 构建镜像
docker build -t virtual-ai-live:v0.2 .

# 2. 运行容器 (将本地模型目录和配置目录映射进容器)
docker run -d \
  --name ai-live \
  -p 8000:8000 \
  -v ${PWD}/configs:/app/configs \
  -v ${PWD}/models:/app/models \
  -e ROOM_ID=21452505 \
  --restart unless-stopped \
  virtual-ai-live:v0.2
```

### 3.2 访问入口
* **OBS / 直播姬 浏览器源 URL**：
  `http://localhost:8000/live`
* **管理端后台控制面板**：
  `http://localhost:8000/admin`
* **健康检查**：
  `http://localhost:8000/api/health`
