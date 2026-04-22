import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./index.css";

const API_KEY = import.meta.env.VITE_APP_API_KEY || "";

const SUGGESTIONS = [
    { icon: "📊", text: "Analyze a dataset", query: "Analyze this sales dataset for key trends and insights" },
    { icon: "🏋️", text: "Get a workout plan", query: "Create a weekly workout plan for muscle building" },
    { icon: "⚽", text: "Football tweet", query: "Generate a hype tweet about the Champions League final" },
    { icon: "🌾", text: "Crop advice", query: "What crops are best to plant in spring in tropical climate?" },
];

/* ── helpers ─────────────────────────────── */
function classifyTrace(t) {
    if (typeof t !== "string") {
        try { t = JSON.stringify(t); } catch { t = String(t); }
    }
    if (t.includes("Discovery")) return { type: "discovery", icon: "🔍", label: "Discovery" };
    if (t.includes("LLM Decision") || t.includes("Matched")) return { type: "decision", icon: "🧠", label: "LLM Decision" };
    if (t.includes("Tool Call")) return { type: "tool", icon: "🛠️", label: "Tool Call" };
    if (t.includes("File")) return { type: "file", icon: "📎", label: "File" };
    if (t.includes("Error") || t.includes("error")) return { type: "error", icon: "❌", label: "Error" };
    return { type: "info", icon: "📋", label: "Info" };
}

function MiniMd({ text }) {
    if (typeof text !== "string") {
        try { text = JSON.stringify(text); } catch { text = String(text); }
    }
    const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
    return (
        <>
            {parts.map((p, i) => {
                if (typeof p !== "string") return null;
                if (p.startsWith("**") && p.endsWith("**")) return <strong key={i}>{p.slice(2, -2)}</strong>;
                if (p.startsWith("`") && p.endsWith("`")) return <code key={i}>{p.slice(1, -1)}</code>;
                return <span key={i}>{p}</span>;
            })}
        </>
    );
}

/* ═══════════════════════════════════════════
   APP
   ═══════════════════════════════════════════ */
