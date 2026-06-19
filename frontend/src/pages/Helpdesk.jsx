import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth.jsx";
import {
  addTicketComment,
  assignTicket,
  createTicket,
  getTicket,
  listAssignees,
  listTicketCategories,
  listTickets,
  rateTicket,
  resolveTicket,
} from "../lib/api.js";

const STATUS_BADGE = {
  new: "bg-blue-100 text-blue-700",
  assigned: "bg-indigo-100 text-indigo-700",
  in_progress: "bg-amber-100 text-amber-700",
  on_hold: "bg-slate-100 text-slate-500",
  resolved: "bg-green-100 text-green-700",
  closed: "bg-slate-200 text-slate-600",
  cancelled: "bg-red-100 text-red-600",
};

const PRIORITY_BADGE = {
  low: "bg-slate-100 text-slate-500",
  medium: "bg-sky-100 text-sky-700",
  high: "bg-orange-100 text-orange-700",
  urgent: "bg-red-100 text-red-700",
};

const PRIORITIES = ["low", "medium", "high", "urgent"];

// Backend caps page_size at 100; request the max so the list isn't silently
// truncated at the default 20. Narrow with the status/priority filters.
const PAGE_SIZE = 100;

export default function Helpdesk() {
  const { user } = useAuth();
  const isStaff = user.role === "admin" || user.role === "staff";

  const [tickets, setTickets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({ status: "", priority: "" });

  const [creating, setCreating] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [truncated, setTruncated] = useState(0); // total rows beyond what's shown

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = { page_size: PAGE_SIZE };
      if (filters.status) params.status = filters.status;
      if (filters.priority) params.priority = filters.priority;
      const data = await listTickets(params);
      const rows = data.results ?? data;
      setTickets(rows);
      // Surface (rather than silently drop) anything past the first page.
      setTruncated(data.count ? Math.max(0, data.count - rows.length) : 0);
    } catch {
      setError("โหลดรายการเคสไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    listTicketCategories()
      .then((d) => setCategories(d.results ?? d))
      .catch(() => {});
  }, []);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-sm text-slate-400 hover:text-brand-600">
              ← กลับ
            </Link>
            <h1 className="text-lg font-bold text-slate-800">Helpdesk & Ticketing</h1>
          </div>
          <button
            onClick={() => setCreating(true)}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
          >
            + แจ้งปัญหา
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-4 flex flex-wrap gap-3">
          <select
            value={filters.status}
            onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
            className="input max-w-[180px]"
          >
            <option value="">ทุกสถานะ</option>
            {Object.keys(STATUS_BADGE).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <select
            value={filters.priority}
            onChange={(e) => setFilters((f) => ({ ...f, priority: e.target.value }))}
            className="input max-w-[180px]"
          >
            <option value="">ทุกความสำคัญ</option>
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>

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
                  <th className="px-5 py-3 font-medium">เลขที่</th>
                  <th className="px-5 py-3 font-medium">หัวข้อ</th>
                  <th className="px-5 py-3 font-medium">หมวด</th>
                  <th className="px-5 py-3 font-medium">สถานะ</th>
                  <th className="px-5 py-3 font-medium">ความสำคัญ</th>
                  {isStaff && <th className="px-5 py-3 font-medium">ผู้แจ้ง</th>}
                  <th className="px-5 py-3 font-medium">SLA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {tickets.map((t) => (
                  <tr
                    key={t.id}
                    onClick={() => setSelectedId(t.id)}
                    className="cursor-pointer hover:bg-slate-50"
                  >
                    <td className="px-5 py-3 font-mono text-xs text-slate-500">
                      {t.reference}
                    </td>
                    <td className="px-5 py-3 font-medium text-slate-700">{t.title}</td>
                    <td className="px-5 py-3 text-slate-600">{t.category_name}</td>
                    <td className="px-5 py-3">
                      <Badge map={STATUS_BADGE} value={t.status} label={t.status_display} />
                    </td>
                    <td className="px-5 py-3">
                      <Badge
                        map={PRIORITY_BADGE}
                        value={t.priority}
                        label={t.priority_display}
                      />
                    </td>
                    {isStaff && (
                      <td className="px-5 py-3 text-slate-600">{t.requester_email}</td>
                    )}
                    <td className="px-5 py-3">
                      {t.is_overdue ? (
                        <span className="text-xs font-medium text-red-600">เกิน SLA</span>
                      ) : (
                        <span className="text-xs text-slate-400">
                          {t.sla_due_at ? new Date(t.sla_due_at).toLocaleString("th-TH") : "—"}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
                {tickets.length === 0 && (
                  <tr>
                    <td colSpan={isStaff ? 7 : 6} className="px-5 py-8 text-center text-slate-400">
                      ยังไม่มีเคส
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {truncated > 0 && (
          <p className="mt-3 text-center text-xs text-slate-400">
            แสดง {tickets.length} เคสแรก · มีอีก {truncated} เคสที่ยังไม่แสดง —
            ใช้ตัวกรองด้านบนเพื่อค้นหา
          </p>
        )}
      </main>

      {creating && (
        <CreateTicketModal
          categories={categories}
          onClose={() => setCreating(false)}
          onCreated={() => {
            setCreating(false);
            load();
          }}
        />
      )}

      {selectedId && (
        <TicketDetail
          id={selectedId}
          isStaff={isStaff}
          onClose={() => setSelectedId(null)}
          onChanged={load}
        />
      )}
    </div>
  );
}

function Badge({ map, value, label }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-medium ${map[value] || "bg-slate-100 text-slate-600"}`}
    >
      {label || value}
    </span>
  );
}

function CreateTicketModal({ categories, onClose, onCreated }) {
  const [form, setForm] = useState({
    title: "",
    description: "",
    category: "",
    priority: "medium",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await createTicket(form);
      onCreated();
    } catch (err) {
      setError(formatError(err) || "สร้างเคสไม่สำเร็จ");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title="แจ้งปัญหาใหม่" onClose={onClose}>
      <form onSubmit={submit}>
        {error && (
          <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
            {error}
          </div>
        )}
        <div className="space-y-3">
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700">หัวข้อ</span>
            <input
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="input"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700">
              รายละเอียด
            </span>
            <textarea
              required
              rows={4}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="input"
            />
          </label>
          <div className="flex gap-3">
            <label className="block flex-1">
              <span className="mb-1 block text-sm font-medium text-slate-700">หมวดหมู่</span>
              <select
                required
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="input"
              >
                <option value="">— เลือก —</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block flex-1">
              <span className="mb-1 block text-sm font-medium text-slate-700">
                ความสำคัญ
              </span>
              <select
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: e.target.value })}
                className="input"
              >
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
        <ModalActions onClose={onClose} saving={saving} />
      </form>
    </Modal>
  );
}

function TicketDetail({ id, isStaff, onClose, onChanged }) {
  const [ticket, setTicket] = useState(null);
  const [comment, setComment] = useState("");
  const [internal, setInternal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [staffOptions, setStaffOptions] = useState([]);

  async function refresh() {
    setError("");
    try {
      setTicket(await getTicket(id));
    } catch {
      setError("โหลดเคสไม่สำเร็จ");
    }
  }

  useEffect(() => {
    refresh();
    if (isStaff) {
      listAssignees()
        .then(setStaffOptions)
        .catch(() => setStaffOptions([]));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function run(fn) {
    setBusy(true);
    setError("");
    try {
      await fn();
      await refresh();
      onChanged();
    } catch (err) {
      setError(formatError(err) || "ทำรายการไม่สำเร็จ");
    } finally {
      setBusy(false);
    }
  }

  if (!ticket) {
    return (
      <Modal title="รายละเอียดเคส" onClose={onClose}>
        <p className="text-slate-400">{error || "กำลังโหลด…"}</p>
      </Modal>
    );
  }

  const canRate =
    !isStaff &&
    ["resolved", "closed"].includes(ticket.status) &&
    !ticket.satisfaction_rating;

  return (
    <Modal title={`${ticket.reference} — ${ticket.title}`} onClose={onClose} wide>
      {error && (
        <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
          {error}
        </div>
      )}

      <div className="mb-3 flex flex-wrap gap-2">
        <Badge map={STATUS_BADGE} value={ticket.status} label={ticket.status_display} />
        <Badge map={PRIORITY_BADGE} value={ticket.priority} label={ticket.priority_display} />
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
          {ticket.category_name}
        </span>
        {ticket.is_overdue && (
          <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-600">
            เกิน SLA
          </span>
        )}
      </div>

      <p className="whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
        {ticket.description}
      </p>
      <p className="mt-2 text-xs text-slate-400">
        ผู้แจ้ง: {ticket.requester_email}
        {ticket.assignee_email && ` · ผู้รับผิดชอบ: ${ticket.assignee_email}`}
      </p>

      {isStaff && (
        <div className="mt-4 flex flex-wrap items-end gap-3">
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-500">
              ผู้รับผิดชอบ
            </span>
            <select
              disabled={busy}
              value={ticket.assignee || ""}
              onChange={(e) =>
                e.target.value && run(() => assignTicket(id, e.target.value))
              }
              className="input max-w-[240px]"
            >
              <option value="">— จ่ายงาน —</option>
              {staffOptions.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.email}
                </option>
              ))}
            </select>
          </label>
          <button
            disabled={busy || ["resolved", "closed"].includes(ticket.status)}
            onClick={() => run(() => resolveTicket(id))}
            className="rounded-lg bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60"
          >
            ปิดเคส (Resolve)
          </button>
        </div>
      )}

      {canRate && (
        <div className="mt-4 rounded-lg border border-slate-200 p-3">
          <p className="mb-2 text-sm font-medium text-slate-700">ให้คะแนนความพึงพอใจ</p>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                disabled={busy}
                onClick={() => run(() => rateTicket(id, { satisfaction_rating: n }))}
                className="h-9 w-9 rounded-lg border border-slate-300 text-sm hover:bg-amber-50"
              >
                {n}
              </button>
            ))}
          </div>
        </div>
      )}

      {ticket.satisfaction_rating && (
        <p className="mt-3 text-sm text-amber-600">
          ความพึงพอใจ: {ticket.satisfaction_rating}/5
        </p>
      )}

      <div className="mt-5">
        <h3 className="mb-2 text-sm font-semibold text-slate-700">
          ความคิดเห็น ({ticket.comments?.length || 0})
        </h3>
        <div className="space-y-2">
          {(ticket.comments || []).map((c) => (
            <div
              key={c.id}
              className={`rounded-lg p-2 text-sm ${c.is_internal ? "bg-amber-50" : "bg-slate-50"}`}
            >
              <p className="text-xs text-slate-400">
                {c.author_email} {c.is_internal && "· ภายใน"}
              </p>
              <p className="text-slate-700">{c.body}</p>
            </div>
          ))}
        </div>

        <div className="mt-3">
          <textarea
            rows={2}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="input"
            placeholder="เพิ่มความคิดเห็น…"
          />
          {isStaff && (
            <label className="mt-1 flex items-center gap-2 text-xs text-slate-600">
              <input
                type="checkbox"
                checked={internal}
                onChange={(e) => setInternal(e.target.checked)}
              />
              เป็นโน้ตภายใน (ผู้แจ้งไม่เห็น)
            </label>
          )}
          <button
            disabled={busy || !comment.trim()}
            onClick={() =>
              run(async () => {
                await addTicketComment({
                  ticket: id,
                  body: comment,
                  is_internal: isStaff ? internal : false,
                });
                setComment("");
                setInternal(false);
              })
            }
            className="mt-2 rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            ส่งความคิดเห็น
          </button>
        </div>
      </div>
    </Modal>
  );
}

function Modal({ title, onClose, wide, children }) {
  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-slate-900/40 px-4 py-8">
      <div
        className={`max-h-full w-full overflow-y-auto rounded-2xl bg-white p-6 shadow-xl ${wide ? "max-w-2xl" : "max-w-md"}`}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 className="text-lg font-semibold text-slate-800">{title}</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
            aria-label="ปิด"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function ModalActions({ onClose, saving }) {
  return (
    <div className="mt-6 flex justify-end gap-2">
      <button
        type="button"
        onClick={onClose}
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
  );
}

function formatError(err) {
  const data = err.response?.data;
  if (!data) return "";
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  return Object.entries(data)
    .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
    .join(" · ");
}
