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
| **โมดูล 2 — Helpdesk & Ticketing** (Ticket + SLA, Category, Comment, Attachment, Knowledge Base) | ✅ |
| **โมดูล 3 — IT Asset Management** (Asset lifecycle, Category, Assignment history, Maintenance, warranty, QR lookup) | ✅ |
| **โมดูล 4 — Inventory Management** (Spare parts + min-stock alert, Category, Stock movement ledger เบิก/รับ/ปรับ signed) | ✅ |
| **โมดูล 5 — Daily Report & Checklist** (Template + Item, Run + Result pass/fail, daily summary รวม checklist + ticket) | ✅ |
| **โมดูล 6 — Project Management / Kanban** (Project + timeline, Board column, Card + assignee/priority, ย้าย card + จัดลำดับ) | ✅ (backend) |
| LDAP / Active Directory (เปิดด้วย `LDAP_ENABLED=True`) | 🟡 เตรียมไว้ |
| Frontend (React + Vite + Tailwind) — Login + Dashboard + User Management + Helpdesk + Asset + Inventory + Daily Report | ✅ |
| โมดูล 7–8 | ⬜ ยังไม่เริ่ม (มี placeholder บน Dashboard) |

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

## API หลัก (โมดูล 2 — Helpdesk)

| Method | Path | สิทธิ์ |
| :--- | :--- | :--- |
| GET/POST | `/api/v1/helpdesk/tickets/` | ผู้ใช้สร้าง/ดูเคสของตนเอง · IT Staff เห็นทุกเคส |
| PATCH | `/api/v1/helpdesk/tickets/{id}/` | IT Staff แก้ได้ทุกฟิลด์ · ผู้ใช้แก้ได้เฉพาะคะแนนความพึงพอใจ |
| POST | `/api/v1/helpdesk/tickets/{id}/assign/` | IT Staff — จ่ายงานให้ผู้รับผิดชอบ |
| POST | `/api/v1/helpdesk/tickets/{id}/resolve/` | IT Staff — ปิดเคสเป็น resolved |
| GET/POST | `/api/v1/helpdesk/comments/` | ผู้ใช้คอมเมนต์เคสตนเอง · internal note เฉพาะ IT Staff |
| GET | `/api/v1/helpdesk/categories/` | ผู้ใช้ที่ล็อกอิน (อ่าน), Admin (เขียน) |
| GET | `/api/v1/helpdesk/kb/` | ผู้ใช้เห็นบทความที่เผยแพร่ · IT Staff จัดการได้ |

Ticket จะได้เลขอ้างอิงอัตโนมัติ (`TKT-000001`) และคำนวณ `sla_due_at` จาก `default_sla_hours` ของหมวดหมู่

## API หลัก (โมดูล 3 — IT Asset Management)

| Method | Path | สิทธิ์ |
| :--- | :--- | :--- |
| GET | `/api/v1/assets/items/` | ผู้ใช้ที่ล็อกอิน (อ่าน) |
| POST/PATCH | `/api/v1/assets/items/` | IT Staff — จัดการสินทรัพย์ |
| GET | `/api/v1/assets/items/lookup/?tag=<asset_tag>` | สแกน QR/บาร์โค้ด — คืนสเปค + ผู้ครอบครอง + ประวัติ |
| POST | `/api/v1/assets/items/{id}/assign/` | IT Staff — มอบหมายให้ผู้ครอบครอง (เปิด assignment + status → in_use) |
| POST | `/api/v1/assets/items/{id}/return/` | IT Staff — รับคืน (ปิด assignment + status → in_store) |
| GET | `/api/v1/assets/assignments/` | ประวัติการมอบหมาย (read-only) |
| GET/POST | `/api/v1/assets/maintenance/` | ประวัติการซ่อม — IT Staff จัดการ |
| GET | `/api/v1/assets/categories/` | ผู้ใช้ที่ล็อกอิน (อ่าน), Admin (เขียน) |

วงจรชีวิต: `procured → in_use → in_store → in_repair → scrapped` · `assigned_to` สะท้อน assignment ที่ยังเปิดอยู่ · มี seed หมวดหมู่ด้วย `manage.py seed_assets`

## API หลัก (โมดูล 4 — Inventory Management)