export default function App() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [trace, setTrace] = useState([]);
    const [agents, setAgents] = useState([]);
    const [activeAgent, setActiveAgent] = useState(null);
    const [file, setFile] = useState(null);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const endRef = useRef(null);
    const taRef = useRef(null);
    const fileRef = useRef(null);

    /* fetch agent registry on mount */
    useEffect(() => {
        fetch("/api/agents", { headers: { "X-API-Key": API_KEY } })
            .then(r => r.json())
            .then(d => setAgents(d.agents || []))
            .catch(() => { });
    }, []);

    useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);
    useEffect(() => { taRef.current?.focus(); }, []);

    const handleInput = useCallback(e => {
        setInput(e.target.value);
        e.target.style.height = "auto";
        e.target.style.height = Math.min(e.target.scrollHeight, 140) + "px";
    }, []);

    const onFile = useCallback(e => {
        const f = e.target.files?.[0];
        if (!f) return;
        const reader = new FileReader();
        reader.onload = () => setFile({ name: f.name, base64: reader.result.split(",")[1] });
        reader.readAsDataURL(f);
        e.target.value = "";
    }, []);

    /* ── send ── */
    const send = useCallback(async (text) => {
        const query = (text || input).trim();
        if (!query || loading) return;

        setMessages(p => [...p, { id: Date.now(), role: "user", text: query, file: file?.name }]);
        setInput("");
        if (taRef.current) taRef.current.style.height = "auto";
        setLoading(true);
        setActiveAgent("coordinator");

        const payload = { query, user_id: "ui_user" };
        if (file) { payload.file_content_base64 = file.base64; payload.filename = file.name; }

        try {
            const res = await fetch("/api/query", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
                body: JSON.stringify(payload),
            });
            if (!res.ok) throw new Error(`Server ${res.status}`);
            const data = await res.json();

            setMessages(p => [...p, { id: Date.now() + 1, role: "assistant", text: data.response || "No response." }]);

            if (data.trace?.length) {
                const events = data.trace.map((t, i) => ({ text: t, ts: Date.now() + i, ...classifyTrace(t) }));
                setTrace(p => [...p, ...events]);
                // detect which agent was used
                const delegated = data.trace.find(t => typeof t === "string" && t.includes("Matched"));
                if (delegated) {
                    const m = delegated.match(/`([^`]+)`/);
                    if (m) setActiveAgent(m[1]);
                }
            }
        } catch (err) {
            setMessages(p => [...p, { id: Date.now() + 1, role: "assistant", text: `⚠️ ${err.message}` }]);
        } finally {
            setFile(null);
            setLoading(false);
            setTimeout(() => setActiveAgent(null), 3000);
            taRef.current?.focus();
        }
    }, [input, loading, file]);

    const onKey = e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } };

    const newChat = () => {
        setMessages([]); setTrace([]); setInput(""); setFile(null);
        taRef.current?.focus();
    };

    /* ── render ── */
    return (
        <div className="app">
            {/* ═══ SIDEBAR ═══ */}
            <aside className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>
                <div className="sb-head">
                    <div className="sb-logo">
                        <span className="sb-icon">🤖</span>
                        <div>
                            <h1 className="sb-title">A2A Coordinator</h1>
                            <p className="sb-sub">Multi-Agent Orchestration</p>
                        </div>
                    </div>
                    <button className="sb-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
                        {sidebarOpen ? "◀" : "▶"}
                    </button>
                </div>

                {sidebarOpen && (
                    <>
                        <div className="sb-section">
                            <h3 className="sb-section-title">Agent Registry</h3>
                            <p className="sb-section-sub">{agents.length} agents discovered</p>
                        </div>

                        <div className="sb-agents">
                            {agents.map(a => (
                                <div
                                    key={a.name}
                                    className={`agent-card ${activeAgent === a.name ? "active" : ""}`}
                                >
                                    <div className="agent-top">
                                        <span className={`agent-dot ${activeAgent === a.name ? "pulse" : ""}`} />
                                        <span className="agent-name">{a.name.replace(/_/g, " ")}</span>
                                        <span className="agent-proto">{a.protocol}</span>
                                    </div>
                                    {a.description && <p className="agent-desc">{a.description}</p>}
                                    {a.capabilities?.length > 0 && (
                                        <div className="agent-caps">
                                            {a.capabilities.map((c, i) => (
                                                <span key={i} className="cap-pill">{c.name.replace(/_/g, " ")}</span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))}

                            {agents.length === 0 && (
                                <div className="sb-empty">
                                    <p>No agents discovered.</p>
                                    <p className="sb-empty-hint">Start the backend to see registered agents.</p>
                                </div>
                            )}
                        </div>

                        <div className="sb-footer">
                            <button className="btn-new" onClick={newChat}>✨ New Chat</button>
                        </div>
                    </>
                )}
            </aside>

            {/* ═══ CHAT ═══ */}
            <main className="chat">
                {/* header bar */}
                <div className="chat-head">
                    <div className="ch-left">
                        <button className="sb-toggle mobile-only" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
                        <span className="ch-title">Chat</span>
                        {loading && <span className="ch-status">●&nbsp; Coordinating...</span>}
                    </div>
                    <div className="ch-right">
                        <span className="pill pill-a2a">A2A</span>
                        <span className="pill pill-lc">LangChain</span>
                    </div>
                </div>

                {/* messages */}
                <div className="messages">
                    {messages.length === 0 && !loading && (
                        <div className="welcome">
                            <div className="w-icon">🌐</div>
                            <h2>A2A Coordinator</h2>
                            <p>Route your request to the right specialized agent. Pick a suggestion or type your own.</p>
                            <div className="suggestions">
                                {SUGGESTIONS.map(s => (
                                    <button key={s.text} className="sug" onClick={() => send(s.query)}>
                                        <span className="sug-icon">{s.icon}</span>
                                        <span>{s.text}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {messages.map(m => (
                        <div key={m.id} className={`msg msg-${m.role}`}>
                            <div className="avatar">{m.role === "user" ? "👤" : "🤖"}</div>
                            <div className="msg-body">
                                {m.file && <div className="msg-file">📄 {m.file}</div>}
                                <div className="msg-text">
                                    {m.role === "assistant" ? (
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
                                    ) : m.text}
                                </div>
                            </div>
                        </div>
                    ))}

                    {loading && (
                        <div className="msg msg-assistant">
                            <div className="avatar">🤖</div>
                            <div className="msg-body">
                                <div className="msg-text">
                                    <span className="typing"><span /><span /><span /></span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={endRef} />
                </div>

                {/* input */}
                <div className="input-area">
                    {file && (
                        <div className="file-chip">
                            <span>📄 {file.name}</span>
                            <button className="file-x" onClick={() => setFile(null)}>✕</button>
                        </div>
                    )}
                    <div className="input-box">
                        <button className="attach" onClick={() => fileRef.current?.click()} disabled={loading} title="Attach file">📎</button>
                        <input ref={fileRef} type="file" accept=".csv,.xlsx,.json,.txt" onChange={onFile} hidden />
                        <textarea ref={taRef} value={input} onChange={handleInput} onKeyDown={onKey}
                            placeholder="Ask anything — I'll route it to the right agent..." rows={1} disabled={loading} />
                        <button className="send" onClick={() => send()} disabled={!input.trim() || loading}>
                            {loading ? <span className="spinner" /> : (
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M22 2L11 13" /><path d="M22 2L15 22L11 13L2 9L22 2Z" />
                                </svg>
                            )}
                        </button>
                    </div>
                    <p className="hint">Enter to send · Shift+Enter new line · 📎 attach dataset</p>
                </div>
            </main>

            {/* ═══ TRACE PANEL ═══ */}
            <aside className="trace">
                <div className="tr-head">
                    <h3>🛠️ Coordination Trace</h3>
                    {trace.length > 0 && <button className="tr-clear" onClick={() => setTrace([])}>Clear</button>}
                </div>

                <div className="tr-body">
                    {trace.length === 0 ? (
                        <div className="tr-empty">
                            <div className="tr-empty-icon">📡</div>
                            <p>Send a message to see the A2A coordination trace</p>
                            <p className="tr-empty-sub">Agent discovery → LLM routing → delegation → response</p>
                        </div>
                    ) : (
                        <div className="tr-timeline">
                            {trace.map((ev, i) => (
                                <div key={i} className={`tr-ev tr-${ev.type}`}>
                                    <div className="tr-dot-col">
                                        <span className="tr-dot" />
                                        {i < trace.length - 1 && <span className="tr-line" />}
                                    </div>
                                    <div className="tr-content">
                                        <div className="tr-label">
                                            <span className="tr-icon">{ev.icon}</span>
                                            <span className="tr-label-text">{ev.label}</span>
                                            <span className="tr-time">{new Date(ev.ts).toLocaleTimeString()}</span>
                                        </div>
                                        <div className="tr-detail"><MiniMd text={ev.text} /></div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </aside>

            {/* ═══ BOTTOM BAR ═══ */}
            <footer className="bottom-bar">
                <div className="bb-left">
                    <span className={`dot ${loading ? "busy" : "ok"}`} />
                    <span>{loading ? "Coordinating agents..." : "Connected · localhost:8000"}</span>
                </div>
                <span>A2A Protocol · Smainos Case Study</span>
            </footer>
        </div>
    );
}
