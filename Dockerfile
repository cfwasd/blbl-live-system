# ==========================================
# 阶段 1: 构建 Vue 3 前端静态产物
# ==========================================
FROM node:18-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ==========================================
# 阶段 2: 构建 Python 生产环境
# ==========================================
FROM python:3.11-slim AS final

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY admin/ ./admin/
COPY configs/ ./configs/
COPY models/ ./models/
COPY --from=frontend-builder /build/dist ./admin/static/live

EXPOSE 8000
VOLUME ["/app/configs", "/app/models"]

CMD ["uvicorn", "admin.main:app", "--host", "0.0.0.0", "--port", "8000"]
