import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth.jsx";
import {
  createBoardColumn,
  createCard,
  createProject,
  getProjectBoard,
  listProjects,
  moveCard,
  updateCard,
} from "../lib/api.js";

const PAGE_SIZE = 100;

const STATUS_BADGE = {
  planning: "bg-blue-100 text-blue-700",
  active: "bg-green-100 text-green-700",
  on_hold: "bg-amber-100 text-amber-700",
  completed: "bg-slate-200 text-slate-600",
  cancelled: "bg-red-100 text-red-600",
};

const PRIORITY_BADGE = {
  low: "bg-slate-100 text-slate-500",
  medium: "bg-sky-100 text-sky-700",
  high: "bg-orange-100 text-orange-700",
  urgent: "bg-red-100 text-red-700",
};

const PRIORITIES = ["low", "medium", "high", "urgent"];

export default function Projects() {
  const { user } = useAuth();
  const isStaff = user.role === "admin" || user.role === "staff";

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [openId, setOpenId] = useState(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await listProjects({ page_size: PAGE_SIZE });
      setProjects(data.results ?? data);
    } catch {
      setError("โหลดโครงการไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (openId) {
    return <Board projectId={openId} isStaff={isStaff} onBack={() => setOpenId(null)} />;
  }

  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-sm text-slate-400 hover:text-brand-600">
              ← กลับ
            </Link>
            <h1 className="text-lg font-bold text-slate-800">Project Management</h1>
          </div>
          {isStaff && (
            <button
              onClick={() => setCreating(true)}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
            >
              + โครงการใหม่
            </button>
          )}
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
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => setOpenId(p.id)}
                className="rounded-2xl bg-white p-5 text-left shadow-sm ring-1 ring-slate-100 transition hover:shadow-md hover:ring-brand-200"
              >
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-mono text-xs text-slate-400">{p.code}</span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_BADGE[p.status] || "bg-slate-100 text-slate-600"}`}
                  >
                    {p.status_display}
                  </span>
                </div>
                <h3 className="font-semibold text-slate-800">{p.name}</h3>
                {p.due_date && (
                  <p className="mt-1 text-xs text-slate-400">กำหนดเสร็จ {p.due_date}</p>
                )}
              </button>
            ))}
            {projects.length === 0 && (
              <p className="text-slate-400">ยังไม่มีโครงการ</p>
            )}
          </div>
        )}
      </main>

      {creating && (
        <CreateProjectModal
          onClose={() => setCreating(false)}
          onCreated={() => {
            setCreating(false);
            load();
          }}
        />
      )}
    </div>
  );
}

