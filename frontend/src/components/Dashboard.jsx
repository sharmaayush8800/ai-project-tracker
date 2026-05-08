import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { AlertTriangle, CheckCircle, Clock, FolderOpen, TrendingUp } from "lucide-react";

const STATUS_COLORS = {
  active: "bg-green-100 text-green-800",
  on_hold: "bg-yellow-100 text-yellow-800",
  completed: "bg-blue-100 text-blue-800",
  archived: "bg-gray-100 text-gray-600",
};

function StatCard({ label, value, icon: Icon, color }) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 flex items-center gap-4">
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getProjects().then(setProjects).finally(() => setLoading(false));
  }, []);

  const stats = {
    total: projects.length,
    active: projects.filter((p) => p.status === "active").length,
    totalTasks: projects.reduce((s, p) => s + (p.task_count || 0), 0),
    risks: projects.reduce((s, p) => s + (p.open_risk_count || 0), 0),
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        Loading dashboard...
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Projects" value={stats.total} icon={FolderOpen} color="bg-indigo-500" />
        <StatCard label="Active Projects" value={stats.active} icon={TrendingUp} color="bg-green-500" />
        <StatCard label="Total Tasks" value={stats.totalTasks} icon={CheckCircle} color="bg-blue-500" />
        <StatCard label="Open Risks" value={stats.risks} icon={AlertTriangle} color="bg-red-500" />
      </div>

      {/* Projects grid */}
      <h2 className="text-lg font-semibold text-gray-700 mb-3">All Projects</h2>
      {projects.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <FolderOpen size={48} className="mx-auto mb-3 opacity-40" />
          <p>No projects yet. Create one to get started!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p) => (
            <Link
              key={p.id}
              to={`/projects/${p.id}`}
              className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 hover:border-indigo-300 hover:shadow-md transition group"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold text-gray-900 group-hover:text-indigo-600 transition line-clamp-1">
                  {p.name}
                </h3>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[p.status]}`}>
                  {p.status.replace("_", " ")}
                </span>
              </div>
              {p.description && (
                <p className="text-sm text-gray-500 line-clamp-2 mb-3">{p.description}</p>
              )}
              <div className="flex items-center gap-4 text-xs text-gray-400">
                <span className="flex items-center gap-1">
                  <CheckCircle size={12} /> {p.task_count} tasks
                </span>
                {p.open_risk_count > 0 && (
                  <span className="flex items-center gap-1 text-red-500">
                    <AlertTriangle size={12} /> {p.open_risk_count} risks
                  </span>
                )}
                {p.slack_channel_name && (
                  <span className="text-purple-500">#{p.slack_channel_name}</span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
