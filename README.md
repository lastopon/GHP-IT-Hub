# GHP IT Hub

แพลตฟอร์มบริหารงาน IT แบบครบวงจร (All-in-One IT Management) สำหรับใช้งานภายในองค์กรบนสภาพแวดล้อม **On-Premise** ออกแบบแบบ **API-First** รองรับทั้ง Web และ Mobile ผ่านแกนกลางเดียวกัน

> สถาปัตยกรรมและขอบเขตโมดูลทั้งหมดอ้างอิงจาก [cloude.md](cloude.md)

## สถานะปัจจุบัน — Skeleton + Phase 1

| ส่วน | สถานะ |
| :--- | :--- |
| โครงสร้างโปรเจกต์ + Docker Compose (Django + PostgreSQL + Redis + Celery + Celery beat) | ✅ |
| Django config (settings แยก base/dev/prod/test, urls, wsgi, asgi, celery) | ✅ |
| Core app (BaseModel UUID + soft-delete, ActiveManager, pagination, `wait_for_db`) | ✅ |
| **โมดูล 1 — User Management & Auth** (CustomUser, RBAC, Department, AuditLog, JWT) | ✅ |
| LDAP / Active Directory (เปิดด้วย `LDAP_ENABLED=True`) | 🟡 เตรียมไว้ |
| Frontend (React + Vite + Tailwind) — Login + Dashboard | ✅ |
| โมดูล 2–8 | ⬜ ยังไม่เริ่ม (มี placeholder บน Dashboard) |

## Stack

- **Backend:** Python 3.12 · Django 5 · Django REST Framework · SimpleJWT · Celery
- **Database / Cache:** PostgreSQL 16 · Redis 7
- **Frontend:** React 18 · Vite 5 · Tailwind CSS 3 · React Router · Axios
- **Infra:** Docker Compose (dev) — ออกแบบให้ขยายไปสู่ K3s/Docker Swarm + MinIO ได้ตาม cloude.md §3

## โครงสร้างโฟลเดอร์

```
GHP IT Hub/
├── cloude.md                 # เอกสารสถาปัตยกรรม (source of truth)
├── docker-compose.yml        # dev stack: db + redis + backend + celery + beat
├── .env.example              # คัดลอกเป็น .env ก่อนรัน
├── backend/
│   ├── Dockerfile            # python:3.12-slim
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/               # settings (base|dev|prod|test|ldap), urls, celery, wsgi, asgi
│   └── apps/
│       ├── core/             # BaseModel, ActiveManager, pagination, wait_for_db
│       └── authentication/   # User, Department, AuditLog, RBAC, JWT, seed_users
└── frontend/                 # React + Vite + Tailwind
    └── src/
        ├── lib/              # api.js (axios+JWT refresh), auth.jsx (context)
        └── pages/            # Login.jsx, Dashboard.jsx
```

## เริ่มต้นใช้งาน

### 1) เตรียม environment

```bash
cp .env.example .env
# แก้ SECRET_KEY เป็นค่าสุ่มยาว ๆ ก่อนใช้งานจริง
```

### 2) รัน backend stack ด้วย Docker

```bash
docker compose up --build
```

จะได้:
- API: http://localhost:8000
- Swagger: http://localhost:8000/api/docs/ · ReDoc: http://localhost:8000/api/redoc/
- Health check: http://localhost:8000/health/

สร้างผู้ใช้ตัวอย่าง (1 คนต่อ role) และแผนกเริ่มต้น:

```bash
docker compose exec backend python manage.py seed_users
```

| Role | อีเมล | รหัสผ่าน |
| :--- | :--- | :--- |
| Super Admin | admin@ghp.local | Admin@1234 |
| IT Staff | staff@ghp.local | Staff@1234 |
| General User | user@ghp.local | User@1234 |

### 3) รัน frontend (dev)

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxy /api -> :8000)
```

## API หลัก (โมดูล 1)

| Method | Path | สิทธิ์ |
| :--- | :--- | :--- |
| POST | `/api/v1/auth/login/` | public — คืน `{access, refresh, user}` |
| POST | `/api/v1/auth/token/refresh/` | public |
| GET/PATCH | `/api/v1/auth/users/me/` | ผู้ใช้ที่ล็อกอิน |
| GET/POST | `/api/v1/auth/users/` | Admin เท่านั้น |
| GET | `/api/v1/auth/departments/` | ผู้ใช้ที่ล็อกอิน (อ่าน), Admin (เขียน) |

## ทดสอบ

```bash
docker compose exec backend python manage.py test --settings=config.settings.test
```

ชุดทดสอบครอบคลุม: JWT login, การ audit เมื่อ login สำเร็จ/ล้มเหลว, RBAC (Admin vs General User), `/me`, และความ immutable ของ AuditLog

## เปิดใช้ LDAP / Active Directory (ภายหลัง)

ตั้งค่าใน `.env`:

```env
LDAP_ENABLED=True
LDAP_SERVER_URI=ldap://dc.example.local
LDAP_BIND_DN=...
LDAP_USER_SEARCH_BASE=...
```

ระบบจะใช้ `django-auth-ldap` ตรวจสอบกับ AD ก่อน แล้ว fallback มาที่บัญชี local — รายละเอียดดู [backend/config/settings/ldap.py](backend/config/settings/ldap.py)

## โรดแมปถัดไป (จาก cloude.md)

โมดูล 2 Helpdesk · 3 Asset · 4 Inventory · 5 Daily Report · 6 Project (Kanban) · 7 IPAM · 8 Monitoring integration
