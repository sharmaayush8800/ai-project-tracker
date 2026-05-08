import { useState } from "react";
import { api } from "../services/api";
import { Plus, Trash2, ChevronDown, Bot } from "lucide-react";

const STATUS_OPTIONS = ["todo", "in_progress", "blocked", "done"];
const PRIORITY_COLORS = {
  low: "bg-gray-100 text-gray-600",
  medium: "bg-blue-100 text-blue-700",
  high: "bg-orange-100 text-orange-700",
  critical: "bg-red-100 text-red-700",
};
const STATUS_COLORS = {
  todo: "bg-gray-100 text-gray-600",
  in_progress: "bg-blue-100 text-blue-700",
  blocked: "bg-red-100 text-red-700",
  done: "bg-green-100 text-green-700",
};

export default function TaskList({ projectId, tasks, onTasksChange }) {
  const [newTitle, setNewTitle] = useState("");
  const [extracting, setExtracting] = useState(false);
  const [extractText, setExtractText] = useState("");
  const [showExtract, setShowExtract] = useState(false);

  const addTask = async () => {
    if (!newTitle.trim()) return;
    await api.createTask(projectId, { title: newTitle });
    setNewTitle("");
    onTasksChange();
  };

  const changeStatus = async (taskId, status) => {
    await api.updateTask(projectId, taskId, { status });
    onTasksChange();
  };

  const deleteTask = async (taskId) => {
    await api.deleteTask(projectId, taskId);
    onTasksChange();
  };

  const handleExtract = async () => {
    if (!extractText.trim()) return;
    setExtracting(true);
    await api.extractTasks(projectId, extractText);
    setExtracting(false);
    setExtractText("");
    setShowExtract(false);
    onTasksChange();
  };

  return (
    <div>
      {/* Header + AI Extract toggle */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Tasks ({tasks.length})</h2>
        <button
          onClick={() => setShowExtract(!showExtract)}
          className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition font-medium"
        >
          <Bot size={14} />
          AI Extract Tasks
        </button>
      </div>

      {/* AI Extract panel */}
      {showExtract && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 mb-4">
          <p className="text-xs text-indigo-600 font-medium mb-2">
            Paste a Slack conversation or text — AI will extract action items:
          </p>
          <textarea
            className="w-full border border-indigo-200 rounded-lg p-2 text-sm bg-white resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
            rows={4}
            placeholder="Paste conversation here..."
            value={extractText}
            onChange={(e) => setExtractText(e.target.value)}
          />
          <button
            onClick={handleExtract}
            disabled={extracting}
            className="mt-2 px-4 py-1.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition"
          >
            {extracting ? "Extracting..." : "Extract Tasks"}
          </button>
        </div>
      )}

      {/* Add task */}
      <div className="flex gap-2 mb-4">
        <input
          className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          placeholder="Add a task..."
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addTask()}
        />
        <button
          onClick={addTask}
          className="px-3 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
        >
          <Plus size={16} />
        </button>
      </div>

      {/* Task rows */}
      <div className="space-y-2">
        {tasks.length === 0 && (
          <p className="text-center text-gray-400 text-sm py-6">No tasks yet.</p>
        )}
        {tasks.map((task) => (
          <div
            key={task.id}
            className={`flex items-center gap-3 p-3 rounded-xl border bg-white ${
              task.status === "done" ? "opacity-60" : ""
            }`}
          >
            {/* Status badge */}
            <select
              value={task.status}
              onChange={(e) => changeStatus(task.id, e.target.value)}
              className={`text-xs font-medium px-2 py-1 rounded-lg border-0 cursor-pointer ${STATUS_COLORS[task.status]}`}
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>{s.replace("_", " ")}</option>
              ))}
            </select>

            {/* Title */}
            <span
              className={`flex-1 text-sm ${task.status === "done" ? "line-through text-gray-400" : "text-gray-800"}`}
            >
              {task.title}
            </span>

            {/* Priority */}
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${PRIORITY_COLORS[task.priority]}`}>
              {task.priority}
            </span>

            {/* Source badge */}
            {task.source !== "manual" && (
              <span className="text-xs bg-purple-100 text-purple-600 px-2 py-0.5 rounded-full">
                {task.source === "ai_extracted" ? "AI" : "Slack"}
              </span>
            )}

            {/* Assignee */}
            {task.assignee && (
              <span className="text-xs text-gray-500 hidden sm:block">{task.assignee}</span>
            )}

            {/* Delete */}
            <button
              onClick={() => deleteTask(task.id)}
              className="text-gray-300 hover:text-red-400 transition"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
