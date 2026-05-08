import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./components/Dashboard";
import ProjectDetail from "./components/ProjectDetail";
import Reports from "./components/Reports";
import AIChat from "./components/AIChat";
import NewProjectModal from "./components/NewProjectModal";

// Stand-alone AI Chat page — pick a project from a dropdown
function ChatPage() {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState("");
  const [loaded, setLoaded] = useState(false);

  if (!loaded) {
    import("./services/api").then(({ api }) =>
      api.getProjects().then((ps) => { setProjects(ps); setLoaded(true); })
    );
  }

  return (
    <div className="flex flex-col h-screen p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">AI Chat</h1>
      <div className="mb-4">
        <select
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 w-64"
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
        >
          <option value="">-- Select project --</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>
      <div className="flex-1 border border-gray-200 rounded-xl overflow-hidden">
        <AIChat projectId={projectId || null} />
      </div>
    </div>
  );
}

function ProjectsPage() {
  return <Navigate to="/" replace />;
}

export default function App() {
  const [showModal, setShowModal] = useState(false);

  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-gray-50">
        <Sidebar onNewProject={() => setShowModal(true)} />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/chat" element={<ChatPage />} />
          </Routes>
        </main>
      </div>
      {showModal && (
        <NewProjectModal
          onClose={() => setShowModal(false)}
          onCreated={() => { setShowModal(false); window.location.reload(); }}
        />
      )}
    </BrowserRouter>
  );
}
