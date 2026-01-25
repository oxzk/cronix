# Cronix - 定时任务调度系统

基于 FastAPI 和 React 构建的轻量级、生产就绪的任务调度系统。支持 Cron 表达式调度，多种执行类型和通知渠道。

## ✨ 功能特性

- 🔐 **JWT 认证** - 支持双因素认证（2FA/TOTP）
- 📅 **Cron 调度** - 支持秒级精度的 6 字段 Cron 表达式
- 🚀 **多执行类型** - Shell、Python、Node.js
- 🔔 **多渠道通知** - Webhook、Telegram、钉钉
- 📊 **执行监控** - 任务执行历史和状态追踪
- ⏱️ **灵活配置** - 超时控制、失败重试、任务取消
- 🐳 **容器化部署** - Docker 支持
- ⚙️ **系统设置** - 通知配置管理、用户设置
- 🎨 **现代化 UI** - 基于 React + Radix UI 的管理界面

## 🚀 快速开始

### 一键启动

```bash
# 克隆项目
git clone <repository-url>
cd cronix

# 配置环境变量
cp .env.example .env

# 一键启动（自动构建前端并启动后端）
./start.sh
```

访问 `http://localhost:8000`

### 分步启动

#### 1. 构建前端

```bash
./build.sh
```

或手动构建：

```bash
cd web
npm install
npm run build
cd ..
```

#### 2. 启动后端

```bash
# 安装依赖
pip3 install -r requirements.txt

# 启动服务
python3 main.py
```

### 使用 Docker

```bash
# 构建镜像
docker build -t cronix .

# 运行容器
docker run -p 8000:8000 --env-file .env cronix
```

## 📁 项目结构

```
cronix/
├── web/                    # 前端源代码 (React + Vite + Radix UI)
│   ├── src/
│   │   ├── components/    # UI 组件
│   │   ├── pages/         # 页面组件
│   │   ├── api/           # API 接口
│   │   └── hooks/         # React Hooks
│   ├── vite.config.ts     # Vite 配置
│   └── package.json
├── public/                 # 前端构建输出（由后端提供服务）
├── src/                    # 后端源代码 (FastAPI)
│   ├── routes/            # API 路由
│   ├── services/          # 业务逻辑
│   ├── models/            # 数据模型
│   └── utils/             # 工具函数
├── main.py                 # 后端入口
├── build.sh                # 前端构建脚本
├── start.sh                # 一键启动脚本
└── requirements.txt        # Python 依赖
```

## 🌐 访问应用

启动后访问：`http://localhost:8000`

- **前端页面**: `/`, `/login`, `/tasks`, `/executions`, `/scripts`, `/settings`
- **健康检查**: `GET /health`
- **系统信息**: `GET /info`

## 📖 详细文档

- [构建和部署指南](BUILD_GUIDE.md) - 详细的构建和部署说明
- [部署文档](DEPLOYMENT.md) - 生产环境部署指南
- [Radix UI 重构说明](web/RADIX_UI_MIGRATION.md) - UI 组件库迁移文档

## ⚙️ 配置说明

`.env` 环境变量配置：

```env
DATABASE_URL=sqlite:///./cronix.db
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_HOURS=24
APP_NAME=Cronix
APP_PORT=8000
APP_DEBUG=False
```

## 🛠️ 技术栈

### 前端
- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Radix UI** - 无障碍 UI 组件
- **Tailwind CSS** - 样式框架
- **React Router** - 路由管理
- **Axios** - HTTP 客户端

### 后端
- **FastAPI** - 现代高性能 Web 框架
- **SQLAlchemy** - 异步 ORM
- **APScheduler** - 任务调度
- **PyJWT** - JWT 令牌认证
- **Bcrypt** - 密码哈希
- **PyOTP** - 双因素认证（TOTP）

## 🔒 安全特性

- JWT 令牌认证
- 双因素认证（2FA/TOTP）支持
- Bcrypt 密码哈希
- 认证中间件保护 API 端点
- 可配置的令牌过期时间

## 📝 日志

应用日志存储在 `data/logs/` 目录下，按日期命名：

- `data/logs/app_YYYYMMDD.log`

## 🔧 开发模式

### 前端开发

```bash
cd web
npm run dev
```

前端开发服务器会在 `http://localhost:5173` 启动。

### 后端开发

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📄 许可证

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题或建议，请通过 Issue 联系我们。
