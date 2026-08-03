# 产线电脑巡检系统

面向制造业工厂的**产线电脑合规巡检平台**。运维人员定期检查产线电脑的防毒软件和入域状态，异常时自动触发签核工单流转，支持邮件通知、图片取证、Excel 批量导入导出。

---

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.11 + FastAPI + SQLAlchemy (async) |
| 前端 | Vue 3 + TypeScript + Element Plus |
| 数据库 | PostgreSQL 15 |
| 对象存储 | MinIO (S3 兼容) |
| 认证 | JWT (python-jose) |
| 部署 | Docker Compose 一键编排 |

---

## 快速开始

### 前置条件

- Docker & Docker Compose
- （可选）WSL2（Windows 用户推荐）

### 1. 克隆仓库

```bash
git clone https://github.com/Sam95271230/inspection-system.git
cd inspection-system
```

### 2. 配置环境变量

编辑 `.env` 文件，修改以下关键配置：

```env
# 数据库（可保持默认）
POSTGRES_USER=inspection_user
POSTGRES_PASSWORD=inspection_pass
POSTGRES_DB=inspection_db

# JWT 密钥（生产环境务必修改！）
JWT_SECRET=your-super-secret-jwt-key

# MinIO（可保持默认）
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# SMTP 邮件（可选，不配置则不发送通知）
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USER=your-email@qq.com
SMTP_PASSWORD=your-auth-code
```

### 3. 启动服务

```bash
docker compose up -d
```

启动顺序（自动按健康检查）：`PostgreSQL + MinIO → Backend → Frontend`

### 4. 初始化管理员

首次部署需要创建超级管理员账号。在 `.env` 中设置 `ALLOW_INIT_ADMIN=true`，然后：

```bash
curl -X POST http://localhost:8080/api/v1/auth/init-admin \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password","real_name":"管理员"}'
```

初始化完成后建议移除 `ALLOW_INIT_ADMIN=true`。

### 5. 访问系统

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost:8081 |
| 后端 API 文档 | http://localhost:8080/docs |
| MinIO 控制台 | http://localhost:9001 |

---

## 功能架构

### 用户与权限

```
超级管理员
  ├── 全部厂区可见，所有功能无限制
  ├── 用户管理 / 厂区字典 / 邮件配置

厂区 Leader
  ├── 仅授权厂区可见
  ├── 巡检录入、查询、异常签核（审批/驳回）

厂区 Member
  ├── 仅授权厂区可见
  ├── 巡检录入、查询、处理分配给自己的工单
```

- 数据按厂区隔离，普通用户只能看到所属厂区的数据
- 一个用户可在多个厂区担任不同角色

### 功能模块

#### 1. 巡检录入

- **单个录入** — 厂区→线别→站别三级联动，IP 自动校验，巡检证据图片上传
- **批量导入** — 上传 ZIP 包（Excel + 图片文件夹），自动解析创建记录

#### 2. 巡检记录查询

- 多条件筛选（厂区/线别/站别/状态/时间）
- 分页列表 + 详情弹窗（图片预览）
- **Excel 导出** — 巡检证据图片直接嵌入单元格

#### 3. 异常签核（工单流转）

```
巡检提交 → 防毒≠正常 或 入域∉{已入域,不适用}
         → 自动创建工单 → 自动分配Member
         → Member处理 → Leader签核 → 通过/驳回
```

完整状态机：`PENDING → PROCESSING → PENDING_SIGNOFF → CLOSED / REJECTED`

#### 4. 厂区字典管理

- 三级结构（厂区→线别→站别），树形卡片展示
- 完整 CRUD（新增/编辑/删除），代码唯一性校验
- 删除保护（已被巡检记录引用时拒绝）
- Excel 批量导入（带预览 + 模板下载）

#### 5. 用户管理

- 用户 CRUD + 启/禁 + 删除保护
- 厂区授权 + 角色分配（Member / Leader）
- 超级管理员开关

#### 6. 邮件通知

