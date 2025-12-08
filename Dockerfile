# Dockerfile for Fly.io or Docker deployment
# Multi-stage build for React + Django

# Stage 1: Build React app
FROM node:20-alpine AS react-builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY src ./src
COPY index.html ./
COPY vite.config.js ./
COPY tailwind.config.js ./
COPY postcss.config.js ./
RUN npm run build

# Stage 2: Django production
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 로그 디렉토리 생성
RUN mkdir -p /app/logs

# Python 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사 (React 빌드 제외)
COPY . .
# React 빌드 결과물 복사
COPY --from=react-builder /app/staticfiles/react ./staticfiles/react

# 정적 파일 수집
RUN python manage.py collectstatic --noinput || true

# 포트 노출
EXPOSE 8000

# Gunicorn 실행
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]