function Board({ projectId, isStaff, onBack }) {
  const [board, setBoard] = useState(null);
  const [error, setError] = useState("");
  const [dragCardId, setDragCardId] = useState(null);
  const [addingColumn, setAddingColumn] = useState(false);
  const [addCardCol, setAddCardCol] = useState(null);
  const [editCard, setEditCard] = useState(null);

  async function refresh() {
    setError("");
    try {
      setBoard(await getProjectBoard(projectId));
    } catch {
      setError("โหลดบอร์ดไม่สำเร็จ");
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleDrop(targetColumn, position) {
    const cardId = dragCardId;
    setDragCardId(null);
    if (!cardId) return;
    try {
      await moveCard(cardId, { column: targetColumn.id, position });
      await refresh();
    } catch {
      setError("ย้ายการ์ดไม่สำเร็จ");
    }
  }

  if (!board) {
    return (
      <BoardShell onBack={onBack} title="…">
        <p className="text-slate-400">{error || "กำลังโหลด…"}</p>
      </BoardShell>
    );
  }

  return (
    <BoardShell
      onBack={onBack}
      title={`${board.code} — ${board.name}`}
      action={
        isStaff && (
          <button
            onClick={() => setAddingColumn(true)}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
          >
            + คอลัมน์
          </button>
        )
      }
    >
      {error && (
        <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
          {error}
        </div>
      )}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {board.columns.map((col) => (
          <Column
            key={col.id}
            column={col}
            isStaff={isStaff}
            dragging={!!dragCardId}
            onDragStartCard={setDragCardId}
            onDrop={handleDrop}
            onAddCard={() => setAddCardCol(col)}
            onOpenCard={setEditCard}
          />
        ))}
        {board.columns.length === 0 && (
          <p className="text-slate-400">ยังไม่มีคอลัมน์ — เพิ่มคอลัมน์เพื่อเริ่ม</p>
        )}
      </div>

      {addingColumn && (
        <AddColumnModal
          projectId={projectId}
          nextOrder={board.columns.length}
          onClose={() => setAddingColumn(false)}
          onAdded={() => {
            setAddingColumn(false);
            refresh();
          }}
        />
      )}
      {addCardCol && (
        <AddCardModal
          column={addCardCol}
          onClose={() => setAddCardCol(null)}
          onAdded={() => {
            setAddCardCol(null);
            refresh();
          }}
        />
      )}
      {editCard && (
        <EditCardModal
          card={editCard}
          onClose={() => setEditCard(null)}
          onSaved={() => {
            setEditCard(null);
            refresh();
          }}
        />
      )}
    </BoardShell>
  );
}

function BoardShell({ title, action, onBack, children }) {
  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <button onClick={onBack} className="text-sm text-slate-400 hover:text-brand-600">
              ← โครงการทั้งหมด
            </button>
            <h1 className="text-lg font-bold text-slate-800">{title}</h1>
          </div>
          {action}
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
    </div>
  );
}

function Column({ column, isStaff, dragging, onDragStartCard, onDrop, onAddCard, onOpenCard }) {
  const [over, setOver] = useState(false);
  const cards = column.cards || [];

  // Drop at the end of the lane when releasing over empty space.
  function onLaneDrop(e) {
    e.preventDefault();
    setOver(false);
    onDrop(column, cards.length);
  }

  return (
    <div className="w-72 shrink-0">
      <div className="mb-2 flex items-center justify-between px-1">
        <h3 className="text-sm font-semibold text-slate-700">
          {column.name}{" "}
          <span className="text-slate-400">({cards.length})</span>
        </h3>
        {isStaff && (
          <button
            onClick={onAddCard}
            className="text-sm text-brand-600 hover:underline"
            aria-label="เพิ่มการ์ด"
          >
            +
          </button>
        )}
      </div>
      <div
        onDragOver={isStaff ? (e) => { e.preventDefault(); setOver(true); } : undefined}
        onDragLeave={() => setOver(false)}
        onDrop={isStaff ? onLaneDrop : undefined}
        className={`min-h-[120px] space-y-2 rounded-xl p-2 ${over ? "bg-brand-50 ring-1 ring-brand-200" : "bg-slate-100"}`}
      >
        {cards.map((card, index) => (
          <CardView
            key={card.id}
            card={card}
            isStaff={isStaff}
            dragging={dragging}
            onDragStart={() => onDragStartCard(card.id)}
            onDropBefore={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onDrop(column, index);
            }}
            onOpen={() => onOpenCard(card)}
          />
        ))}
        {cards.length === 0 && (
          <p className="px-2 py-4 text-center text-xs text-slate-400">วางการ์ดที่นี่</p>
        )}
      </div>
    </div>
  );
}

