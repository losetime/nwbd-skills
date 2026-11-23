#!/bin/sh
# 容器入口：先执行数据库迁移，再启动应用。
# 迁移失败时直接退出，避免带病启动导致表结构不一致。
set -e

echo "[nwbd-skills] 执行数据库迁移"
alembic upgrade head

echo "[nwbd-skills] 启动 API"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
