# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is an **AI teaching assistant** (AI 助教平台) — a teacher-facing platform for programming coursework. Teachers create classes, publish assignments, review submissions and track who has not submitted; students write and execute Python code with AI guidance; an LLM grades submissions automatically; admins handle user management.

This is **not an online judge**: there are no test cases and no deterministic verdicts. Grading is performed by an LLM in `app/utils/auto_grader.py`, which evaluates requirement coverage, correctness, code quality and generated figures.

### Tech Stack
- **Backend**: Flask + SQLAlchemy + SQLite (dev) + JWT auth + python-dotenv
- **Frontend**: Vue 3 + Vite 5 + Element Plus + Pinia + Vue Router + Axios
- **AI**: DeepSeek API (`deepseek-v4-flash`, OpenAI-compatible) for chat + code generation
- **Code Execution**: subprocess-based sandbox with matplotlib/GIF animation support

### Dual Rendering System
The app has **two parallel rendering paths** that share the same backend models:
1. **Server-rendered (Jinja2 templates)**: Older templates in `app/templates/`, using `session`-based auth via `app/utils/decorators.py`. Routes in `app/routes/auth.py`, `app/routes/student.py`, `app/routes/teacher.py`.
2. **Vue SPA (frontend/dist)**: Modern Vue app in `frontend/src/`, using JWT auth via `app/routes/api_auth.py`. The Flask app serves the built SPA at `/` and handles API routes under `/api/` via `app/routes/api.py`.

The `app/__init__.py:create_app()` function bootstraps both — API blueprints are registered alongside the SPA static file serving via catch-all `/<path:path>` route.

### Data Model (app/models.py)
- **User** — id, username, display_name, password (hashed), role (student/teacher/admin)
- **Class** — id, name, description, created_by, created_at (table name: `class_table`)
- **StudentClass** — many-to-many join between User (student) and Class
- **Assignment** — title, description, deadline, created_by (teacher), class_id, total_score
- **Submission** — assignment_id, student_id, code, stdout, stderr, images (JSON list), score, feedback
- **ChatSession/ChatMessage** — user chat sessions with AI assistant, stores message history with code execution results
- **XuexitongStudent** — binds 学习通 CPI params to a local user account for SSO-like auto-login

### 学习通 (Xuexitong) Integration
A non-interactive SSO flow for students coming from 学银在线/学习通 (`xuexitong.com`):
1. **Referer parsing** (`app/__init__.py:_parse_xuetang_referer()`) — extracts `cpi`, `courseId`, `clazzId` from the Referer header on `/xuetang-entry` and stores them in the session
2. **Endpoint `/xuetang-entry`** — redirects to the SPA `/xuetang?cpi=...` with query params for cross-origin support
3. **API `GET /api/xuetang/check`** — looks up `XuexitongStudent` by CPI, returns existing user's JWT if found, or signals "not registered"
4. **API `POST /api/xuetang/register`** — creates both a `User` (with auto-generated username `xt_{cpi[:20]}`) and a `XuexitongStudent` binding, returns JWT
5. **Frontend `XuetangEntry.vue`** — automates the check → register → redirect flow with a loading spinner and form

### Code Execution Pipeline
1. User submits Python code via API
2. `app/utils/security.py:is_safe_code()` checks for dangerous imports (os, subprocess, socket, etc.) and keywords (exec, eval, compile)
3. `app/utils/code_executor.py:execute_python_code()` runs code in a temp sandbox directory with matplotlib Chinese font config, automatic PNG saving (patched `plt.show`), and FuncAnimation → GIF conversion (via `atexit`)
4. Output files (PNG, GIF) are moved to `static/outputs/` with timestamped filenames

### LLM Integration (app/utils/llm.py)
- OpenAI-compatible API calls to DeepSeek (`deepseek-v4-flash` model)
- Falls back to `curl` subprocess if `requests` fails
- Called by the chat endpoint (`POST /api/chat/sessions/:id/messages`), which builds a conversation context with system prompt + history (last 20 rounds, capped at 40 messages)

### Auth System
- **JWT auth**: Used by the Vue SPA. `login_required`, `teacher_required`, `admin_required` decorators in `app/utils/api_decorators.py` decode JWT and set `g.current_user`
- **Session auth**: Used by Jinja templates. `require_role()` decorator in `app/utils/decorators.py` checks `flask.session`
- Admin > Teacher > Student hierarchy (admin inherits teacher permissions)

### Frontend Route Architecture (frontend/src/router/index.js)
- **Auth guard**: `router.beforeEach` checks `window.__VUE_APP_READY__` flag (set in `main.js` after app mount), ensures user is initialized via `ensureUserInitialized()` which restores token from `localStorage` and calls `GET /api/auth/me`
- **Role-based routing**: `requiresTeacher` and `requiresAdmin` meta flags redirect unauthorized users to `/dashboard`
- **Routes**: `/login`, `/register`, `/xuetang` (no auth) → `/dashboard`, `/chat`, `/profile`, `/teacher/*`, `/student/*`, `/admin/*` (auth required)

## Key Commands

```bash
# Backend
pip install -r requirements.txt              # Install Python deps
python run.py                                # Start Flask dev server (default :5000)

# Frontend
cd frontend && npm install                   # Install JS deps
cd frontend && npm run dev                   # Start Vite dev server (default :3000, proxies /api to :5000)
cd frontend && npm run build                 # Build SPA to frontend/dist/

# Database & Users
python init_db_with_users.py                 # Create tables + 3 demo accounts (teacher/student/admin)
python manage_users.py                       # List all users
python manage_users.py reset <user> <pass>   # Reset password
python manage_users.py add <user> <name> <pass> [role]  # Add user
```

