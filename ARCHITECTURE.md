# Web 应用框架架构设计文档

## 一、架构概述

### 1.1 设计目标

本框架旨在构建一套**企业级 Web 应用开发基础设施**，具备以下核心特性：

| 特性 | 描述 |
|------|------|
| **高可用** | 支持多实例部署、健康检查、故障自动恢复 |
| **高响应** | 异步非阻塞架构、连接池优化、缓存策略 |
| **高度扩展** | 模块化设计、插件机制、微服务就绪 |
| **模块化** | 分层架构、依赖注入、松耦合组件 |
| **前后端分离** | RESTful API、独立部署、并行开发 |

### 1.2 技术架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户层 (Users)                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        负载均衡 (Nginx/Traefik)                          │
└─────────────────────────────────────────────────────────────────────────┘
                          │                    │
                          ▼                    ▼
┌──────────────────────────────┐    ┌──────────────────────────────┐
│      前端容器 (React)         │    │      前端容器 (React)         │
│  - Vite 构建                  │    │  - Vite 构建                 │
│  - Nginx 静态服务             │    │  - Nginx 静态服务            │
└──────────────────────────────┘    └──────────────────────────────┘
                          │
                          ▼ API 请求
┌─────────────────────────────────────────────────────────────────────────┐
│                        API 网关层 (FastAPI)                             │
│  - 请求路由、认证鉴权、限流熔断、日志记录                                  │
└─────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           业务服务层                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ 用户服务     │  │ 权限服务    │  │ 业务服务    │  │ 文件服务    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          数据访问层                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ PostgreSQL      │  │ Redis Cache     │  │ 文件存储         │         │
│  │ (主数据库)       │  │ (缓存/会话)     │  │ (MinIO/本地)    │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 二、后端架构设计

### 2.1 技术选型

| 组件 | 技术选型 | 版本要求 | 说明 |
|------|----------|----------|------|
| Web 框架 | FastAPI | ≥0.109.0 | 高性能异步框架，自动 API 文档 |
| ORM | SQLAlchemy | ≥2.0.0 | 异步 ORM，支持复杂查询 |
| 数据库驱动 | asyncpg / aiomysql | 最新 | 异步数据库驱动 |
| 数据验证 | Pydantic | ≥2.0.0 | 数据模型验证 |
| 配置管理 | pydantic-settings | 最新 | 类型安全配置 |
| 日志系统 | loguru | 最新 | 结构化日志 |
| 缓存 | Redis + aioredis | 最新 | 异步缓存 |
| 测试框架 | pytest + httpx | 最新 | 异步测试 |
| 代码规范 | Ruff + Black | 最新 | 代码检查与格式化 |

