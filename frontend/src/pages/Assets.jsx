import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth.jsx";
import {
  addMaintenanceRecord,
  assignAsset,
  createAsset,
  getAsset,
  listAssetCategories,
  listAssetHolders,
  listAssets,
  returnAsset,
  updateAsset,
} from "../lib/api.js";

const STATUS_BADGE = {
  procured: "bg-blue-100 text-blue-700",
  in_use: "bg-green-100 text-green-700",
  in_store: "bg-slate-100 text-slate-600",
  in_repair: "bg-amber-100 text-amber-700",
  scrapped: "bg-red-100 text-red-600",
};

const STATUSES = Object.keys(STATUS_BADGE);

// Backend caps page_size at 100; request the max so the list isn't silently
// truncated at the default 20. Narrow with the filters.
const PAGE_SIZE = 100;

const EMPTY_FORM = {
  asset_tag: "",
  name: "",
  category: "",
  status: "procured",
  serial_number: "",
  manufacturer: "",
  model: "",
  specs: "",
  purchase_date: "",
  purchase_cost: "",
  warranty_expiry: "",
};

export default function Assets() {
  const { user } = useAuth();
  const isStaff = user.role === "admin" || user.role === "staff";

  const [assets, setAssets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({ status: "", category: "" });
  const [truncated, setTruncated] = useState(0);

  const [editing, setEditing] = useState(null); // null | {} create | {id,...} edit
  const [selectedId, setSelectedId] = useState(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = { page_size: PAGE_SIZE };
      if (filters.status) params.status = filters.status;
      if (filters.category) params.category = filters.category;
      const data = await listAssets(params);
      const rows = data.results ?? data;
      setAssets(rows);
      setTruncated(data.count ? Math.max(0, data.count - rows.length) : 0);
    } catch {
      setError("โหลดรายการสินทรัพย์ไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    listAssetCategories()
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
            <h1 className="text-lg font-bold text-slate-800">IT Asset Management</h1>
          </div>
          {isStaff && (
            <button
              onClick={() => setEditing({})}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
            >
              + เพิ่มสินทรัพย์
            </button>
          )}
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
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
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
                  <th className="px-5 py-3 font-medium">Asset Tag</th>
                  <th className="px-5 py-3 font-medium">ชื่อ</th>
                  <th className="px-5 py-3 font-medium">หมวด</th>
                  <th className="px-5 py-3 font-medium">สถานะ</th>
                  <th className="px-5 py-3 font-medium">ผู้ครอบครอง</th>
                  <th className="px-5 py-3 font-medium">ประกัน</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {assets.map((a) => (
                  <tr
                    key={a.id}
                    onClick={() => setSelectedId(a.id)}
                    className="cursor-pointer hover:bg-slate-50"
                  >
                    <td className="px-5 py-3 font-mono text-xs text-slate-500">
                      {a.asset_tag}
                    </td>
                    <td className="px-5 py-3 font-medium text-slate-700">{a.name}</td>
                    <td className="px-5 py-3 text-slate-600">{a.category_name}</td>
                    <td className="px-5 py-3">
                      <Badge map={STATUS_BADGE} value={a.status} label={a.status_display} />
                    </td>
                    <td className="px-5 py-3 text-slate-600">
                      {a.assigned_to_email || "—"}
                    </td>
                    <td className="px-5 py-3">
                      {a.warranty_expiry ? (
                        <span
                          className={`text-xs ${a.warranty_active ? "text-green-600" : "text-red-600"}`}
                        >
                          {a.warranty_expiry}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
                {assets.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-5 py-8 text-center text-slate-400">
                      ยังไม่มีสินทรัพย์
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {truncated > 0 && (
          <p className="mt-3 text-center text-xs text-slate-400">
            แสดง {assets.length} รายการแรก · มีอีก {truncated} รายการที่ยังไม่แสดง —
            ใช้ตัวกรองด้านบนเพื่อค้นหา
          </p>
        )}
      </main>

      {editing && (
        <AssetFormModal
          asset={editing.id ? editing : null}
          categories={categories}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
        />
      )}

      {selectedId && (
        <AssetDetail
          id={selectedId}
          isStaff={isStaff}
          onClose={() => setSelectedId(null)}
          onEdit={(a) => {
            setSelectedId(null);
            setEditing(a);
          }}
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

function AssetFormModal({ asset, categories, onClose, onSaved }) {
  const [form, setForm] = useState(() =>
    asset
      ? {
          asset_tag: asset.asset_tag,
          name: asset.name,
          category: asset.category || "",
          status: asset.status,
          serial_number: asset.serial_number || "",
          manufacturer: asset.manufacturer || "",
          model: asset.model || "",
          specs: asset.specs || "",
          purchase_date: asset.purchase_date || "",
          purchase_cost: asset.purchase_cost || "",
          warranty_expiry: asset.warranty_expiry || "",
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
      // Empty optional fields must be null, not "" (date/decimal validation).
      const payload = {
        ...form,
        purchase_date: form.purchase_date || null,
        purchase_cost: form.purchase_cost || null,
        warranty_expiry: form.warranty_expiry || null,
      };
      if (asset) {
        delete payload.asset_tag; // tag is the immutable identifier
        await updateAsset(asset.id, payload);
      } else {
        await createAsset(payload);
      }
      onSaved();
    } catch (err) {
      setError(formatError(err) || "บันทึกไม่สำเร็จ");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={asset ? "แก้ไขสินทรัพย์" : "เพิ่มสินทรัพย์ใหม่"} onClose={onClose}>
      <form onSubmit={submit}>
        {error && (
          <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
            {error}
          </div>
        )}
        <div className="space-y-3">
          <div className="flex gap-3">
            <Field label="Asset Tag" className="flex-1">
              <input
                required
                disabled={!!asset}
                value={form.asset_tag}
                onChange={(e) => set("asset_tag", e.target.value)}
                className="input disabled:bg-slate-100 disabled:text-slate-400"
              />
            </Field>
            <Field label="สถานะ" className="flex-1">
              <select
                value={form.status}
                onChange={(e) => set("status", e.target.value)}
                className="input"
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </Field>
          </div>
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
            <Field label="ผู้ผลิต" className="flex-1">
              <input
                value={form.manufacturer}
                onChange={(e) => set("manufacturer", e.target.value)}
                className="input"
              />
            </Field>
            <Field label="รุ่น" className="flex-1">
              <input
                value={form.model}
                onChange={(e) => set("model", e.target.value)}
                className="input"
              />
            </Field>
          </div>
          <Field label="Serial Number">
            <input
              value={form.serial_number}
              onChange={(e) => set("serial_number", e.target.value)}
              className="input"
            />
          </Field>
          <div className="flex gap-3">
            <Field label="วันจัดซื้อ" className="flex-1">
              <input
                type="date"
                value={form.purchase_date}
                onChange={(e) => set("purchase_date", e.target.value)}
                className="input"
              />
            </Field>
            <Field label="วันหมดประกัน" className="flex-1">
              <input
                type="date"
                value={form.warranty_expiry}
                onChange={(e) => set("warranty_expiry", e.target.value)}
                className="input"
              />
            </Field>
          </div>
          <Field label="ราคา (บาท)">
            <input
              type="number"
              step="0.01"
              value={form.purchase_cost}
              onChange={(e) => set("purchase_cost", e.target.value)}
              className="input"
            />
          </Field>
        </div>
        <ModalActions onClose={onClose} saving={saving} />
      </form>
    </Modal>
  );
}

function AssetDetail({ id, isStaff, onClose, onEdit, onChanged }) {
  const [asset, setAsset] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [maint, setMaint] = useState({ open: false, summary: "", vendor: "" });

  async function refresh() {
    setError("");
    try {
      setAsset(await getAsset(id));
    } catch {
      setError("โหลดสินทรัพย์ไม่สำเร็จ");
    }
  }

  useEffect(() => {
    refresh();
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

  if (!asset) {
    return (
      <Modal title="รายละเอียดสินทรัพย์" onClose={onClose}>
        <p className="text-slate-400">{error || "กำลังโหลด…"}</p>
      </Modal>
    );
  }

  return (
    <Modal title={`${asset.asset_tag} — ${asset.name}`} onClose={onClose} wide>
      {error && (
        <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
          {error}
        </div>
      )}

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Badge map={STATUS_BADGE} value={asset.status} label={asset.status_display} />
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
          {asset.category_name}
        </span>
        {asset.warranty_expiry && (
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${asset.warranty_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"}`}
          >
            ประกัน {asset.warranty_active ? "ใช้ได้ถึง" : "หมดเมื่อ"} {asset.warranty_expiry}
          </span>
        )}
        {isStaff && (
          <button
            onClick={() => onEdit(asset)}
            className="ml-auto text-sm text-brand-600 hover:underline"
          >
            แก้ไข
          </button>
        )}
      </div>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        <Detail label="ผู้ผลิต / รุ่น" value={[asset.manufacturer, asset.model].filter(Boolean).join(" ") || "—"} />
        <Detail label="Serial" value={asset.serial_number || "—"} />
        <Detail label="ผู้ครอบครอง" value={asset.assigned_to_email || "ยังไม่มอบหมาย"} />
        <Detail label="วันจัดซื้อ" value={asset.purchase_date || "—"} />
      </dl>
      {asset.specs && (
        <p className="mt-2 whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
          {asset.specs}
        </p>
      )}

      {isStaff && asset.status !== "scrapped" && (
        <div className="mt-4">
          <HolderPicker
            busy={busy}
            currentHolderId={asset.assigned_to}
            onAssign={(holderId) => run(() => assignAsset(id, holderId))}
          />
          {asset.assigned_to && (
            <button
              disabled={busy}
              onClick={() => run(() => returnAsset(id))}
              className="mt-2 rounded-lg bg-slate-600 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-60"
            >
              รับคืน
            </button>
          )}
        </div>
      )}

      <HistorySection title="ประวัติการมอบหมาย" items={asset.assignments} render={(a) => (
        <span>
          {a.holder_email} · {new Date(a.assigned_at).toLocaleDateString("th-TH")}
          {a.returned_at
            ? ` → คืน ${new Date(a.returned_at).toLocaleDateString("th-TH")}`
            : " · ถืออยู่"}
        </span>
      )} />

      <div className="mt-5">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-700">
            ประวัติการซ่อม ({asset.maintenance_records?.length || 0})
          </h3>
          {isStaff && (
            <button
              onClick={() => setMaint((m) => ({ ...m, open: !m.open }))}
              className="text-sm text-brand-600 hover:underline"
            >
              {maint.open ? "ยกเลิก" : "+ บันทึกการซ่อม"}
            </button>
          )}
        </div>
        <div className="space-y-2">
          {(asset.maintenance_records || []).map((r) => (
            <div key={r.id} className="rounded-lg bg-slate-50 p-2 text-sm">
              <p className="font-medium text-slate-700">{r.summary}</p>
              <p className="text-xs text-slate-400">
                {new Date(r.reported_at).toLocaleDateString("th-TH")}
                {r.vendor && ` · ${r.vendor}`}
                {r.is_open ? " · กำลังซ่อม" : " · เสร็จแล้ว"}
              </p>
            </div>
          ))}
        </div>
        {maint.open && isStaff && (
          <div className="mt-2 space-y-2 rounded-lg border border-slate-200 p-3">
            <input
              value={maint.summary}
              onChange={(e) => setMaint((m) => ({ ...m, summary: e.target.value }))}
              className="input"
              placeholder="หัวข้อการซ่อม"
            />
            <input
              value={maint.vendor}
              onChange={(e) => setMaint((m) => ({ ...m, vendor: e.target.value }))}
              className="input"
              placeholder="ผู้ให้บริการ (ถ้ามี)"
            />
            <button
              disabled={busy || !maint.summary.trim()}
              onClick={() =>
                run(async () => {
                  await addMaintenanceRecord({
                    asset: id,
                    summary: maint.summary,
                    vendor: maint.vendor,
                  });
                  setMaint({ open: false, summary: "", vendor: "" });
                })
              }
              className="rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              บันทึก
            </button>
          </div>
        )}
      </div>
    </Modal>
  );
}

// Searchable, capped holder picker. Assigning is an explicit button click
// (not a select onChange), so re-assigning to the current holder works and
// the list never renders the whole user table.
function HolderPicker({ busy, currentHolderId, onAssign }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    const handle = setTimeout(() => {
      listAssetHolders(query)
        .then((r) => active && setResults(r))
        .catch(() => active && setResults([]))
        .finally(() => active && setLoading(false));
    }, 250); // debounce typing
    return () => {
      active = false;
      clearTimeout(handle);
    };
  }, [query]);

  return (
    <div>
      <span className="mb-1 block text-xs font-medium text-slate-500">มอบหมายให้</span>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="input max-w-[280px]"
        placeholder="ค้นหาด้วยอีเมล / ชื่อ…"
      />
      <div className="mt-1 max-h-40 max-w-[280px] divide-y divide-slate-50 overflow-y-auto rounded-lg border border-slate-200">
        {loading ? (
          <p className="px-3 py-2 text-xs text-slate-400">กำลังค้นหา…</p>
        ) : results.length === 0 ? (
          <p className="px-3 py-2 text-xs text-slate-400">ไม่พบผู้ใช้</p>
        ) : (
          results.map((h) => (
            <button
              key={h.id}
              type="button"
              disabled={busy}
              onClick={() => onAssign(h.id)}
              className="flex w-full items-center justify-between px-3 py-1.5 text-left text-sm hover:bg-brand-50 disabled:opacity-60"
            >
              <span className="truncate">{h.email}</span>
              {h.id === currentHolderId && (
                <span className="ml-2 text-xs text-green-600">ปัจจุบัน</span>
              )}
            </button>
          ))
        )}
      </div>
    </div>
  );
}

function HistorySection({ title, items, render }) {
  return (
    <div className="mt-5">
      <h3 className="mb-2 text-sm font-semibold text-slate-700">
        {title} ({items?.length || 0})
      </h3>
      <div className="space-y-1 text-sm text-slate-600">
        {(items || []).length === 0 ? (
          <p className="text-slate-400">— ยังไม่มี —</p>
        ) : (
          items.map((it) => (
            <div key={it.id} className="rounded-lg bg-slate-50 px-2 py-1.5">
              {render(it)}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <div>
      <dt className="text-xs text-slate-400">{label}</dt>
      <dd className="text-slate-700">{value}</dd>
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
