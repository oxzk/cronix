# 通知配置表迁移说明

## 数据库变更

### 1. 新增表：Notification（通知配置表）

```sql
CREATE TABLE cm_notifications (
    id SERIAL PRIMARY KEY,
    notify_type VARCHAR(20) NOT NULL UNIQUE,
    config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cm_notifications_type ON cm_notifications(notify_type);
```

### 2. 修改表：Task（任务表）

**新增字段：**
```sql
ALTER TABLE cm_tasks 
ADD COLUMN notification_ids INTEGER[] NULL;
```

### 3. 删除表：TaskNotification（任务通知关联表）

```sql
DROP TABLE IF EXISTS cm_task_notifications CASCADE;
```

## 迁移步骤

### 方案1：全新安装（推荐）

如果是新项目或可以清空数据：

```sql
-- 删除旧表
DROP TABLE IF EXISTS cm_task_notifications CASCADE;

-- 创建通知配置表
CREATE TABLE cm_notifications (
    id SERIAL PRIMARY KEY,
    notify_type VARCHAR(20) NOT NULL UNIQUE,
    config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cm_notifications_type ON cm_notifications(notify_type);

-- 修改任务表，添加通知配置ID数组字段
ALTER TABLE cm_tasks 
ADD COLUMN notification_ids INTEGER[] NULL;
```

### 方案2：保留现有数据迁移

如果需要保留现有的任务通知配置：

```sql
-- 1. 创建通知配置表
CREATE TABLE cm_notifications (
    id SERIAL PRIMARY KEY,
    notify_type VARCHAR(20) NOT NULL UNIQUE,
    config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_cm_notifications_type ON cm_notifications(notify_type);

-- 2. 迁移现有通知配置到新表（按类型去重，保留第一个配置）
INSERT INTO cm_notifications (notify_type, config)
SELECT DISTINCT ON (notify_type) 
    notify_type,
    config
FROM cm_task_notifications
ORDER BY notify_type, id;

-- 3. 添加新字段到任务表
ALTER TABLE cm_tasks 
ADD COLUMN notification_ids INTEGER[] NULL;

-- 4. 迁移任务的通知配置关联
UPDATE cm_tasks t
SET notification_ids = (
    SELECT ARRAY_AGG(DISTINCT n.id)
    FROM cm_task_notifications tn
    JOIN cm_notifications n 
        ON n.notify_type = tn.notify_type
    WHERE tn.task_id = t.id
);

-- 5. 验证数据后删除旧表
-- DROP TABLE cm_task_notifications;
```

## API 变更

### 新增接口：设置管理

- `GET /settings/notifications` - 获取所有通知配置
- `PUT /settings/notifications/{id}` - 更新通知配置
- `PUT /settings/user` - 更新用户设置（密码、2FA配置）
  - 支持字段：
    - `password` - 更新密码
    - `is_2fa_enabled` - 启用/禁用2FA
    - `totp_secret` - 设置TOTP密钥

### 修改接口：任务管理

**创建/更新任务时的请求体变更：**

```json
{
  "name": "test",
  "notification_ids": [1, 2]
}
```

**任务响应体变更：**

```json
{
  "id": 1,
  "notifications": [
    {
      "id": 1,
      "notify_type": "webhook",
      "config": {"url": "http://example.com"},
      "created_at": "2026-01-21T00:00:00Z",
      "updated_at": "2026-01-21T00:00:00Z"
    }
  ]
}
```

## 使用示例

### 1. 获取所有通知配置

```bash
curl -X GET http://localhost:8000/settings/notifications
```

### 2. 更新通知配置

```bash
curl -X PUT http://localhost:8000/settings/notifications/1 \
  -H "Content-Type: application/json" \
  -d '{
    "notify_type": "webhook",
    "config": {"url": "http://example.com/webhook"}
  }'
```

### 3. 创建任务并关联通知

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "backup",
    "cron_expression": "0 0 2 * * *",
    "execution_type": "shell",
    "command": "backup.sh",
    "notification_ids": [1, 2]
  }'
```

### 4. 更新用户密码

```bash
curl -X PUT http://localhost:8000/settings/user \
  -H "Content-Type: application/json" \
  -d '{
    "password": "new_password"
  }'
```

### 5. 更新用户2FA设置

```bash
# 启用2FA并设置TOTP密钥
curl -X PUT http://localhost:8000/settings/user \
  -H "Content-Type: application/json" \
  -d '{
    "is_2fa_enabled": true,
    "totp_secret": "BASE32ENCODEDSECRET"
  }'

# 禁用2FA
curl -X PUT http://localhost:8000/settings/user \
  -H "Content-Type: application/json" \
  -d '{
    "is_2fa_enabled": false
  }'

# 同时更新密码和2FA
curl -X PUT http://localhost:8000/settings/user \
  -H "Content-Type: application/json" \
  -d '{
    "password": "new_password",
    "is_2fa_enabled": true,
    "totp_secret": "BASE32ENCODEDSECRET"
  }'
```

### 6. 用户登录

```bash
# 普通登录
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'

# 带2FA的登录
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password",
    "totp_code": "123456"
  }'
```

## 优势

1. **极简设计**：通知配置只保留必要字段（类型和配置）
2. **类型唯一**：每种通知类型只能有一个配置，避免混淆
3. **统一管理**：所有设置相关接口集中在 `/settings` 路由下
4. **配置复用**：多个任务可以共享同一个通知配置
5. **灵活性**：支持为空（不发送通知）或多个通知配置
6. **精简接口**：只保留必要的更新接口，避免配置被误删除
7. **完整的用户管理**：支持更新密码和2FA配置