### 2.2 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (路由层)                        │
│  - 请求参数验证、响应格式化、路由定义                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer (服务层)                     │
│  - 业务逻辑处理、事务管理、跨模块协调                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Repository Layer (数据访问层)               │
│  - 数据库操作封装、查询构建、数据持久化                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Model Layer (模型层)                     │
│  - SQLAlchemy 模型定义、表结构映射                            │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 项目结构

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py                    # 应用入口
│   ├── app.py                     # FastAPI 应用实例
│   │
│   ├── api/                       # API 路由层
│   │   ├── __init__.py
│   │   ├── deps.py                # 依赖注入
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py          # 路由汇总
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py      # 健康检查
│   │           ├── auth.py        # 认证接口
│   │           └── users.py       # 用户接口
│   │
│   ├── core/                      # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py              # 配置管理
│   │   ├── security.py            # 安全模块 (JWT/密码)
│   │   ├── exceptions.py          # 自定义异常
│   │   └── middleware.py          # 中间件
│   │
│   ├── models/                    # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   └── base.py                # 基础模型类
│   │
│   ├── schemas/                   # Pydantic 模式
│   │   ├── __init__.py
│   │   └── base.py                # 基础响应模式
│   │
│   ├── services/                  # 业务服务层
│   │   └── __init__.py
│   │
│   ├── repositories/              # 数据访问层
│   │   └── __init__.py
│   │
│   ├── db/                        # 数据库配置
│   │   ├── __init__.py
│   │   ├── session.py             # 会话管理
│   │   └── init_db.py             # 数据库初始化
│   │
│   └── utils/                     # 工具模块
│       ├── __init__.py
│       └── logger.py              # 日志工具
│
├── config/
│   ├── config.yaml                # 应用配置
│   └── logging.yaml               # 日志配置
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # pytest 配置
│   └── test_api/
│       └── test_health.py
│
├── scripts/
│   └── init_db.py                 # 数据库初始化脚本
│
├── logs/                          # 日志目录
│   └── .gitkeep
│
├── alembic.ini                    # 数据库迁移配置
├── alembic/                       # 数据库迁移
│   ├── versions/
│   └── env.py
│
├── requirements.txt               # 生产依赖
├── requirements-dev.txt           # 开发依赖
├── pyproject.toml                 # 项目配置
├── ruff.toml                      # Ruff 配置
└── Dockerfile                     # Docker 构建文件
```

---

## 三、前端架构设计

### 3.1 技术选型

| 组件 | 技术选型 | 版本要求 | 说明 |
|------|----------|----------|------|
| UI 框架 | React | ≥18.0.0 | 声明式 UI |
| 类型系统 | TypeScript | ≥5.0.0 | 类型安全 |
| 构建工具 | Vite | ≥5.0.0 | 快速构建 |
| 样式框架 | Tailwind CSS | ≥3.4.0 | 原子化 CSS |
| 状态管理 | Zustand | 最新 | 轻量状态管理 |
| HTTP 客户端 | Axios | 最新 | HTTP 请求 |
| 路由 | React Router | ≥6.0.0 | 前端路由 |
| 图标库 | Lucide React | 最新 | 现代图标 |

### 3.2 项目结构

```
frontend/
├── src/
│   ├── main.tsx                   # 应用入口
│   ├── App.tsx                    # 根组件
│   ├── index.css                  # 全局样式
│   │
│   ├── components/                # 公共组件
│   │   ├── ui/                    # 基础 UI 组件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── index.ts
│   │   ├── layout/                # 布局组件
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── MainLayout.tsx
│   │   └── common/                 # 通用业务组件
│   │       ├── Loading.tsx
│   │       └── ErrorBoundary.tsx
│   │
│   ├── pages/                     # 页面组件
│   │   ├── Home.tsx
│   │   ├── Login.tsx
│   │   └── Dashboard.tsx
│   │
│   ├── hooks/                     # 自定义 Hooks
│   │   ├── useAuth.ts
│   │   └── useApi.ts
│   │
│   ├── services/                  # API 服务
│   │   ├── api.ts                 # Axios 实例
│   │   ├── auth.ts                # 认证服务
│   │   └── user.ts                # 用户服务
│   │
│   ├── stores/                    # 状态管理
│   │   ├── authStore.ts
│   │   └── appStore.ts
│   │
│   ├── types/                     # TypeScript 类型
│   │   ├── api.ts
│   │   └── models.ts
│   │
│   └── utils/                     # 工具函数
│       ├── format.ts
│       └── validate.ts
│
├── public/
│   └── favicon.ico
│
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
└── Dockerfile
```

---

## 四、日志系统设计

### 4.1 日志格式规范

```
[2026-03-16 15:30:25.123] [INFO ] [main] [UserService:45] - 用户登录成功，ID:1001
[2026-03-16 15:30:26.456] [ERROR] [Thread-2] [OrderService:78] - 创建订单失败：库存不足
```

**格式解析**：
- `[时间戳]` - 精确到毫秒，格式 `YYYY-MM-DD HH:mm:ss.SSS`
- `[级别]` - 日志级别，固定宽度 5 字符
- `[线程/协程名]` - 执行上下文标识
- `[模块:行号]` - 调用位置
- `消息内容` - 日志消息

### 4.2 日志配置

```yaml
# config/logging.yaml
logging:
  level: INFO
  format: "[{time:YYYY-MM-DD HH:mm:ss.SSS}] [{level: <5}] [{thread}] [{module}:{line}] - {message}"
  
  # 文件输出配置
  file:
    path: logs/app.log
    rotation: "00:00"           # 每天午夜轮转
    retention: "30 days"        # 保留 30 天
    compression: "zip"         # 压缩旧日志
    max_size: "50 MB"           # 单文件最大 50MB
    
  # 控制台输出
  console:
    enabled: true
    colorize: true
    
  # 按模块级别控制
  loggers:
    uvicorn: WARNING
    sqlalchemy: WARNING
    httpx: WARNING
```

### 4.3 日志工具实现

```python
# src/utils/logger.py
import sys
from loguru import logger
from pathlib import Path
from typing import Optional

