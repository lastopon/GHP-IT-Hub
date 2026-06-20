import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth.jsx";

// The 8 modules from cloude.md §2. `roles` controls who sees each card.
// `ready` cards link to their implemented page (`to`); the rest are
// placeholders so the roadmap is visible in the UI.
const MODULES = [
  { id: 1, name: "User Management", desc: "จัดการผู้ใช้ + สิทธิ์ RBAC", roles: ["admin"], ready: true, to: "/users" },
  { id: 2, name: "Helpdesk & Ticketing", desc: "แจ้งซ่อม / SLA / Knowledge Base", roles: ["admin", "staff", "user"], ready: true, to: "/helpdesk" },
  { id: 3, name: "IT Asset Management", desc: "วงจรชีวิตสินทรัพย์ + QR Code", roles: ["admin", "staff", "user"], ready: true, to: "/assets" },
  { id: 4, name: "Inventory", desc: "คลังอะไหล่ + แจ้งเตือนสต็อกต่ำ", roles: ["admin", "staff", "user"], ready: true, to: "/inventory" },
  { id: 5, name: "Daily Report & Checklist", desc: "ตรวจเช็กประจำวัน + รายงานอัตโนมัติ", roles: ["admin", "staff"] },
  { id: 6, name: "Project Management", desc: "Kanban board สำหรับงานโครงการ", roles: ["admin", "staff"] },
  { id: 7, name: "IP & VLAN / IPAM", desc: "ทะเบียน IP/VLAN + เบิก IP ว่าง", roles: ["admin", "staff"] },
  { id: 8, name: "Monitoring Integration", desc: "เชื่อม Zabbix/PRTG + auto ticket", roles: ["admin", "staff"] },
];

const ROLE_LABEL = {
  admin: "Super Admin / IT Manager",
  staff: "IT Staff / Engineer",
  user: "General User",
};

export default function Dashboard() {
  const { user, logout } = useAuth();
  const visible = MODULES.filter((m) => m.roles.includes(user.role));

  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-lg font-bold text-brand-600">GHP IT Hub</h1>
            <p className="text-xs text-slate-400">All-in-One IT Management (On-Premise)</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-slate-700">
                {user.first_name} {user.last_name}
              </p>
              <p className="text-xs text-slate-400">{ROLE_LABEL[user.role] || user.role}</p>
            </div>
            <button
              onClick={logout}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
            >
              ออกจากระบบ
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">
          โมดูลที่ใช้งานได้ ({visible.length})
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {visible.map((m) => {
            const clickable = m.ready && m.to;
            const body = (
              <>
                <div className="mb-2 flex items-center justify-between">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-sm font-bold text-brand-600">
                    {m.id}
                  </span>
                  {m.ready ? (
                    <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                      พร้อมใช้
                    </span>
                  ) : (
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-400">
                      เร็วๆ นี้
                    </span>
                  )}
                </div>
                <h3 className="font-semibold text-slate-800">{m.name}</h3>
                <p className="mt-1 text-sm text-slate-500">{m.desc}</p>
              </>
            );
            const base =
              "rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-100 transition";
            return clickable ? (
              <Link
                key={m.id}
                to={m.to}
                className={`${base} block hover:shadow-md hover:ring-brand-200`}
              >
                {body}
              </Link>
            ) : (
              <div key={m.id} className={`${base} hover:shadow-md`}>
                {body}
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
