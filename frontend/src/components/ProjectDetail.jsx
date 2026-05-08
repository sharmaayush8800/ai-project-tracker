import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../services/api";
import TaskList from "./TaskList";
import AIChat from "./AIChat";
import {
  ArrowLeft, Sparkles, FileBarChart2, AlertTriangle,
  MessageSquare, CheckSquare, Activity, Loader2
} from "lucide-react";

const TABS = [
  { id: "tasks", label: "Tasks", icon: CheckSquare },
  { id: "updates", label: "Activity", icon: Activity },
  { id: "chat", label: "AI Chat", icon: MessageSquare },
];

export default function ProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [updates, setUpdates] = useState([]);
  const [tab, setTab] = useState("tasks");
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);
  const [newUpdate, setNewUpdate] = useState("");
  const [postingUpdate, setPostingUpdate] = useState(false);

  const loadData = useCallback(async () => {
    const [p, t, u] = await Promise.all([
      api.getProject(id),
      api.getTasks(id),
      api.getUpdates(id),
    ]);
    setProject(p);
    setTasks(t);
    setUpdates(u);
  }, [id]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSummarize = async () => {
    setLoadingSummary(true);
    const res = await api.summarize(id);
    setSummary(res.summary);
    setLoadingSummary(false);
  };

  const handleReport = async () => {
    setLoadingReport(true);
    await api.generateReport(id);
    setLoadingReport(false);
    alert("Report generated! Check the Reports page.");
  };

  const handlePostUpdate = async () => {
    if (!newUpdate.trim()) return;
    setPostingUpdate(true);
    await api.createUpdate(id, { content: newUpdate });
    setNewUpdate("");
    await loadData();
    setPostingUpdate(false);
  };

  if (!project) {
    return <div className="flex items-center justify-center h-64 text-gray-400">Loading...</div>;
  }

  const risks = updates.filter((u) => u.has_risk === "yes");

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-indigo-600 mb-4 transition"
      >
        <ArrowLeft size={16} /> Back
      </button>

      <div className="flex items-start justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
          {project.description && (
            <p className="text-gray-500 text-sm mt-1">{project.description}</p>
          )}
          {project.slack_channel_name && (
            <span className="text-purple-600 text-sm">#{project.slack_channel_name}</span>
          )}
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={handleSummarize}
            disabled={loadingSummary}
            className="flex items-center gap-1 px-3 py-2 text-sm rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition font-medium disabled:opacity-50"
          >
            {loadingSummary ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            AI Summary
          </button>
          <button
            onClick={handleReport}
            disabled={loadingReport}
            className="flex items-center gap-1 px-3 py-2 text-sm rounded-lg bg-green-50 text-green-700 hover:bg-green-100 transition font-medium disabled:opacity-50"
          >
            {loadingReport ? <Loader2 size={14} className="animate-spin" /> : <FileBarChart2 size={14} />}
            Generate Report
          </button>
        </div>
      </div>

      {/* AI Summary panel */}
      {summary && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 mb-6 text-sm text-gray-700 whitespace-pre-wrap">
          <p className="font-semibold text-indigo-700 mb-1 flex items-center gap-1">
            <Sparkles size={14} /> AI Summary
          </p>
          {summary}
        </div>
      )}

      {/* Risk banner */}
      {risks.length > 0 && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
          <AlertTriangle size={18} className="text-red-500 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-700">{risks.length} Risk(s) Detected</p>
            {risks.slice(0, 3).map((r) => (
              <p key={r.id} className="text-xs text-red-600 mt-0.5">• {r.risk_summary}</p>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {TABS.map(({ id: tid, label, icon: Icon }) => (
          <button
            key={tid}
            onClick={() => setTab(tid)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition -mb-px ${
              tab === tid
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            <Icon size={15} /> {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "tasks" && (
        <TaskList projectId={id} tasks={tasks} onTasksChange={loadData} />
      )}

      {tab === "updates" && (
        <div>
          {/* Post update */}
          <div className="flex gap-2 mb-4">
            <textarea
              className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
              rows={2}
              placeholder="Post an update..."
              value={newUpdate}
              onChange={(e) => setNewUpdate(e.target.value)}
            />
            <button
              onClick={handlePostUpdate}
              disabled={postingUpdate}
              className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition"
            >
              Post
            </button>
          </div>
          <div className="space-y-3">
            {updates.map((u) => (
              <div
                key={u.id}
                className={`p-4 rounded-xl border text-sm ${
                  u.has_risk === "yes" ? "border-red-200 bg-red-50" : "bg-white border-gray-100"
                }`}
              >
                <div className="flex items-center justify-between mb-1 text-xs text-gray-400">
                  <span className="font-medium text-gray-600">{u.author || "Anonymous"}</span>
                  <span className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded-full ${
                      u.source === "slack" ? "bg-purple-100 text-purple-600" : "bg-gray-100 text-gray-500"
                    }`}>
                      {u.source}
                    </span>
                    {new Date(u.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-gray-700">{u.content}</p>
                {u.has_risk === "yes" && u.risk_summary && (
                  <p className="mt-1 text-xs text-red-600 flex items-center gap-1">
                    <AlertTriangle size={11} /> {u.risk_summary}
                  </p>
                )}
              </div>
            ))}
            {updates.length === 0 && (
              <p className="text-center text-gray-400 text-sm py-8">No updates yet.</p>
            )}
          </div>
        </div>
      )}

      {tab === "chat" && (
        <div className="h-[520px] border border-gray-200 rounded-xl overflow-hidden">
          <AIChat projectId={id} />
        </div>
      )}
    </div>
  );
}