- SMTP 配置（TLS/SSL 自动探测）
- 工单关键节点自动通知相关人员
- HTML 邮件（含巡检详情 + 图片 + 系统链接）
- 测试发送功能

---

## 巡检检查项

| 检查项 | 可选值 | 触发异常 |
|--------|--------|----------|
| 防毒软件 | 正常 / 异常 / 未安装 | ≠ 正常 |
| 入域状态 | 已入域 / 未入域 / 不适用 | 既不是"已入域"也不是"不适用" |

**异常判定**：防毒 ≠ NORMAL **或** 入域 ∉ {JOINED, NOT_APPLICABLE} → 自动创建异常工单

---

## API 概览

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/auth/init-admin` | POST | 初始化管理员（需环境变量启用） |
| `/api/v1/inspections` | GET/POST | 巡检记录列表 / 创建 |
| `/api/v1/inspections/upload` | POST | 上传巡检图片 |
| `/api/v1/inspections/batch-import` | POST | 批量导入 ZIP |
| `/api/v1/inspections/export` | GET | 导出 Excel |
| `/api/v1/exceptions` | GET | 异常工单列表 |
| `/api/v1/exceptions/{id}/assign` | POST | 分配处理人 |
| `/api/v1/exceptions/{id}/process` | POST | 提交处理结果 |
| `/api/v1/exceptions/{id}/approve` | POST | 签核通过 |
| `/api/v1/exceptions/{id}/reject` | POST | 驳回 |
| `/api/v1/exceptions/{id}/reprocess` | POST | 重新处理 |
| `/api/v1/dict/tree` | GET | 厂区字典树 |
| `/api/v1/dict/plant` | POST | 新增厂区 |
| `/api/v1/dict/plant/{id}` | PUT/DELETE | 修改/删除厂区 |
| `/api/v1/dict/line` | POST | 新增线别 |
| `/api/v1/dict/line/{id}` | PUT/DELETE | 修改/删除线别 |
| `/api/v1/dict/station` | POST | 新增站别 |
| `/api/v1/dict/station/{id}` | PUT/DELETE | 修改/删除站别 |
| `/api/v1/users` | GET/POST | 用户列表 / 创建 |
| `/api/v1/users/{id}` | PUT/DELETE | 修改/删除用户 |
| `/api/v1/email-config` | GET/PUT | 邮件配置 |
| `/api/v1/roles` | GET | 角色列表 |
| `/api/v1/health` | GET | 健康检查 |

---

## 项目结构

```
inspection-system/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── database.py          # 数据库连接
│   │   ├── dependencies.py      # 权限校验依赖
│   │   ├── constants.py         # 全局常量
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── routers/             # API 路由
│   │   ├── schemas/             # Pydantic 校验
│   │   ├── security/            # 密码加密
│   │   └── utils/               # JWT / MinIO / 响应模板
│   ├── alembic/                 # 数据库迁移
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                 # API 请求封装
│   │   ├── components/          # 公共组件
│   │   ├── composables/         # 组合式函数
│   │   ├── constants/           # 前端常量
│   │   ├── router/              # 路由配置
│   │   ├── stores/              # Pinia 状态
│   │   └── views/               # 页面组件
│   ├── nginx.conf               # Nginx 反向代理
│   └── Dockerfile
├── init-db/                     # 数据库初始化脚本
├── docker-compose.yml
├── .env                         # 环境变量（不提交 Git）
└── README.md
```

---

## 安全设计

- **图片安全** — MinIO Bucket 不设公开读，使用预签名 URL（1h 有效）
- **JWT 认证** — 所有 API 需 Bearer Token，401 自动拦截
- **数据隔离** — 非管理员强制按授权厂区过滤数据
- **密码加密** — bcrypt 哈希存储
- **管理员保护** — `init-admin` 接口需要环境变量开启，已有管理员后自动拒绝
- **删除保护** — 被巡检/工单引用的字典和用户不可删除

---

## License

MIT
