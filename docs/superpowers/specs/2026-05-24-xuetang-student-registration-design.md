# 学习通学生登记系统 - 设计文档

## 概述
用户从学习通（xuexitong.com）跳转到本应用时，Referer 头携带 `courseId`、`clazzId`、`cpi` 参数。系统据此识别学生，首次来访弹出登记表单，再次来访自动识别。

## 数据模型

**XuexitongStudent**（新增，独立于现有 User 模型）：
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| cpi | String unique | 学习通用户唯一标识 |
| course_id | String | 课程ID |
| clazz_id | String | 班级ID |
| name | String | 学生填写的姓名 |
| student_id | String | 学生填写的学号 |
| user_id | Integer FK | 关联的系统 User（自动创建，角色=student）|
| created_at | DateTime | 首次登记时间 |

## 流程

1. **Referer 解析**（Flask 端）
   - 用户从学习通跳转到 `/`，Flask 的 `index()` 检查 `request.referrer`
   - 用 `urllib.parse` 提取 courseId、clazzId、cpi
   - 存入 `session['xuetang_params']`

2. **检查接口** — `GET /api/xuetang/check`
   - 从 session 读取 xuetang 参数
   - 如果有 cpi，查 `XuexitongStudent` 表
   - 已注册 → 返回 `{ registered: true, user: {...}, token: "..." }`
   - 未注册 → 返回 `{ registered: false, hasParams: true }`

3. **登记接口** — `POST /api/xuetang/register`
   - Body: `{ name, student_id }`
   - 从 session 读取 cpi/courseId/clazzId
   - 创建 `XuexitongStudent` 记录
   - 自动创建系统 User（username=xt_<cpi>，display_name=name，role=student，随机密码）
   - 返回 JWT 直接登录

4. **前端流程**
   - App.vue/MainLayout.vue 挂载时调用 `/api/xuetang/check`
   - 已注册 → 存 JWT → 正常进入页面
   - 未注册但有参数 → 弹出 ElDialog 表单
   - 提交表单 → 调用 register → 存 JWT → 正常进入页面

## 文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| app/models.py | 修改 | 新增 XuexitongStudent 模型 |
| app/routes/xuetang.py | 新建 | check + register 两个接口 |
| app/__init__.py | 修改 | 注册蓝图 + 解析 Referer |
| frontend/src/stores/user.js | 修改 | 增加 xuetang 登录方法 |
| frontend/src/views/XuetangRegister.vue | 新建 | 登记弹窗组件 |

## 安全说明
- cpi 是学习通内部唯一标识，作为 lookup key 不会暴露给前端 JS
- Referer 只在服务端解析，前端不直接接触
- 生成的 User 密码随机，不支持密码登录（只走 JWT）
