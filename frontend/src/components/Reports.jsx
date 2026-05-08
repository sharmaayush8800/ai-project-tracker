import { useState, useEffect } from "react";
import { api } from "../services/api";
import { FileBarChart2, Calendar, FolderOpen } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function Reports() {
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(null);
  const [reports, setReports] = useState([]);
  const [activeReport, setActiveReport] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getProjects().then(setProjects);
  }, []);

  const selectProject = async (project) => {
    setSelected(project);
    setLoading(true);
    // Reports are fetched from a dedicated endpoint (add to backend if needed)
    // For now we generate one on demand via the API
    setReports([]);
    setActiveReport(null);
    setLoading(false);
  };

  const generateReport = async () => {
    if (!selected) return;
    setLoading(true);
    const report = await api.generateReport(selected.id);
    setReports((r) => [report, ...r]);
    setActiveReport(report);
    setLoading(false);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Progress Reports</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: project list */}
        <div className="lg:col-span-1">
          <h2 className="text-sm font-semibold text-gray-500 uppercase mb-3">Projects</h2>
          <div className="space-y-2">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => selectProject(p)}
                className={`w-full text-left px-4 py-3 rounded-xl border text-sm font-medium transition ${
                  selected?.id === p.id
                    ? "border-indigo-400 bg-indigo-50 text-indigo-700"
                    : "border-gray-200 bg-white text-gray-700 hover:border-gray-300"
                }`}
              >
                <p className="font-medium">{p.name}</p>
                {p.slack_channel_name && (
                  <p className="text-xs text-purple-500 mt-0.5">#{p.slack_channel_name}</p>
                )}
              </button>
            ))}
          </div>

          {selected && (
            <button
              onClick={generateReport}
              disabled={loading}
              className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-xl text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition"
            >
              <FileBarChart2 size={16} />
              {loading ? "Generating..." : "Generate New Report"}
            </button>
          )}
        </div>

        {/* Right: report viewer */}
        <div className="lg:col-span-2">
          {!selected && (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <FolderOpen size={48} className="mb-3 opacity-40" />
              <p>Select a project to view reports</p>
            </div>
          )}

          {selected && reports.length === 0 && !loading && (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <FileBarChart2 size={48} className="mb-3 opacity-40" />
              <p>No reports yet. Click "Generate New Report".</p>
            </div>
          )}

          {activeReport && (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-gray-900">{activeReport.title}</h2>
                <span className="flex items-center gap-1 text-xs text-gray-400">
                  <Calendar size={12} />
                  {new Date(activeReport.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="prose prose-sm max-w-none text-gray-700">
                <ReactMarkdown>{activeReport.content}</ReactMarkdown>
              </div>
            </div>
          )}

          {/* Report list */}
          {reports.length > 1 && (
            <div className="mt-4 space-y-2">
              <h3 className="text-sm font-semibold text-gray-500">Previous Reports</h3>
              {reports.slice(1).map((r) => (
                <button
                  key={r.id}
                  onClick={() => setActiveReport(r)}
                  className="w-full text-left px-4 py-3 rounded-xl border border-gray-200 bg-white hover:border-indigo-300 transition text-sm"
                >
                  <p className="font-medium text-gray-700">{r.title}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(r.created_at).toLocaleDateString()}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
