import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth.jsx";
import {
  createChecklistRun,
  getChecklistRun,
  getDailySummary,
  listChecklistRuns,
  listChecklistTemplates,
  submitChecklistRun,
} from "../lib/api.js";

const PAGE_SIZE = 100;

const STATUS_BADGE = {
  in_progress: "bg-amber-100 text-amber-700",
  completed: "bg-green-100 text-green-700",
};

function todayISO() {
  // Local calendar date (YYYY-MM-DD), NOT UTC — the backend stamps
  // performed_on with timezone.localdate(), so toISOString() would be a day
  // off during the early-morning hours when local time is ahead of UTC.
  return new Intl.DateTimeFormat("en-CA").format(new Date());
}

export default function DailyReport() {
  const { user } = useAuth();
  const isStaff = user.role === "admin" || user.role === "staff";

  const [summary, setSummary] = useState(null);
  const [date, setDate] = useState(todayISO());
  const [runs, setRuns] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [truncated, setTruncated] = useState(0);

  const [starting, setStarting] = useState(false);
  const [activeRunId, setActiveRunId] = useState(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [s, r] = await Promise.all([
        getDailySummary(date),
        listChecklistRuns({ page_size: PAGE_SIZE, performed_on: date }),
      ]);
      setSummary(s);
      const rows = r.results ?? r;
      setRuns(rows);
      setTruncated(r.count ? Math.max(0, r.count - rows.length) : 0);
    } catch {
      setError("โหลดรายงานประจำวันไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    listChecklistTemplates()
      .then((d) => setTemplates(d.results ?? d))
      .catch(() => {});
  }, []);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-sm text-slate-400 hover:text-brand-600">
              ← กลับ
            </Link>
            <h1 className="text-lg font-bold text-slate-800">Daily Report & Checklist</h1>
          </div>
          {isStaff && (
            <button
              onClick={() => setStarting(true)}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
            >
              + เริ่มเดินตรวจ
            </button>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-4 flex items-center gap-3">
          <label className="text-sm text-slate-600">วันที่</label>
          <input
            type="date"
            value={date}
            max={todayISO()}
            onChange={(e) => setDate(e.target.value)}
            className="input max-w-[180px]"
          />
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
            {error}
          </div>
        )}

        {summary && (
          <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-5">
            <SummaryCard label="รอบเดินตรวจ" value={summary.checklists.runs} />
            <SummaryCard label="เสร็จแล้ว" value={summary.checklists.completed} />
            <SummaryCard
              label="พบปัญหา"
              value={summary.checklists.with_failures}
              danger={summary.checklists.with_failures > 0}
            />
            <SummaryCard label="Ticket วันนี้" value={summary.tickets.opened} />
            <SummaryCard
              label="ยังเปิดอยู่"
              value={summary.tickets.still_open}
              danger={summary.tickets.still_open > 0}
            />
          </div>
        )}

        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
          รอบเดินตรวจ
        </h2>
        {loading ? (
          <p className="text-slate-400">กำลังโหลด…</p>
        ) : (
          <div className="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-slate-100">
            <table className="min-w-full divide-y divide-slate-100 text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-5 py-3 font-medium">แม่แบบ</th>
                  <th className="px-5 py-3 font-medium">สถานะ</th>
                  <th className="px-5 py-3 font-medium">ผู้ตรวจ</th>
                  <th className="px-5 py-3 font-medium">ผล</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {runs.map((run) => (
                  <tr
                    key={run.id}
                    onClick={() => setActiveRunId(run.id)}
                    className="cursor-pointer hover:bg-slate-50"
                  >
                    <td className="px-5 py-3 font-medium text-slate-700">
                      {run.template_name}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_BADGE[run.status] || "bg-slate-100 text-slate-600"}`}
                      >
                        {run.status_display}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-slate-600">
                      {run.performed_by_email || "—"}
                    </td>
                    <td className="px-5 py-3">
                      {run.status === "completed" &&
                        (run.has_failures ? (
                          <span className="text-xs font-medium text-red-600">พบปัญหา</span>
                        ) : (
                          <span className="text-xs text-green-600">ปกติ</span>
                        ))}
                    </td>
                  </tr>
                ))}
                {runs.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-5 py-8 text-center text-slate-400">
                      ยังไม่มีรอบเดินตรวจในวันนี้
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {truncated > 0 && (
          <p className="mt-3 text-center text-xs text-slate-400">
            แสดง {runs.length} รอบแรก · มีอีก {truncated} รอบที่ยังไม่แสดง
          </p>
        )}
      </main>

      {starting && (
        <StartRunModal
          templates={templates}
          onClose={() => setStarting(false)}
          onStarted={(runId) => {
            setStarting(false);
            setActiveRunId(runId);
            load();
          }}
        />
      )}

      {activeRunId && (
        <RunDetail
          id={activeRunId}
          isStaff={isStaff}
          templates={templates}
          onClose={() => setActiveRunId(null)}
          onChanged={load}
        />
      )}
    </div>
  );
}

function SummaryCard({ label, value, danger }) {
  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-100">
      <p className="text-xs text-slate-400">{label}</p>
      <p className={`text-2xl font-bold ${danger ? "text-red-600" : "text-slate-800"}`}>
        {value}
      </p>
    </div>
  );
}

function StartRunModal({ templates, onClose, onStarted }) {
  const [templateId, setTemplateId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function start(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const run = await createChecklistRun(templateId);
      onStarted(run.id);
    } catch (err) {
      setError(formatError(err) || "เริ่มรอบไม่สำเร็จ");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="เริ่มเดินตรวจ" onClose={onClose}>
      <form onSubmit={start}>
        {error && (
          <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
            {error}
          </div>
        )}
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-slate-700">แม่แบบ</span>
          <select
            required
            value={templateId}
            onChange={(e) => setTemplateId(e.target.value)}
            className="input"
          >
            <option value="">— เลือกแม่แบบ —</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        <ModalActions onClose={onClose} saving={busy} saveLabel="เริ่ม" />
      </form>
    </Modal>
  );
}

function RunDetail({ id, isStaff, templates, onClose, onChanged }) {
  const [run, setRun] = useState(null);
  const [items, setItems] = useState(null); // the run's template items
  const [answers, setAnswers] = useState({}); // itemId -> {passed, reading, note}
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Load the run (its payload carries results but not the full item list) and
  // resolve the template's items from the list the parent already fetched,
  // falling back to a fetch only if it isn't loaded yet. Seed answers from any
  // existing results.
  useEffect(() => {
    let active = true;
    async function loadAll() {
      setError("");
      try {
        const data = await getChecklistRun(id);
        if (!active) return;
        setRun(data);
        const seeded = {};
        for (const r of data.results || []) {
          seeded[r.item] = { passed: r.passed, reading: r.reading, note: r.note };
        }
        setAnswers(seeded);

        let tpl = (templates || []).find((t) => t.id === data.template);
        if (!tpl) {
          const tpls = await listChecklistTemplates();
          if (!active) return;
          tpl = (tpls.results ?? tpls).find((t) => t.id === data.template);
        }
        setItems((tpl?.items || []).filter((i) => i.is_active));
      } catch {
        if (active) setError("โหลดรอบเดินตรวจไม่สำเร็จ");
      }
    }
    loadAll();
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  function setAnswer(itemId, patch) {
    setAnswers((a) => ({ ...a, [itemId]: { ...a[itemId], ...patch } }));
  }

  async function submit() {
    setBusy(true);
    setError("");
    try {
      const results = (items || []).map((it) => ({
        item: it.id,
        passed: answers[it.id]?.passed ?? null,
        reading: answers[it.id]?.reading ?? "",
        note: answers[it.id]?.note ?? "",
      }));
      const updated = await submitChecklistRun(id, { results });
      setRun(updated);
      onChanged();
    } catch (err) {
      setError(formatError(err) || "บันทึกผลไม่สำเร็จ");
    } finally {
      setBusy(false);
    }
  }

  if (!run) {
    return (
      <Modal title="รอบเดินตรวจ" onClose={onClose}>
        <p className="text-slate-400">{error || "กำลังโหลด…"}</p>
      </Modal>
    );
  }

  const editable = isStaff;

  return (
    <Modal title={`${run.template_name} · ${run.performed_on}`} onClose={onClose} wide>
      {error && (
        <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
          {error}
        </div>
      )}

      <div className="mb-3 flex items-center gap-2">
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_BADGE[run.status] || "bg-slate-100 text-slate-600"}`}
        >
          {run.status_display}
        </span>
        {run.performed_by_email && (
          <span className="text-xs text-slate-400">ผู้ตรวจ: {run.performed_by_email}</span>
        )}
      </div>

      {items === null ? (
        <p className="text-slate-400">กำลังโหลดรายการ…</p>
      ) : items.length === 0 ? (
        <p className="text-slate-400">แม่แบบนี้ยังไม่มีรายการ</p>
      ) : (
        <RunItems items={items} answers={answers} editable={editable} onAnswer={setAnswer} />
      )}

      {editable && items && items.length > 0 && (
        <div className="mt-4 flex justify-end">
          <button
            disabled={busy}
            onClick={submit}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {busy ? "กำลังบันทึก…" : run.status === "completed" ? "บันทึกแก้ไข" : "บันทึกผล"}
          </button>
        </div>
      )}
    </Modal>
  );
}

// Renders a row per checklist item with the appropriate input for its type.
function RunItems({ items, answers, editable, onAnswer }) {
  return (
    <div className="space-y-2">
      {items.map((it) => {
        const ans = answers[it.id] || {};
        return (
          <div key={it.id} className="rounded-lg border border-slate-200 p-3">
            <p className="mb-2 text-sm font-medium text-slate-700">
              {it.order}. {it.text}
              {it.unit && <span className="text-slate-400"> ({it.unit})</span>}
            </p>
            <div className="flex flex-wrap items-center gap-3">
              {it.response_type === "reading" ? (
                <input
                  disabled={!editable}
                  value={ans.reading ?? ""}
                  onChange={(e) => onAnswer(it.id, { reading: e.target.value })}
                  className="input max-w-[160px]"
                  placeholder={`ค่าที่อ่านได้${it.unit ? ` (${it.unit})` : ""}`}
                />
              ) : it.response_type === "text" ? (
                <input
                  disabled={!editable}
                  value={ans.note ?? ""}
                  onChange={(e) => onAnswer(it.id, { note: e.target.value })}
                  className="input"
                  placeholder="บันทึก"
                />
              ) : (
                <div className="flex gap-2">
                  <PassButton
                    active={ans.passed === true}
                    disabled={!editable}
                    onClick={() => onAnswer(it.id, { passed: true })}
                    tone="ok"
                  >
                    ผ่าน
                  </PassButton>
                  <PassButton
                    active={ans.passed === false}
                    disabled={!editable}
                    onClick={() => onAnswer(it.id, { passed: false })}
                    tone="fail"
                  >
                    ไม่ผ่าน
                  </PassButton>
                  <PassButton
                    active={ans.passed === null || ans.passed === undefined}
                    disabled={!editable}
                    onClick={() => onAnswer(it.id, { passed: null })}
                    tone="na"
                  >
                    N/A
                  </PassButton>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function PassButton({ active, tone, children, ...props }) {
  const tones = {
    ok: active ? "bg-green-600 text-white" : "text-green-700 hover:bg-green-50",
    fail: active ? "bg-red-600 text-white" : "text-red-600 hover:bg-red-50",
    na: active ? "bg-slate-500 text-white" : "text-slate-500 hover:bg-slate-100",
  };
  return (
    <button
      type="button"
      className={`rounded-lg border border-slate-300 px-3 py-1 text-sm disabled:opacity-60 ${tones[tone]}`}
      {...props}
    >
      {children}
    </button>
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

function ModalActions({ onClose, saving, saveLabel = "บันทึก" }) {
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
        {saving ? "กำลังบันทึก…" : saveLabel}
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
