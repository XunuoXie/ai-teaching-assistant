# AI Teaching Assistant

面向教师的教学作业管理平台。老师发布作业、学生在线编写并运行 Python 代码，AI 自动完成批改与反馈，教师随时掌握班级的作业完成情况与学习过程。

> 相比传统在线判题系统，本平台不依赖预设测试用例，而是通过大模型对代码质量、运行结果和图表产出做语义化评分，适合开放式编程作业与数据可视化作业。

## 核心功能

### 教师端

- **班级管理**：创建班级、维护学生名单、批量分班
- **作业发布**：设置标题、要求、截止时间与总分
- **AI 自动批改**：提交后自动评分并生成评语，识别画图类作业与普通编程作业
- **作业完成情况追踪**：Dashboard 实时显示作业数量、学生人数、已提交、**未提交**、已完成批改
- **学情监督**：回看任意学生与 AI 助手的完整对话记录，定位学生的卡点与提问习惯
- **人工复核**：查看提交代码、运行输出与生成图片，可覆盖 AI 给出的分数与评语

### 学生端

- 与 AI 助手多轮对话，获得 Python 编程指导
- 在线编写并运行代码，支持 matplotlib 图表与 GIF 动画生成
- 提交作业并查看 AI 评分反馈

### 管理端

- 用户管理、角色分配（学生 / 教师 / 管理员）与密码重置

### 学习通集成

学生从学习通（学银在线）跳转进入时，系统解析 Referer 中的 `cpi` / `courseId` / `clazzId`：

- 已登记学生：自动登录，无需账号密码
- 首次来访：弹出登记表单，自动创建账号并加入默认教师班级

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端框架 | Flask + SQLAlchemy |
| 数据库 | SQLite（开发） |
| 认证 | JWT（Vue SPA）+ Flask Session（Jinja 页面） |
| 前端 | Vue 3 + Vite + Element Plus + Pinia + Vue Router |
| AI | DeepSeek API（OpenAI 兼容协议） |
| 代码执行 | subprocess 沙箱 + 超时与危险调用拦截 |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 1. 安装后端依赖

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，至少填写 `OPENAI_API_KEY`。配置项说明：

| 变量 | 说明 |
| --- | --- |
| `SECRET_KEY` | Flask session 签名密钥，生产环境必须替换 |
| `OPENAI_API_KEY` | DeepSeek（或任意 OpenAI 兼容服务）的 API Key |
| `OPENAI_API_BASE_URL` | 接口地址，默认 `https://api.deepseek.com/v1/chat/completions` |
| `DEFAULT_MODEL` | 使用的模型名 |
| `DEFAULT_TEACHER_USERNAME` | 新学生自动分班的目标教师用户名 |
| `XUETANG_TEACHER_CPIS` | 学习通教师 CPI 白名单，逗号分隔 |
| `FRONTEND_URL` | 学习通 SSO 回跳的前端地址 |
| `API_TIMEOUT` / `CODE_EXECUTION_TIMEOUT` | LLM 调用与代码执行的超时秒数 |

### 3. 初始化数据库

```bash
python init_db_with_users.py
```

该脚本会创建数据库表，并生成三个演示账号（见下方「默认账号」）。

### 4. 构建前端

```bash
cd frontend
npm install
npm run build
```

Flask 会直接托管 `frontend/dist` 构建产物。

### 5. 启动服务

```bash
python run.py
```

访问 `http://localhost:5000`。监听地址与端口由 `.env` 中的 `FLASK_HOST` / `FLASK_PORT` 控制。

### 前端开发模式（可选）

前后端分离调试时，修改 `vite.config.js` 已配置代理，前端开发服务器默认运行在 `3000` 端口：

```bash
cd frontend && npm run dev
```

访问 `http://localhost:3000`，接口请求将代理至后端。

## 项目结构