## Configuration (.env)

All environment variables are documented in `.env.example`. Copy to `.env` to customize.

> **重要：cpolar 隧道地址动态变化** — 每次启动项目时，用户会提供新的前端和后端 cpolar 公网地址（如 `http://xxx.r11.cpolar.top`）。必须立即更新 `.env` 中的 `FRONTEND_URL`（学习通重定向用）和 `VITE_API_TARGET`（Vite 代理目标），同时更新 `vite.config.js` 的 `allowedHosts`。旧地址失效后要清理掉。

```ini
# Flask backend
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Vite dev server (frontend development only)
VITE_DEV_PORT=3000
VITE_API_TARGET=http://localhost:5000

# LLM (required for AI chat features)
OPENAI_API_KEY=your_key
OPENAI_API_BASE_URL=https://api.deepseek.com/v1/chat/completions
DEFAULT_MODEL=deepseek-v4-flash
```

## Project Structure

```
app/                          # Flask backend
├── __init__.py               # create_app() — factory, blueprint registration, demo user seeding, 学习通 referer parsing
├── config.py                 # Config classes (dev/prod), env vars
├── extensions.py             # SQLAlchemy db instance
├── models.py                 # All DB models (User, Class, Assignment, Submission, ChatSession, ChatMessage, XuexitongStudent)
├── routes/
│   ├── api.py                # Main REST API (classes, assignments, submissions, chat, students, admin, teacher-endpoints)
│   ├── api_auth.py           # JWT auth endpoints (login, register, me, logout)
│   ├── auth.py               # Session-based auth (login, register, logout, profile)
│   ├── student.py            # Server-rendered student dashboard, assignment detail, code runner
│   ├── teacher.py            # Server-rendered teacher dashboard, class/assignment/submission management
│   └── xuetang.py            # 学习通 SSO check/register endpoints
├── utils/
│   ├── api_decorators.py     # JWT auth decorators (login_required, teacher_required, admin_required)
│   ├── code_executor.py      # Sandboxed Python code execution with matplotlib/GIF support
│   ├── decorators.py         # Session auth decorator (require_role)
│   ├── llm.py                # LLM API caller (OpenAI-compatible, with curl fallback)
│   ├── auto_grader.py        # LLM auto grading (precheck → task type → weighted tier score)
│   ├── auto_assign.py        # Assigns new students to the default teacher's default class
│   └── security.py           # Code security scanner (block dangerous imports/keywords)
├── templates/                 # Jinja2 templates (legacy rendering path)
frontend/                     # Vue 3 SPA
├── src/
│   ├── main.js               # Vue app bootstrap (Element Plus + zhCn locale, Pinia, Router, Element Plus Icons)
│   ├── App.vue               # Root component
│   ├── router/index.js       # Route definitions with auth guards and initialization flow
│   ├── stores/user.js        # Pinia user store (login state, token management, role computed helpers)
│   ├── services/api.js       # Axios instance with JWT interceptor (auto-redirect on 401)
│   ├── layouts/              # Layout components (MainLayout.vue)
│   ├── views/                # Page components
│   │   ├── Login.vue / Register.vue / XuetangEntry.vue  # Auth pages
│   │   ├── Dashboard.vue     # Role-based dashboard with stats and quick actions
│   │   ├── Chat.vue          # AI chat with markdown/code rendering (uses marked + highlight.js)
│   │   ├── Profile.vue       # User profile
│   │   ├── teacher/          # Classes, Assignments, Students, Submissions, ViewSubmission, ChatHistory
│   │   ├── student/          # Assignments list, AssignmentDetail (with code editor/submit)
│   │   └── admin/            # Users management
│   └── style/                # Global CSS (code-block.css for syntax highlighting)
├── dist/                     # Built SPA (served by Flask in production via `/<path:path>` catch-all)
├── package.json
└── vite.config.js            # Dev server proxy to Flask on :5000, reads root .env via loadEnv()
static/
├── outputs/                  # Code execution output files (PNG, GIF)
└── css/
```

## Important Notes

- **No tests directory** currently exists — no test framework is configured
- `app.old.py` is excluded via `.gitignore` — a local-only legacy single-file version, not in the remote repo
- Code execution sandbox (`sandbox_temp/`) is created at runtime and cleaned up after each execution
- Two demo-account sets exist: `create_app()` seeds 4 users (admin, teacher, student1, student2) only when `User.query.count() == 0`; `init_db_with_users.py` seeds 3 users (teacher, student, admin). Whichever runs first determines the final account set
- The `is_safe_code()` check in `security.py` is regex-based and blocks dangerous operations, but is not a full sandbox — the subprocess isolation is the real security boundary
- Frontend key dependencies: `marked` (Markdown rendering in AI chat replies), `highlight.js` (Python code syntax highlighting in chat), `@element-plus/icons-vue` (all icons globally registered in main.js)
- The vite config uses `loadEnv(mode, projectRoot, '')` to read the root `.env` file — prefix filtering is disabled so both `VITE_*` and `FLASK_*` vars are available
- 学习通 CPI binding uses `XuexitongStudent.cpi` as the unique key — the CPI is a per-course/per-user identifier from 学银在线
