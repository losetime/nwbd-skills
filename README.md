# nwbd-skills

内部技能（Claude Skills 风格的 `SKILL.md` 技能包）注册中心。提供技能包上传与校验、版本与发布管理、技能广场浏览、评论与审计，并通过 `/.well-known/skills.json` 对外提供技能索引，供下游工具消费。

## 功能

- **技能包上传与校验**：上传 zip，在落盘前完成结构、命名、体积与压缩比校验，失败不产生任何文件
- **版本管理**：新增版本、发布、弃用、恢复、删除，支持下载历史版本
- **技能广场**：按名称搜索、标签筛选、文件树预览、Markdown 渲染
- **协作**：评论、转移负责人
- **权限与审计**：普通用户 / 管理员两级角色，用户管理、审计日志
- **登录**：账号密码登录（JWT），可选钉钉扫码登录
- **对外索引**：`/.well-known/skills.json` 暴露已发布技能清单

## 目录结构

```
nwbd-skills/
├─ backend/          FastAPI 服务
│  ├─ app/modules/   auth / skill / audit / package / dingtalk
│  ├─ migrations/    Alembic 数据库迁移
│  └─ tests/         单元测试
├─ frontend/         Vue 3 + Vite 前端
├─ deploy/           docker compose、Nginx 配置、生产环境变量样例
├─ samples/          示例技能包（contract-review）
└─ scripts/          本地数据库初始化 SQL
```

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.12、FastAPI、SQLAlchemy 2、Alembic、PostgreSQL 16 |
| 认证 | JWT（HS256）、argon2 口令哈希 |
| 前端 | Vue 3、TypeScript、Vite 6、Pinia、Vue Router、Tailwind CSS 4 |
| 部署 | Docker Compose、Nginx、Uvicorn |

## 技能包格式

技能包是一个 zip，解压后根目录下必须有 `SKILL.md`：

```markdown
---
name: contract-review
description: 合同条款审查，输出风险点与修改建议
---

# 合同审查

正文写清执行步骤，细节放到 references/ 目录。
```

校验规则：

| 项目 | 要求 |
| --- | --- |
| 目录名 | `name` 只能是小写字母、数字与连字符，长度 1–64，且必须与包内根目录名一致 |
| description | 必填，不超过 1024 字符 |
| 路径 | 不允许绝对路径与 `..` 越界 |
| 体积 | 单包 ≤ 50 MB，单文件 ≤ 10 MB，条目数 ≤ 500，压缩比 ≤ 100 |
| 编码 | `SKILL.md` 必须是 UTF-8 |
| 链接 | 正文内的相对链接指向的文件最好真实存在（仅告警） |

包内含可执行脚本时会给出告警，请在发布前确认来源可信。体积上限可在 `backend/app/core/config.py` 调整。

## 本地开发