class AppLogger:
    """应用日志管理器"""
    
    _initialized = False
    
    @classmethod
    def setup(
        cls,
        log_level: str = "INFO",
        log_dir: str = "logs",
        rotation: str = "00:00",
        retention: str = "30 days",
        compression: str = "zip",
        enable_console: bool = True
    ) -> None:
        """初始化日志配置"""
        if cls._initialized:
            return
            
        # 移除默认处理器
        logger.remove()
        
        # 日志格式
        log_format = (
            "[{time:YYYY-MM-DD HH:mm:ss.SSS}] "
            "[{level: <5}] "
            "[{thread}] "
            "[{module}:{line}] - {message}"
        )
        
        # 控制台输出
        if enable_console:
            logger.add(
                sys.stdout,
                format=log_format,
                level=log_level,
                colorize=True
            )
        
        # 确保日志目录存在
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 文件输出 - 按日期轮转
        logger.add(
            log_path / "app_{time:YYYY-MM-DD}.log",
            format=log_format,
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8"
        )
        
        # 错误日志单独文件
        logger.add(
            log_path / "error_{time:YYYY-MM-DD}.log",
            format=log_format,
            level="ERROR",
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8"
        )
        
        cls._initialized = True
        logger.info("日志系统初始化完成")
    
    @classmethod
    def get_logger(cls, name: str = "app"):
        """获取绑定名称的日志器"""
        return logger.bind(name=name)


# 便捷函数
def get_logger(name: str = "app"):
    return AppLogger.get_logger(name)
```

---

## 五、Docker 部署方案

### 5.1 容器架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                           │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │   Frontend    │  │   Backend     │  │   Database    │  │
│  │   (Nginx)     │  │   (FastAPI)   │  │   (PostgreSQL)│  │
│  │   Port: 80    │  │   Port: 8000  │  │   Port: 5432  │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  │
│                           │                                 │
│                    ┌──────┴──────┐                         │
│                    │    Redis    │                         │
│                    │  Port: 6379 │                         │
│                    └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - app-network
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/app
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./backend/logs:/app/logs
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=app
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    networks:
      - app-network
    restart: unless-stopped

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

---

## 六、API 设计规范

### 6.1 RESTful 规范

| HTTP 方法 | 路径 | 操作 | 说明 |
|-----------|------|------|------|
| GET | /api/v1/users | list | 获取用户列表 |
| POST | /api/v1/users | create | 创建用户 |
| GET | /api/v1/users/{id} | read | 获取单个用户 |
| PUT | /api/v1/users/{id} | update | 更新用户 |
| DELETE | /api/v1/users/{id} | delete | 删除用户 |

### 6.2 统一响应格式

```python
# 成功响应
{
    "code": 200,
    "message": "success",
    "data": { ... }
}

# 分页响应
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [...],
        "total": 100,
        "page": 1,
        "page_size": 20
    }
}

# 错误响应
{
    "code": 400,
    "message": "参数验证失败",
    "data": {
        "errors": [
            {"field": "email", "message": "邮箱格式不正确"}
        ]
    }
}
```

### 6.3 错误码规范

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

---

## 七、安全设计

### 7.1 认证授权

- **JWT Token** 认证机制
- **RBAC** 角色权限控制
- **Refresh Token** 刷新机制
- **密码加密** bcrypt 哈希

### 7.2 安全中间件

- CORS 跨域配置
- 请求限流
- SQL 注入防护
- XSS 防护
- CSRF Token

---

## 八、性能优化

### 8.1 后端优化

- 异步数据库连接池
- Redis 缓存热点数据
- 响应压缩 (Gzip)
- 数据库查询优化

### 8.2 前端优化

- 代码分割 (Code Splitting)
- 懒加载 (Lazy Loading)
- 静态资源 CDN
- Gzip 压缩

---

## 九、监控与运维

### 9.1 健康检查

```python
# /health 端点
{
    "status": "healthy",
    "version": "1.0.0",
    "components": {
        "database": "connected",
        "redis": "connected"
    }
}
```

### 9.2 日志监控

- 结构化日志输出
- 日志聚合 (ELK/Loki)
- 告警规则配置

---

## 十、开发规范

### 10.1 Git 分支策略

```
main (生产分支)
  │
  ├── develop (开发分支)
  │     │
  │     ├── feature/user-auth (功能分支)
  │     ├── feature/order-system
  │     │
  │     └── fix/login-error (修复分支)
```

### 10.2 提交规范

```
feat(auth): 实现 JWT 认证功能
fix(api): 修复用户登录接口参数验证
docs: 更新 API 文档
style: 代码格式化
refactor: 重构用户服务
test: 添加用户模块单元测试
chore: 更新依赖版本
```

### 10.3 代码规范

**Python**:
- 遵循 PEP8 规范
- 使用 Ruff 进行代码检查
- 使用 Black 进行代码格式化
- 类型注解必须完整

**TypeScript**:
- 使用 ESLint + Prettier
- 严格模式开启
- 接口优于类型别名

---

*文档版本: 1.0.0*
*最后更新: 2026-03-16*