function CardView({ card, isStaff, dragging, onDragStart, onDropBefore, onOpen }) {
  const [over, setOver] = useState(false);
  return (
    <div
      draggable={isStaff}
      onDragStart={onDragStart}
      onDragOver={
        isStaff && dragging
          ? (e) => { e.preventDefault(); setOver(true); }
          : undefined
      }
      onDragLeave={() => setOver(false)}
      onDrop={
        isStaff
          ? (e) => { setOver(false); onDropBefore(e); }
          : undefined
      }
      onClick={onOpen}
      className={`cursor-pointer rounded-lg bg-white p-3 shadow-sm ring-1 ring-slate-100 hover:ring-brand-200 ${over ? "border-t-2 border-brand-400" : ""}`}
    >
      <div className="mb-1 flex items-center justify-between gap-2">
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${PRIORITY_BADGE[card.priority] || "bg-slate-100 text-slate-600"}`}
        >
          {card.priority_display}
        </span>
        {card.is_milestone && (
          <span className="text-xs font-medium text-amber-600">★ milestone</span>
        )}
      </div>
      <p className="text-sm font-medium text-slate-700">{card.title}</p>
      <div className="mt-1 flex items-center justify-between text-xs text-slate-400">
        <span className="truncate">{card.assignee_email || "—"}</span>
        {card.due_date && <span>{card.due_date}</span>}
      </div>
    </div>
  );
}

// ---- Modals ----
function CreateProjectModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ code: "", name: "", description: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await createProject(form);
      onCreated();
    } catch (err) {
      setError(formatError(err) || "สร้างโครงการไม่สำเร็จ");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="โครงการใหม่" onClose={onClose}>
      <form onSubmit={submit}>
        {error && <ErrorBox>{error}</ErrorBox>}
        <div className="space-y-3">
          <Field label="รหัสโครงการ">
            <input required value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="input" />
          </Field>
          <Field label="ชื่อ">
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" />
          </Field>
          <Field label="รายละเอียด">
            <textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="input" />
          </Field>
        </div>
        <ModalActions onClose={onClose} saving={busy} />
      </form>
    </Modal>
  );
}

function AddColumnModal({ projectId, nextOrder, onClose, onAdded }) {
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await createBoardColumn({ project: projectId, name, order: nextOrder });
      onAdded();
    } catch (err) {
      setError(formatError(err) || "เพิ่มคอลัมน์ไม่สำเร็จ");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="เพิ่มคอลัมน์" onClose={onClose}>
      <form onSubmit={submit}>
        {error && <ErrorBox>{error}</ErrorBox>}
        <Field label="ชื่อคอลัมน์">
          <input required value={name} onChange={(e) => setName(e.target.value)} className="input" placeholder="เช่น To Do" />
        </Field>
        <ModalActions onClose={onClose} saving={busy} />
      </form>
    </Modal>
  );
}

function AddCardModal({ column, onClose, onAdded }) {
  const [form, setForm] = useState({ title: "", priority: "medium" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await createCard({ column: column.id, title: form.title, priority: form.priority });
      onAdded();
    } catch (err) {
      setError(formatError(err) || "เพิ่มการ์ดไม่สำเร็จ");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={`เพิ่มการ์ดใน "${column.name}"`} onClose={onClose}>
      <form onSubmit={submit}>
        {error && <ErrorBox>{error}</ErrorBox>}
        <div className="space-y-3">
          <Field label="หัวข้อ">
            <input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="input" />
          </Field>
          <Field label="ความสำคัญ">
            <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })} className="input">
              {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </Field>
        </div>
        <ModalActions onClose={onClose} saving={busy} />
      </form>
    </Modal>
  );
}

function EditCardModal({ card, onClose, onSaved }) {
  const [form, setForm] = useState({
    title: card.title,
    description: card.description || "",
    priority: card.priority,
    due_date: card.due_date || "",
    is_milestone: card.is_milestone,
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await updateCard(card.id, { ...form, due_date: form.due_date || null });
      onSaved();
    } catch (err) {
      setError(formatError(err) || "บันทึกไม่สำเร็จ");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="แก้ไขการ์ด" onClose={onClose}>
      <form onSubmit={submit}>
        {error && <ErrorBox>{error}</ErrorBox>}
        <div className="space-y-3">
          <Field label="หัวข้อ">
            <input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="input" />
          </Field>
          <Field label="รายละเอียด">
            <textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="input" />
          </Field>
          <div className="flex gap-3">
            <Field label="ความสำคัญ" className="flex-1">
              <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })} className="input">
                {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
            <Field label="กำหนดเสร็จ" className="flex-1">
              <input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} className="input" />
            </Field>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={form.is_milestone} onChange={(e) => setForm({ ...form, is_milestone: e.target.checked })} />
            เป็น Milestone
          </label>
        </div>
        <ModalActions onClose={onClose} saving={busy} />
      </form>
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

function ErrorBox({ children }) {
  return <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">{children}</div>;
}

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-slate-900/40 px-4 py-8">
      <div className="max-h-full w-full max-w-md overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 className="text-lg font-semibold text-slate-800">{title}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600" aria-label="ปิด">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function ModalActions({ onClose, saving }) {
  return (
    <div className="mt-6 flex justify-end gap-2">
      <button type="button" onClick={onClose} className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-100">
        ยกเลิก
      </button>
      <button type="submit" disabled={saving} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60">
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
