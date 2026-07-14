# 账号配置优化说明

## 优化目的
将 UI 测试和 API 测试的账号密码分开管理，避免混淆。

## 配置说明

### UI 测试账号（明文密码）
**文件**: `tests/ui/fixtures/accounts.ts`

```typescript
accounts.ui = {
  username: 'zsy',
  password: 'admin123'  // 明文密码，前端会自动加密
}
```

**特点**:
- 使用明文密码 `admin123`
- 前端登录时会自动加密为 `17uV/kDYwCJ3/zyUt59BHw==`
- 用于所有 UI 自动化测试场景

### API 测试账号（加密密码）
**文件**: `tests/api/env/test.yaml`

```yaml
auth:
  username: "zsy"
  password: "17uV/kDYwCJ3/zyUt59BHw=="  # 加密密码
  clientId: "e5cd7e4891bf95d1d19206ce24a7b32e"
```

**特点**:
- 使用加密密码 `17uV/kDYwCJ3/zyUt59BHw==`
- 直接调用 API 接口，不需要前端加密
- 用于所有 API 自动化测试场景

## 使用方式

### UI 测试代码
```typescript
import accounts from '../fixtures/accounts';

// 使用 UI 账号
await loginPage.login(accounts.ui.username, accounts.ui.password);
```

### API 测试代码
```python
from utils.config_loader import load_env_config

env_config = load_env_config()
username = env_config["auth"]["username"]
password = env_config["auth"]["password"]  # 已加密
```

## 加密说明

### 前端加密流程
1. 用户在登录页面输入明文密码 `admin123`
2. 前端 JavaScript 自动加密为 `17uV/kDYwCJ3/zyUt59BHw==`
3. 提交到后端接口 `/prod-api/auth/login`

### API 测试
- 直接提交加密密码 `17uV/kDYwCJ3/zyUt59BHw==`
- 不需要额外加密步骤

## 账号状态

### 当前状态
- **账号**: zsy
- **状态**: ⚠️ 临时锁定（密码错误 5 次）
- **锁定时间**: 10 分钟
- **解锁时间**: 等待锁定时间过后自动解锁

### 解锁后验证
```bash
# UI 测试
cd tests/ui
npx playwright test specs/smoke --reporter=html --output=reports

# API 测试
cd tests/api
python -m pytest testsuites/auth/test_login.py -v
```

## 注意事项

1. **不要混用账号配置**
   - UI 测试必须使用 `accounts.ui`（明文密码）
   - API 测试必须使用 `test.yaml` 配置（加密密码）

2. **密码加密**
   - UI 测试：前端自动加密，测试代码使用明文
   - API 测试：直接使用加密后的密码

3. **账号安全**
   - 避免多次登录失败导致账号锁定
   - 生产环境应使用环境变量管理敏感信息
