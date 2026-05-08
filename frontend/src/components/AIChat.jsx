import { useState, useRef, useEffect } from "react";
import { api } from "../services/api";
import { Send, Bot, User, Upload, FileText, Loader2 } from "lucide-react";

function Message({ role, content, sources }) {
  return (
    <div className={`flex gap-3 ${role === "user" ? "flex-row-reverse" : ""}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          role === "user" ? "bg-indigo-600" : "bg-gray-200"
        }`}
      >
        {role === "user" ? <User size={16} className="text-white" /> : <Bot size={16} className="text-gray-600" />}
      </div>
      <div className={`max-w-[75%] ${role === "user" ? "items-end" : "items-start"} flex flex-col gap-1`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
            role === "user"
              ? "bg-indigo-600 text-white rounded-tr-none"
              : "bg-white border border-gray-200 text-gray-800 rounded-tl-none"
          }`}
        >
          {content}
        </div>
        {sources && sources.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {sources.map((s) => (
              <span key={s} className="flex items-center gap-1 text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">
                <FileText size={10} /> {s}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function AIChat({ projectId }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hi! I'm your AI project assistant. Ask me anything about your project documents, tasks, or updates.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [docs, setDocs] = useState([]);
  const bottomRef = useRef(null);
  const fileRef = useRef(null);

  useEffect(() => {
    if (projectId) {
      api.getDocuments(projectId).then(setDocs).catch(() => {});
    }
  }, [projectId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: "user", content: input };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);

    // Build history for API (exclude system greeting)
    const history = messages
      .slice(1)
      .map(({ role, content }) => ({ role, content }));

    try {
      const res = await api.chat(projectId, input, history);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `Error: ${e.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !projectId) return;
    setUploading(true);
    try {
      await api.uploadDocument(projectId, file);
      const updated = await api.getDocuments(projectId);
      setDocs(updated);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `✅ Document **${file.name}** uploaded and indexed. You can now ask questions about it!` },
      ]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: `Upload failed: ${e.message}` }]);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Document list */}
      {docs.length > 0 && (
        <div className="flex flex-wrap gap-2 p-3 bg-gray-50 border-b border-gray-200">
          {docs.map((d) => (
            <span key={d.id} className="flex items-center gap-1 text-xs bg-white border border-gray-200 text-gray-600 px-2 py-1 rounded-lg">
              <FileText size={11} /> {d.filename}
              <span className="text-gray-400">({d.chunk_count} chunks)</span>
            </span>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((msg, i) => (
          <Message key={i} {...msg} />
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
              <Bot size={16} className="text-gray-600" />
            </div>
            <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-none px-4 py-3">
              <Loader2 size={16} className="animate-spin text-indigo-500" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="p-3 border-t border-gray-200 bg-white flex gap-2 items-end">
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.txt,.md"
          onChange={handleUpload}
          className="hidden"
        />
        <button
          onClick={() => fileRef.current?.click()}
          disabled={uploading || !projectId}
          className="flex-shrink-0 p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition disabled:opacity-40"
          title="Upload document"
        >
          {uploading ? <Loader2 size={18} className="animate-spin" /> : <Upload size={18} />}
        </button>
        <textarea
          className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 max-h-32"
          rows={1}
          placeholder={projectId ? "Ask about this project..." : "Select a project first"}
          value={input}
          disabled={!projectId}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim() || !projectId}
          className="flex-shrink-0 p-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-40 transition"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
