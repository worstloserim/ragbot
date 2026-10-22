import React, { useCallback, useEffect, useRef, useState } from 'react';

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...options.headers },
    });
  } catch {
    throw new Error(`Could not reach ${API_BASE}. Is the FastAPI server running, and is CORS configured?`);
  }
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

function App() {
  const [threads, setThreads] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [loadingThreads, setLoadingThreads] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const endRef = useRef(null);

  const loadThreads = useCallback(async (selectId = null) => {
    setLoadingThreads(true);
    try {
      const rows = await request('/threads');
      setThreads(rows);
      const nextId = selectId || activeId || rows[0]?.id || null;
      setActiveId(nextId);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingThreads(false);
    }
  }, [activeId]);

  useEffect(() => { loadThreads(); }, []); // initial load

  useEffect(() => {
    if (!activeId) { setMessages([]); return; }
    let cancelled = false;
    setLoadingMessages(true);
    setError('');
    request(`/threads/${activeId}/messages`)
      .then(rows => { if (!cancelled) setMessages(rows); })
      .catch(err => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoadingMessages(false); });
    return () => { cancelled = true; };
  }, [activeId]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, sending]);

  async function createThread() {
    setError('');
    try {
      const created = await request('/threads', { method: 'POST' });
      setThreads(current => [created, ...current]);
      setActiveId(created.id);
      setMessages([]);
    } catch (err) { setError(err.message); }
  }

  async function sendMessage(event) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || !activeId || sending) return;
    setDraft('');
    setError('');
    setSending(true);
    const optimistic = { id: `pending-${Date.now()}`, role: 'user', content };
    setMessages(current => [...current, optimistic]);
    try {
      const result = await request(`/threads/${activeId}/messages`, {
        method: 'POST',
        body: JSON.stringify({ role: 'user', content }),
      });
      setMessages(current => [
        ...current.filter(item => item.id !== optimistic.id),
        result.user_message,
        result.assistant_message,
      ]);
      await loadThreads(activeId);
    } catch (err) {
      setMessages(current => current.filter(item => item.id !== optimistic.id));
      setDraft(content);
      setError(err.message);
    } finally { setSending(false); }
  }

  async function deleteThread(id) {
    if (!window.confirm('Delete this conversation?')) return;
    setError('');
    try {
      await request(`/threads/${id}`, { method: 'DELETE' });
      const remaining = threads.filter(item => item.id !== id);
      setThreads(remaining);
      if (activeId === id) {
        setActiveId(remaining[0]?.id || null);
        if (!remaining.length) setMessages([]);
      }
    } catch (err) { setError(err.message); }
  }

  const activeThread = threads.find(thread => thread.id === activeId);

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">R</div><div><strong>Ragbot</strong><span>Your AI workspace</span></div></div>
        <button className="new-chat" onClick={createThread}><span>＋</span> New chat</button>
        <div className="section-label">RECENT</div>
        <div className="thread-list">
          {loadingThreads && <p className="muted sidebar-hint">Loading chats…</p>}
          {!loadingThreads && threads.length === 0 && <p className="muted sidebar-hint">Your conversations will appear here.</p>}
          {threads.map(thread => (
            <div className={`thread-row ${thread.id === activeId ? 'selected' : ''}`} key={thread.id}>
              <button className="thread-select" onClick={() => setActiveId(thread.id)} title={thread.title}>{thread.title || 'New Chat'}</button>
              <button className="delete-chat" onClick={() => deleteThread(thread.id)} aria-label="Delete conversation" title="Delete">×</button>
            </div>
          ))}
        </div>
        <div className="sidebar-footer"><span className="status-dot" /> API: {API_BASE}</div>
      </aside>

      <section className="chat-panel">
        <header className="topbar">
          <div><span className="eyebrow">CONVERSATION</span><h1>{activeThread?.title || 'New conversation'}</h1></div>
          <div className="connection"><span className="status-dot" /> Backend connected</div>
        </header>
        {error && <div className="error-banner" role="alert"><span>{error}</span><button onClick={() => setError('')} aria-label="Dismiss">×</button></div>}

        <div className="conversation">
          {!activeId ? (
            <div className="welcome"><div className="welcome-icon">✦</div><p className="eyebrow">RAGBOT ASSISTANT</p><h2>What would you like to explore?</h2><p>Start a conversation and I’ll help you work through it.</p><button onClick={createThread}>Start a new chat <span>→</span></button></div>
          ) : loadingMessages ? <div className="loading">Loading messages…</div> : messages.length === 0 ? (
            <div className="welcome"><div className="welcome-icon">✦</div><p className="eyebrow">RAGBOT ASSISTANT</p><h2>How can I help?</h2><p>Ask a question below to start this conversation.</p></div>
          ) : (
            <div className="message-list">
              {messages.map((message, index) => (
                <article className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`} key={message.id ?? index}>
                  <div className="avatar">{message.role === 'user' ? 'Y' : '✦'}</div>
                  <div className="message-body"><div className="message-author">{message.role === 'user' ? 'You' : 'Ragbot'}</div><div className="message-content">{message.content}</div></div>
                </article>
              ))}
              {sending && <article className="message assistant-message"><div className="avatar">✦</div><div className="message-body"><div className="message-author">Ragbot</div><div className="typing"><i /><i /><i /></div></div></article>}
              <div ref={endRef} />
            </div>
          )}
        </div>

        <div className="composer-wrap">
          <form className="composer" onSubmit={sendMessage}>
            <textarea value={draft} onChange={event => setDraft(event.target.value)} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(event); } }} placeholder={activeId ? 'Message Ragbot…' : 'Create a chat to get started'} disabled={!activeId || sending} rows="1" />
            <button className="send-button" type="submit" disabled={!activeId || !draft.trim() || sending} aria-label="Send message">↑</button>
          </form>
          <p className="disclaimer">Ragbot can make mistakes. Check important information.</p>
        </div>
      </section>
    </main>
  );
}

export default App;