| Method | Path | สิทธิ์ |
| :--- | :--- | :--- |
| GET | `/api/v1/inventory/items/` | ผู้ใช้ที่ล็อกอิน (อ่าน) |
| POST/PATCH | `/api/v1/inventory/items/` | IT Staff — จัดการรายการอะไหล่ (`quantity` แก้ตรงไม่ได้) |
| POST | `/api/v1/inventory/items/{id}/move/` | IT Staff — เบิก/รับเข้า/ปรับ (`kind` = issue/receive/adjust) |
| GET | `/api/v1/inventory/items/low_stock/` | รายการที่ `quantity ≤ min_stock` |
| GET | `/api/v1/inventory/movements/` | บันทึกการเคลื่อนไหวสต็อก (read-only) |
| GET | `/api/v1/inventory/categories/` | ผู้ใช้ที่ล็อกอิน (อ่าน), Admin (เขียน) |

`quantity` เปลี่ยนผ่าน `move/` เท่านั้น (atomic + ล็อกแถว, กันสต็อกติดลบ) ทุกการเคลื่อนไหวบันทึกลง ledger พร้อม `quantity_after` · มี seed หมวดหมู่ด้วย `manage.py seed_inventory`

## API หลัก (โมดูล 5 — Daily Report & Checklist)

| Method | Path | สิทธิ์ |
| :--- | :--- | :--- |
| GET | `/api/v1/dailyreport/templates/` | ผู้ใช้ที่ล็อกอิน (อ่าน) · แม่แบบ + รายการที่ต้องเช็ก |
| GET/POST | `/api/v1/dailyreport/runs/` | อ่านทุกคน · IT Staff สร้างรอบเดินตรวจ |
| POST | `/api/v1/dailyreport/runs/{id}/submit/` | IT Staff — ส่งผลทั้งรอบ (pass/fail/reading) + ปิดเป็น completed |
| GET | `/api/v1/dailyreport/runs/daily_summary/?date=YYYY-MM-DD` | สรุปรายวัน: รวมผล checklist + ยอด ticket จาก Helpdesk |
| GET | `/api/v1/dailyreport/results/` | ผลแต่ละรายการ (read-only) |

`submit/` เป็น atomic + ตรวจว่า item อยู่ใน template ของรอบนั้นและไม่ซ้ำ (re-submit แทนที่ผลเดิม) · `daily_summary` ดึงยอด ticket วันเดียวกันจากโมดูล 2 มารวม · มี seed แม่แบบ "Server Room Daily Check" ด้วย `manage.py seed_dailyreport`

## API หลัก (โมดูล 6 — Project Management / Kanban)

| Method | Path | สิทธิ์ |
| :--- | :--- | :--- |
| GET | `/api/v1/projects/items/` | ผู้ใช้ที่ล็อกอิน (อ่าน) |
| POST/PATCH | `/api/v1/projects/items/` | IT Staff — จัดการโครงการ |
| GET | `/api/v1/projects/items/{id}/board/` | บอร์ด Kanban เต็ม (columns → cards เรียงลำดับ) |
| GET/POST | `/api/v1/projects/columns/` | IT Staff — จัดการคอลัมน์ |
| GET/POST | `/api/v1/projects/cards/` | IT Staff — สร้างการ์ด (ต่อท้ายคอลัมน์อัตโนมัติ) |
| POST | `/api/v1/projects/cards/{id}/move/` | IT Staff — ย้ายการ์ด (`column?`, `position`) + จัดลำดับใหม่ทั้งสองเลน |

`move/` เป็น atomic — ตรวจว่าคอลัมน์ปลายทางอยู่ในโครงการเดียวกัน, clamp position, แล้วเขียน order ใหม่ 0..n-1 พร้อมปิดช่องว่างในเลนต้นทาง · มี seed โครงการตัวอย่าง "Network Upgrade 2026" ด้วย `manage.py seed_projects`

## ทดสอบ

```bash
docker compose exec backend python manage.py test --settings=config.settings.test
```

ชุดทดสอบครอบคลุม: JWT login, การ audit เมื่อ login สำเร็จ/ล้มเหลว, RBAC (Admin vs General User), `/me`, ความ immutable ของ AuditLog, flow ของ Helpdesk (สร้าง ticket + ออกเลขอ้างอิง/SLA, RBAC การมองเห็นเคส, การ assign/resolve) Asset (RBAC, วงจรชีวิต assign/return + ประวัติ, QR lookup) Inventory (RBAC, เบิก/รับ/ปรับ + sync quantity, กันสต็อกติดลบ, low-stock) Daily Report (RBAC, submit run + validation, daily summary รวม checklist + ticket) และ Projects/Kanban (RBAC, ย้าย card ในเลน/ข้ามเลน + จัดลำดับ, กันข้ามโครงการ) — รวม 77 เทสต์

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

โมดูล 7 IPAM · 8 Monitoring integration