```
.
├── app/
│   ├── __init__.py              # 应用工厂、蓝图注册、学习通 Referer 解析
│   ├── config.py                # 从环境变量加载配置
│   ├── models.py                # User / Class / Assignment / Submission / Chat* / XuexitongStudent
│   ├── routes/
│   │   ├── api.py               # 主要业务 API（班级/作业/提交/评分/统计）
│   │   ├── api_auth.py          # JWT 认证
│   │   ├── auth.py              # Jinja 页面会话认证
│   │   ├── student.py           # 学生端页面路由
│   │   ├── teacher.py           # 教师端页面路由
│   │   └── xuetang.py           # 学习通登记与自动登录
│   ├── utils/
│   │   ├── llm.py               # LLM 调用封装
│   │   ├── code_executor.py     # 沙箱执行、matplotlib 出图与 GIF 导出
│   │   ├── auto_grader.py       # AI 自动评分（前置检查 → 题型识别 → 定档打分）
│   │   ├── auto_assign.py       # 新学生自动分班
│   │   ├── security.py          # 危险导入 / 调用检测
│   │   ├── api_decorators.py    # JWT 权限装饰器
│   │   └── decorators.py        # Session 权限装饰器
│   └── templates/               # Jinja 服务端渲染页面
├── frontend/
│   └── src/
│       ├── views/               # Vue 页面（含 teacher/ student/ admin/ 子目录）
│       ├── router/              # 路由与角色守卫
│       ├── services/            # Axios 封装
│       └── stores/              # Pinia 状态
├── docs/                        # 设计文档
├── static/outputs/              # 代码执行产出（运行时生成）
├── init_db.py                   # 仅建表
├── init_db_with_users.py        # 建表 + 演示账号
├── manage_users.py              # 命令行用户管理
└── run.py                       # 启动入口
```

## 主要 API

所有业务接口以 `/api` 为前缀，认证接口以 `/api/auth` 为前缀。

### 认证

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/auth/login` | POST | 登录，返回 JWT |
| `/api/auth/register` | POST | 注册 |
| `/api/auth/me` | GET | 获取当前用户 |
| `/api/auth/logout` | POST | 登出 |

### 班级与用户

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/classes` | GET / POST | 班级列表 / 创建班级 |
| `/api/classes/<id>/students` | GET / POST | 班级成员 / 添加成员 |
| `/api/students` | GET / POST | 学生列表 / 新建学生 |
| `/api/students/<id>/add-class` | POST | 学生加入班级 |
| `/api/admin/users` | GET / POST | 用户管理 |
| `/api/admin/users/<id>/reset-password` | POST | 重置密码 |

### 作业与评分

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/assignments` | GET / POST | 作业列表 / 发布作业 |
| `/api/assignments/<id>/submit` | POST | 学生提交作业 |
| `/api/submissions` | GET | 提交列表 |
| `/api/submissions/<id>` | GET / PUT | 提交详情 / 修改 |
| `/api/submissions/<id>/grade` | POST | 打分（可覆盖 AI 评分） |
| `/api/dashboard/stats` | GET | 教师统计看板 |

### AI 与代码执行

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/chat/sessions` | GET / POST | 会话列表 / 新建会话 |
| `/api/chat/sessions/<id>/messages` | GET / POST | 拉取历史 / 发送消息 |
| `/api/execute-code` | POST | 在沙箱中执行 Python 代码 |
| `/api/teacher/students/<id>/chat-sessions` | GET | 查看某学生的全部会话 |
| `/api/xuetang/check` | GET | 学习通学生是否已登记 |
| `/api/xuetang/register` | POST | 学习通学生登记 |

## AI 评分流程

`app/utils/auto_grader.py` 的处理链路：

1. **前置检查**：代码为空、运行报错或无输出 → 直接 0 分
2. **题型识别**：根据作业描述判断是否画图类作业，选用不同评分提示词
3. **模型打分**：将作业要求、学生代码、stdout/stderr 与图片信息交给模型，要求返回结构化 JSON
4. **加权计算**：需求覆盖度、正确性、代码质量、效率等维度加权求和
5. **档位映射**：把百分制结果对齐到档位区间，避免分数零碎

教师可在前端复核并修改最终分数。

## 安全说明

- **切勿提交 `.env`**：仓库已通过 `.gitignore` 排除，请只提交 `.env.example`
- **及时轮换密钥**：若 API Key 曾出现在任何会被提交或分享的文件中，应立即在服务商处重新生成
- **代码执行沙箱**：基于 subprocess 与危险调用检测，属于教学用途的轻量隔离，不建议直接暴露到公网
- **演示账号仅供本地开发**：首次部署后请立即修改或删除默认账号
- **聊天记录含学生隐私**：数据库文件已被忽略，生产环境请做好备份与访问控制

## 默认账号

由 `init_db_with_users.py` 创建，**仅用于本地开发**：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 教师 | teacher | teacher123 |
| 学生 | student | student123 |
| 管理员 | admin | admin123 |

修改密码：

```bash
python manage_users.py                      # 查看用户列表
python manage_users.py reset teacher 新密码  # 重置密码
python manage_users.py add 用户名 显示名 密码 role
```

## License

本项目基于 [MIT License](LICENSE) 开源。
