import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, FolderKanban, MessageSquare, FileText, Plus } from "lucide-react";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/projects", icon: FolderKanban, label: "Projects" },
  { to: "/reports", icon: FileText, label: "Reports" },
  { to: "/chat", icon: MessageSquare, label: "AI Chat" },
];

export default function Sidebar({ onNewProject }) {
  const { pathname } = useLocation();

  return (
    <aside className="w-60 min-h-screen bg-gray-900 text-white flex flex-col py-6 px-4 gap-2 border-r border-gray-800">
      {/* Logo */}
      <div className="flex items-center gap-2 px-2 mb-6">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm">
          AI
        </div>
        <span className="font-bold text-lg tracking-tight">ProjectTracker</span>
      </div>

      {/* New Project button */}
      <button
        onClick={onNewProject}
        className="flex items-center gap-2 w-full px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition mb-4"
      >
        <Plus size={16} />
        New Project
      </button>

      {/* Nav links */}
      {navItems.map(({ to, icon: Icon, label }) => {
        const active = pathname === to || (to !== "/" && pathname.startsWith(to));
        return (
          <Link
            key={to}
            to={to}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
              active
                ? "bg-indigo-700 text-white"
                : "text-gray-400 hover:bg-gray-800 hover:text-white"
            }`}
          >
            <Icon size={18} />
            {label}
          </Link>
        );
      })}

      {/* Slack status indicator */}
      <div className="mt-auto pt-4 border-t border-gray-800 px-2">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          Slack connected
        </div>
      </div>
    </aside>
  );
}
