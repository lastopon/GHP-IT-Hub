import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth.jsx";
import {
  createInventoryItem,
  getInventoryItem,
  listInventoryCategories,
  listInventoryItems,
  listLowStock,
  moveStock,
  updateInventoryItem,
} from "../lib/api.js";

// Backend caps page_size at 100; request the max so the list isn't silently
// truncated at the default 20. Narrow with the filters.
const PAGE_SIZE = 100;

const MOVE_KINDS = [
  { value: "receive", label: "รับเข้า (+)" },
  { value: "issue", label: "เบิกออก (−)" },
  { value: "adjust", label: "ปรับยอด (+)" },
];

const KIND_BADGE = {
  receive: "bg-green-100 text-green-700",
  issue: "bg-red-100 text-red-600",
  adjust: "bg-amber-100 text-amber-700",
};

const EMPTY_FORM = {
  sku: "",
  name: "",
  category: "",
  min_stock: 0,
  unit: "pcs",
  location: "",
};

export default function Inventory() {
  const { user } = useAuth();
  const isStaff = user.role === "admin" || user.role === "staff";

  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({ category: "", lowOnly: false });
  const [truncated, setTruncated] = useState(0);

  const [editing, setEditing] = useState(null); // null | {} create | {id,...} edit
  const [selectedId, setSelectedId] = useState(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = { page_size: PAGE_SIZE };
      if (filters.category) params.category = filters.category;
      const data = filters.lowOnly
        ? await listLowStock(params)
        : await listInventoryItems(params);
      const rows = data.results ?? data;
      setItems(rows);
      setTruncated(data.count ? Math.max(0, data.count - rows.length) : 0);
    } catch {
      setError("โหลดรายการคลังไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    listInventoryCategories()
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
            <h1 className="text-lg font-bold text-slate-800">Inventory Management</h1>
          </div>
          {isStaff && (
            <button
              onClick={() => setEditing({})}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
            >
              + เพิ่มอะไหล่
            </button>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <select
            value={filters.category}
            onChange={(e) => setFilters((f) => ({ ...f, category: e.target.value }))}
            className="input max-w-[180px]"
          >
            <option value="">ทุกหมวด</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input
              type="checkbox"
              checked={filters.lowOnly}
              onChange={(e) => setFilters((f) => ({ ...f, lowOnly: e.target.checked }))}
            />
            เฉพาะสต็อกต่ำ
          </label>
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
                  <th className="px-5 py-3 font-medium">SKU</th>
                  <th className="px-5 py-3 font-medium">ชื่อ</th>
                  <th className="px-5 py-3 font-medium">หมวด</th>
                  <th className="px-5 py-3 font-medium text-right">คงเหลือ</th>
                  <th className="px-5 py-3 font-medium text-right">ขั้นต่ำ</th>
                  <th className="px-5 py-3 font-medium">ที่เก็บ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {items.map((it) => (
                  <tr
                    key={it.id}
                    onClick={() => setSelectedId(it.id)}
                    className="cursor-pointer hover:bg-slate-50"
                  >
                    <td className="px-5 py-3 font-mono text-xs text-slate-500">{it.sku}</td>
                    <td className="px-5 py-3 font-medium text-slate-700">{it.name}</td>
                    <td className="px-5 py-3 text-slate-600">{it.category_name}</td>
                    <td className="px-5 py-3 text-right">
                      <span
                        className={`font-medium ${it.is_low_stock ? "text-red-600" : "text-slate-700"}`}
                      >
                        {it.quantity} {it.unit}
                      </span>
                      {it.is_low_stock && (
                        <span className="ml-2 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-600">
                          ต่ำ
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-right text-slate-500">{it.min_stock}</td>
                    <td className="px-5 py-3 text-slate-600">{it.location || "—"}</td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-5 py-8 text-center text-slate-400">
                      ไม่มีรายการ
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {truncated > 0 && (
          <p className="mt-3 text-center text-xs text-slate-400">
            แสดง {items.length} รายการแรก · มีอีก {truncated} รายการที่ยังไม่แสดง —
            ใช้ตัวกรองด้านบนเพื่อค้นหา
          </p>
        )}
      </main>

      {editing && (
        <ItemFormModal
          item={editing.id ? editing : null}
          categories={categories}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
        />
      )}

      {selectedId && (
        <ItemDetail
          id={selectedId}
          isStaff={isStaff}
          onClose={() => setSelectedId(null)}
          onEdit={(it) => {
            setSelectedId(null);
            setEditing(it);
          }}
          onChanged={load}
        />
      )}
    </div>
  );
}

function ItemFormModal({ item, categories, onClose, onSaved }) {
  const [form, setForm] = useState(() =>
    item
      ? {
          sku: item.sku,
          name: item.name,
          category: item.category || "",
          min_stock: item.min_stock,
          unit: item.unit || "pcs",
          location: item.location || "",
        }
      : EMPTY_FORM,
  );
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function set(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const payload = { ...form, min_stock: Number(form.min_stock) || 0 };
      if (item) {
        delete payload.sku; // sku is the immutable identifier
        await updateInventoryItem(item.id, payload);
      } else {
        await createInventoryItem(payload);
      }
      onSaved();
    } catch (err) {
      setError(formatError(err) || "บันทึกไม่สำเร็จ");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={item ? "แก้ไขอะไหล่" : "เพิ่มอะไหล่ใหม่"} onClose={onClose}>
      <form onSubmit={submit}>
        {error && (
          <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
            {error}
          </div>
        )}
        <div className="space-y-3">
          <Field label="SKU">
            <input
              required
              disabled={!!item}
              value={form.sku}
              onChange={(e) => set("sku", e.target.value)}
              className="input disabled:bg-slate-100 disabled:text-slate-400"
            />
          </Field>
          <Field label="ชื่อ">
            <input
              required
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              className="input"
            />
          </Field>
          <Field label="หมวดหมู่">
            <select
              required
              value={form.category}
              onChange={(e) => set("category", e.target.value)}
              className="input"
            >
              <option value="">— เลือก —</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </Field>
          <div className="flex gap-3">
            <Field label="สต็อกขั้นต่ำ" className="flex-1">
              <input
                type="number"
                min={0}
                value={form.min_stock}
                onChange={(e) => set("min_stock", e.target.value)}
                className="input"
              />
            </Field>
            <Field label="หน่วย" className="flex-1">
              <input
                value={form.unit}
                onChange={(e) => set("unit", e.target.value)}
                className="input"
              />
            </Field>
          </div>
          <Field label="ที่เก็บ">
            <input
              value={form.location}
              onChange={(e) => set("location", e.target.value)}
              className="input"
            />
          </Field>
          {!item && (
            <p className="text-xs text-slate-400">
              ยอดคงเหลือเริ่มต้นที่ 0 — ใช้ “รับเข้า” ในหน้ารายละเอียดเพื่อเพิ่มสต็อก
            </p>
          )}
        </div>
        <ModalActions onClose={onClose} saving={saving} />
      </form>
    </Modal>
  );
}

function ItemDetail({ id, isStaff, onClose, onEdit, onChanged }) {
  const [item, setItem] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [move, setMove] = useState({ kind: "receive", quantity: "", counterparty: "" });

  async function refresh() {
    setError("");
    try {
      setItem(await getInventoryItem(id));
    } catch {
      setError("โหลดรายการไม่สำเร็จ");
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function submitMove() {
    const qty = Number(move.quantity);
    if (!qty || qty < 1) {
      setError("จำนวนต้องมากกว่า 0");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await moveStock(id, {
        kind: move.kind,
        quantity: qty,
        counterparty: move.counterparty,
      });
      setMove({ kind: "receive", quantity: "", counterparty: "" });
      await refresh();
      onChanged();
    } catch (err) {
      setError(formatError(err) || "ทำรายการไม่สำเร็จ");
    } finally {
      setBusy(false);
    }
  }

  if (!item) {
    return (
      <Modal title="รายละเอียดอะไหล่" onClose={onClose}>
        <p className="text-slate-400">{error || "กำลังโหลด…"}</p>
      </Modal>
    );
  }

  return (
    <Modal title={`${item.sku} — ${item.name}`} onClose={onClose} wide>
      {error && (
        <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
          {error}
        </div>
      )}

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
          {item.category_name}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${item.is_low_stock ? "bg-red-100 text-red-600" : "bg-green-100 text-green-700"}`}
        >
          คงเหลือ {item.quantity} {item.unit}
          {item.is_low_stock && " · สต็อกต่ำ"}
        </span>
        <span className="text-xs text-slate-400">ขั้นต่ำ {item.min_stock}</span>
        {item.location && (
          <span className="text-xs text-slate-400">· ที่เก็บ {item.location}</span>
        )}
        {isStaff && (
          <button
            onClick={() => onEdit(item)}
            className="ml-auto text-sm text-brand-600 hover:underline"
          >
            แก้ไข
          </button>
        )}
      </div>

      {isStaff && (
        <div className="mt-4 flex flex-wrap items-end gap-2 rounded-lg border border-slate-200 p-3">
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-500">ประเภท</span>
            <select
              value={move.kind}
              onChange={(e) => setMove((m) => ({ ...m, kind: e.target.value }))}
              className="input max-w-[140px]"
            >
              {MOVE_KINDS.map((k) => (
                <option key={k.value} value={k.value}>
                  {k.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-500">จำนวน</span>
            <input
              type="number"
              min={1}
              value={move.quantity}
              onChange={(e) => setMove((m) => ({ ...m, quantity: e.target.value }))}
              className="input max-w-[100px]"
            />
          </label>
          <label className="block flex-1">
            <span className="mb-1 block text-xs font-medium text-slate-500">
              ผู้รับ / ผู้จ่าย (ถ้ามี)
            </span>
            <input
              value={move.counterparty}
              onChange={(e) => setMove((m) => ({ ...m, counterparty: e.target.value }))}
              className="input"
            />
          </label>
          <button
            disabled={busy}
            onClick={submitMove}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            บันทึก
          </button>
        </div>
      )}

      <div className="mt-5">
        <h3 className="mb-2 text-sm font-semibold text-slate-700">
          ประวัติการเคลื่อนไหว ({item.movements?.length || 0})
        </h3>
        <div className="space-y-1 text-sm">
          {(item.movements || []).length === 0 ? (
            <p className="text-slate-400">— ยังไม่มี —</p>
          ) : (
            item.movements.map((m) => (
              <div
                key={m.id}
                className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-1.5"
              >
                <span className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${KIND_BADGE[m.kind] || "bg-slate-100 text-slate-600"}`}
                  >
                    {m.kind_display}
                  </span>
                  <span className="text-slate-600">
                    {m.quantity_delta > 0 ? `+${m.quantity_delta}` : m.quantity_delta} →{" "}
                    {m.quantity_after}
                  </span>
                  {m.counterparty && (
                    <span className="text-xs text-slate-400">· {m.counterparty}</span>
                  )}
                </span>
                <span className="text-xs text-slate-400">
                  {new Date(m.created_at).toLocaleDateString("th-TH")}
                  {m.actor_email && ` · ${m.actor_email}`}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </Modal>
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
