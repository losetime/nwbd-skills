FROM python:3.12-slim

# 构建期镜像源，默认官方；国内服务器可用 build args 换成镜像站
ARG APT_MIRROR=deb.debian.org
ARG PYPI_INDEX=https://pypi.org/simple

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai \
    PATH="/app/.venv/bin:$PATH"

RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources; \
    fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl tzdata \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -i ${PYPI_INDEX} uv

# venv 安装依赖同样走构建期镜像源
ENV UV_DEFAULT_INDEX=${PYPI_INDEX} \
    UV_INDEX_URL=${PYPI_INDEX}

WORKDIR /app

# 先装依赖，源码变化时复用依赖层
# 用 uv 导出锁定版本，再交给 pip 安装：uv.lock 里写死了 PyPI 直链，
# 无法通过镜像源加速，pip 则可以按版本号从国内镜像拉取。
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev --no-emit-project --no-hashes -o /tmp/requirements.txt \
    && python -m venv /app/.venv \
    && /app/.venv/bin/pip install --no-cache-dir -i ${PYPI_INDEX} -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY entrypoint.sh ./

RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/api/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