前置：Python 3.12、[uv](https://docs.astral.sh/uv/)、Node.js 20+、PostgreSQL 16。

### 1. 初始化数据库

```bash
psql -U postgres -f scripts/init-local-db.sql
```

该脚本创建角色 `skills`（密码 `skills_dev`）与数据库 `skills`。

### 2. 启动后端

```bash
cd backend
cp .env.example .env        # 按需修改数据库连接、JWT 密钥、初始管理员密码
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

- 健康检查：<http://127.0.0.1:8000/api/health>
- 接口文档：<http://127.0.0.1:8000/docs>
- 首次启动会按 `NWBD_SKILLS_BOOTSTRAP_ADMIN_*` 创建管理员，已存在则跳过
- 本地数据默认落在 `backend/data/`（`packages/` 存原始 zip，`extracted/` 存解压结果）

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev                 # http://localhost:18139
```

`vite.config.ts` 中的 `/api` 代理指向 `127.0.0.1:18138`（生产 Nginx 端口）。本地直连后端时，把代理目标改为 `http://127.0.0.1:8000`，或让后端直接监听 18138 端口。

### 测试与静态检查

```bash
cd backend
uv run pytest
uv run ruff check .

cd ../frontend
npm run type-check
```

## 生产部署

Compose 与 Nginx 配置中的路径按 `/opt/nwbd-skills` 硬编码，代码需放在该目录。

### 1. 准备目录

```bash
mkdir -p /opt/nwbd-skills/data /opt/nwbd-skills/frontend/dist /opt/nwbd-skills/deploy
```

### 2. 填写环境变量

```bash
cd /opt/nwbd-skills/deploy
cp .env.example .env
```

至少要改 `POSTGRES_PASSWORD`、`NWBD_SKILLS_JWT_SECRET`、`NWBD_SKILLS_BOOTSTRAP_ADMIN_PASSWORD` 三处，不能保留 `CHANGE_ME`。

### 3. 构建前端

```bash
cd /opt/nwbd-skills/frontend
npm ci
npm run build
cp -r dist/. /opt/nwbd-skills/frontend/dist/
```

### 4. 启动服务

```bash
cd /opt/nwbd-skills/deploy
docker compose up -d --build
```

访问 `http://<服务器IP>:18138`。容器内 API 迁移由 `entrypoint.sh` 在启动时自动执行 `alembic upgrade head`，迁移失败会直接退出，不会带病运行。

国内服务器可在 `deploy/.env` 中设置 `APT_MIRROR`、`PYPI_INDEX` 加速构建。升级时重新构建前端、`docker compose up -d --build` 即可，数据库数据在宿主机的 `/opt/nwbd-skills/data/pg`。

## 环境变量

后端读取 `NWBD_SKILLS_` 前缀的变量（见 `backend/app/core/config.py`），生产环境由 `deploy/.env` 注入。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `NWBD_SKILLS_DATABASE_URL` | `postgresql+psycopg://skills:skills@127.0.0.1:5432/skills` | 数据库连接串 |
| `NWBD_SKILLS_JWT_SECRET` | `dev-secret-change-me` | 令牌签名密钥，生产必须替换 |
| `NWBD_SKILLS_TOKEN_TTL_MINUTES` | `720` | 令牌有效期（分钟） |
| `NWBD_SKILLS_DATA_DIR` | `./data` | 技能包存储目录，容器内为 `/app/data` |
| `NWBD_SKILLS_BOOTSTRAP_ADMIN_USERNAME` | `admin` | 初始管理员账号 |
| `NWBD_SKILLS_BOOTSTRAP_ADMIN_PASSWORD` | `admin12345` | 初始管理员密码，仅首次创建时生效 |
| `NWBD_SKILLS_MAX_PACKAGE_BYTES` | 50 MB | 单个技能包上限 |
| `NWBD_SKILLS_MAX_FILE_BYTES` | 10 MB | 包内单个文件上限 |
| `NWBD_SKILLS_CORS_ORIGINS` | 空 | 前后端不同源时的允许来源，逗号分隔 |
| `NWBD_SKILLS_DINGTALK_CLIENT_ID` | 空 | 钉钉应用 AppKey，三项齐全才启用扫码登录 |
| `NWBD_SKILLS_DINGTALK_CLIENT_SECRET` | 空 | 钉钉应用 AppSecret |
| `NWBD_SKILLS_DINGTALK_REDIRECT_URI` | 空 | 登录回调地址 |
| `NWBD_SKILLS_DINGTALK_EXTRA_ADMINS` | 空 | 额外管理员，逗号分隔的钉钉 userId / unionId |

Compose 另需 `POSTGRES_DB`、`POSTGRES_USER`、`POSTGRES_PASSWORD`。

## 主要接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/auth/config` | 登录页配置（是否启用钉钉登录） |
| GET | `/api/auth/me` | 当前用户 |
| POST | `/api/auth/dingtalk/exchange` | 钉钉授权码换取令牌 |
| GET | `/api/skills` | 技能列表（搜索、筛选、分页） |
| POST | `/api/skills` | 上传新技能 |
| GET | `/api/skills/{name}` | 技能详情 |
| GET | `/api/skills/{name}/files` | 技能文件树 |
| GET | `/api/skills/{name}/file` | 读取单个文件内容 |
| POST | `/api/skills/{name}/versions` | 上传新版本 |
| POST | `/api/skills/{name}/versions/{version}/publish` | 发布版本 |
| POST | `/api/skills/{name}/versions/{version}/deprecate` | 弃用版本 |
| POST | `/api/skills/{name}/versions/{version}/restore` | 恢复版本 |
| DELETE | `/api/skills/{name}/versions/{version}` | 删除版本 |
| PATCH | `/api/skills/{name}/owner` | 转移负责人 |
| DELETE | `/api/skills/{name}` | 删除技能 |
| GET/POST | `/api/skills/{name}/comments` | 评论列表 / 发表评论 |
| GET | `/api/skills/{name}/download` | 下载技能包 |
| GET | `/api/stats` | 统计信息 |
| GET | `/api/users`、`PATCH /api/users/{id}` | 用户管理（管理员） |
| GET | `/api/audit` | 审计日志（管理员） |
| GET | `/.well-known/skills.json` | 对外技能索引 |

## 数据存储

- 元信息、版本、评论、审计记录存于 PostgreSQL，表结构由 Alembic 管理
- 原始 zip 按内容摘要存放在 `<data_dir>/packages/`，解压结果在 `<data_dir>/extracted/`
- `data/` 目录不入库，生产环境挂载宿主机目录做持久化

## 注意

- `.env` 含密钥，已被 `.gitignore` 排除，不要提交；需要新增变量时同步更新对应的 `.env.example`
- 新增数据库字段必须配 Alembic 迁移，启动时会自动执行
- 仓库统一使用 LF 换行（见 `.gitattributes`），避免容器内脚本因 CRLF 无法执行
