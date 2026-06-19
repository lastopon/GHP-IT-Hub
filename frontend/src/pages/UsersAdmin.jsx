import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../lib/auth.jsx";
import {
  createUser,
  listDepartments,
  listUsers,
  updateUser,
} from "../lib/api.js";

const ROLES = [
  { value: "admin", label: "Super Admin / IT Manager" },
  { value: "staff", label: "IT Staff / Engineer" },
  { value: "user", label: "General User" },
];

const ROLE_BADGE = {
  admin: "bg-brand-100 text-brand-700",
  staff: "bg-amber-100 text-amber-700",
  user: "bg-slate-100 text-slate-600",
};

const EMPTY_FORM = {
  email: "",
  first_name: "",
  last_name: "",
  role: "user",
  department: "",
  phone: "",
  employee_id: "",
  password: "",
  is_active: true,
};

export default function UsersAdmin() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Modal state: null = closed, {} = create, {id,...} = edit.
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const [truncated, setTruncated] = useState(0);

  const isAdmin = user.role === "admin";

  async function load() {
    setLoading(true);
    setError("");
    try {
      // Backend caps page_size at 100; request the max so the table isn't
      // silently truncated at the default 20.
      const [u, d] = await Promise.all([
        listUsers({ page_size: 100 }),
        listDepartments(),
      ]);
      const rows = u.results ?? u;
      setUsers(rows);
      setTruncated(u.count ? Math.max(0, u.count - rows.length) : 0);
      setDepartments(d.results ?? d);
    } catch {
      setError("โหลดรายชื่อผู้ใช้ไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  }

  // Keep hook order stable: always register the effect, but skip the fetch
  // for non-admins (who are redirected below).
  useEffect(() => {
    if (isAdmin) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  // Only admins can manage users (backend enforces it too — this avoids a 403).
  if (!isAdmin) return <Navigate to="/" replace />;

  function openCreate() {
    setEditing({});
    setForm(EMPTY_FORM);
    setFormError("");
  }

  function openEdit(u) {
    setEditing(u);
    setForm({
      email: u.email,
      first_name: u.first_name || "",
      last_name: u.last_name || "",
      role: u.role,
      department: u.department || "",
      phone: u.phone || "",
      employee_id: u.employee_id || "",
      password: "",
      is_active: u.is_active,
    });
    setFormError("");
  }

  function closeModal() {
    setEditing(null);
  }

  async function onSubmit(e) {
    e.preventDefault();
    setFormError("");
    setSaving(true);
    try {
      const payload = { ...form, department: form.department || null };
      if (editing.id) {
        // Email + password aren't editable on the update endpoint.
        delete payload.email;
        delete payload.password;
        await updateUser(editing.id, payload);
      } else {
        await createUser(payload);
      }
      closeModal();
      await load();
    } catch (err) {
      const data = err.response?.data;
      setFormError(
        data
          ? Object.entries(data)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
              .join(" · ")
          : "บันทึกไม่สำเร็จ",
      );
    } finally {
      setSaving(false);
    }
  }

  function setField(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-sm text-slate-400 hover:text-brand-600">
              ← กลับ
            </Link>
            <h1 className="text-lg font-bold text-slate-800">จัดการผู้ใช้งาน</h1>
          </div>
          <button
            onClick={openCreate}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
          >
            + เพิ่มผู้ใช้
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        {error && (
          <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
            {error}
          </div>
        )}

        {loading ? (
          <p className="text-slate-400">กำลังโหลด…</p>
        ) : (
          <div className="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-slate-100">
            <table className="min-w-full divide-y divide-slate-100 text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-5 py-3 font-medium">อีเมล</th>
                  <th className="px-5 py-3 font-medium">ชื่อ</th>
                  <th className="px-5 py-3 font-medium">บทบาท</th>
                  <th className="px-5 py-3 font-medium">แผนก</th>
                  <th className="px-5 py-3 font-medium">สถานะ</th>
                  <th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50">
                    <td className="px-5 py-3 font-medium text-slate-700">{u.email}</td>
                    <td className="px-5 py-3 text-slate-600">
                      {[u.first_name, u.last_name].filter(Boolean).join(" ") || "—"}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${ROLE_BADGE[u.role] || "bg-slate-100 text-slate-600"}`}
                      >
                        {u.role_display || u.role}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-slate-600">{u.department_name || "—"}</td>
                    <td className="px-5 py-3">
                      {u.is_active ? (
                        <span className="text-green-600">● ใช้งาน</span>
                      ) : (
                        <span className="text-slate-400">● ปิดใช้งาน</span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-right">
                      <button
                        onClick={() => openEdit(u)}
                        className="text-sm text-brand-600 hover:underline"
                      >
                        แก้ไข
                      </button>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-5 py-8 text-center text-slate-400">
                      ยังไม่มีผู้ใช้
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {truncated > 0 && (
          <p className="mt-3 text-center text-xs text-slate-400">
            แสดง {users.length} รายชื่อแรก · มีอีก {truncated} รายชื่อที่ยังไม่แสดง
          </p>
        )}
      </main>

      {editing && (
        <div className="fixed inset-0 z-10 flex items-center justify-center bg-slate-900/40 px-4">
          <form
            onSubmit={onSubmit}
            className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"
          >
            <h2 className="mb-4 text-lg font-semibold text-slate-800">
              {editing.id ? "แก้ไขผู้ใช้" : "เพิ่มผู้ใช้ใหม่"}
            </h2>

            {formError && (
              <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
                {formError}
              </div>
            )}

            <div className="space-y-3">
              <Field label="อีเมล">
                <input
                  type="email"
                  required
                  disabled={!!editing.id}
                  value={form.email}
                  onChange={(e) => setField("email", e.target.value)}
                  className="input disabled:bg-slate-100 disabled:text-slate-400"
                />
              </Field>

              {!editing.id && (
                <Field label="รหัสผ่าน">
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={form.password}
                    onChange={(e) => setField("password", e.target.value)}
                    className="input"
                    placeholder="อย่างน้อย 8 ตัวอักษร"
                  />
                </Field>
              )}

              <div className="flex gap-3">
                <Field label="ชื่อ" className="flex-1">
                  <input
                    value={form.first_name}
                    onChange={(e) => setField("first_name", e.target.value)}
                    className="input"
                  />
                </Field>
                <Field label="นามสกุล" className="flex-1">
                  <input
                    value={form.last_name}
                    onChange={(e) => setField("last_name", e.target.value)}
                    className="input"
                  />
                </Field>
              </div>

              <Field label="บทบาท">
                <select
                  value={form.role}
                  onChange={(e) => setField("role", e.target.value)}
                  className="input"
                >
                  {ROLES.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="แผนก">
                <select
                  value={form.department}
                  onChange={(e) => setField("department", e.target.value)}
                  className="input"
                >
                  <option value="">— ไม่ระบุ —</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </Field>

              {editing.id && (
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(e) => setField("is_active", e.target.checked)}
                  />
                  เปิดใช้งานบัญชี
                </label>
              )}
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <button
                type="button"
                onClick={closeModal}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-100"
              >
                ยกเลิก
              </button>
              <button
                type="submit"
                disabled={saving}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
              >
                {saving ? "กำลังบันทึก…" : "บันทึก"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function Field({ label, className = "", children }) {
  return (
    <label className={`block ${className}`}>
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      {children}
    </label>
  );
}
