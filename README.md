# State Grid Simulator

电网模拟系统 - 企业级 Web 应用框架

## 项目概述

本项目是一个高可用、高响应、高度扩展的 Web 应用框架，采用前后端分离架构，适用于电网模拟系统的开发。

### 核心特性

- **高可用**: 支持多实例部署、健康检查、故障自动恢复
- **高响应**: 异步非阻塞架构、连接池优化、缓存策略
- **高度扩展**: 模块化设计、插件机制、微服务就绪
- **前后端分离**: RESTful API、独立部署、并行开发
- **完善的日志系统**: 按时间轮转、自动清理、结构化格式

## 技术栈

### 后端

| 组件 | 技术 | 版本 |
|------|------|------|
| Web 框架 | FastAPI | ≥0.109.0 |
| ORM | SQLAlchemy | ≥2.0.0 |
| 数据库 | PostgreSQL / MySQL | - |
| 缓存 | Redis | ≥7.0 |
| 日志 | loguru | ≥0.7.0 |

### 前端

| 组件 | 技术 | 版本 |
|------|------|------|
| UI 框架 | React | ≥18.0.0 |
| 类型系统 | TypeScript | ≥5.0.0 |
| 构建工具 | Vite | ≥5.0.0 |
| 样式框架 | Tailwind CSS | ≥3.4.0 |
| 状态管理 | Zustand | ≥4.5.0 |

## 项目结构

```
StateGridSimulatorNew/
├── backend/                    # 后端项目
│   ├── src/                    # 源代码
│   │   ├── api/                # API 路由层
│   │   ├── core/               # 核心配置
│   │   ├── db/                 # 数据库配置
│   │   ├── models/             # 数据模型
│   │   ├── schemas/            # Pydantic 模式
│   │   ├── services/           # 业务服务层
│   │   ├── repositories/       # 数据访问层
│   │   └── utils/              # 工具模块
│   ├── config/                 # 配置文件
│   ├── tests/                  # 测试代码
│   └── Dockerfile              # Docker 构建文件
│
├── frontend/                   # 前端项目
│   ├── src/                    # 源代码
│   │   ├── components/         # 组件
│   │   ├── pages/              # 页面
│   │   ├── services/           # API 服务
│   │   ├── stores/             # 状态管理
│   │   └── types/              # 类型定义
│   └── Dockerfile              # Docker 构建文件
│
├── docker-compose.yml          # Docker Compose 配置
├── ARCHITECTURE.md             # 架构设计文档
└── README.md                   # 项目说明
```

## 快速开始

### 环境要求

- Python ≥3.10
- Node.js ≥18.0
- PostgreSQL ≥15 / MySQL ≥8.0
- Redis ≥7.0
- Docker & Docker Compose (可选)

### 本地开发

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements-dev.txt

# 配置环境变量
cp ../.env.example ../.env
# 编辑 .env 文件配置数据库等

# 启动开发服务器
python -m src.main
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### Docker 部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## API 文档

启动后端服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 日志格式

日志采用统一格式：

```
[2026-03-16 15:30:25.123] [INFO ] [main] [UserService:45] - 用户登录成功，ID:1001
```

日志文件按日期轮转，默认保留 30 天，自动压缩。

## 开发规范

### Git 分支策略

- `main`: 生产分支
- `develop`: 开发分支
- `feature/*`: 功能分支
- `fix/*`: 修复分支

### 提交规范

```
feat(auth): 实现 JWT 认证功能
fix(api): 修复用户登录接口参数验证
docs: 更新 API 文档
```

## 许可证

MIT License