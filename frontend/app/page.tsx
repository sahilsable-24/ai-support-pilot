"use client";

import { useState, useRef, useEffect } from "react";

type Citation = {
  id: number;
  document_title: string;
  page: number;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  insufficientEvidence?: boolean;
  messageId?: string;
  feedback?: "helpful" | "not_helpful" | null;
};

const API = "http://localhost:8000";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, conversation_id: conversationId }),
      });
      const data = await res.json();

      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          citations: data.citations,
          insufficientEvidence: data.insufficient_evidence,
          messageId: data.message_id,
          feedback: null,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Something went wrong reaching SupportPilot.",
          insufficientEvidence: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleFeedback(index: number, rating: "helpful" | "not_helpful") {
    const message = messages[index];
    if (!message.messageId) return;

    setMessages((prev) =>
      prev.map((m, i) => (i === index ? { ...m, feedback: rating } : m))
    );

    await fetch(`${API}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_id: message.messageId, rating }),
    });
  }

  return (
    <div className="min-h-screen flex flex-col max-w-7xl mx-auto">
      <header className="flex items-center justify-between px-10 py-5 border-b border-line">
        <div className="font-serif-display font-semibold text-[22px] tracking-tight">
          SupportPilot
        </div>
        <nav className="flex gap-7 text-sm">
          <a href="/" className="text-ink border-b-2 border-steel pb-0.5">
            Chat
          </a>
          <a href="/documents" className="text-meta">
            Documents
          </a>
        </nav>
      </header>

      <main className="flex-1 px-10 py-12 flex justify-center overflow-y-auto">
        <div className="w-full max-w-170 flex flex-col gap-8">
          {messages.length === 0 && (
            <p className="text-sm text-meta">
              Ask a question about your support knowledge base.
            </p>
          )}

          {messages.map((m, i) => (
            <div key={i} className={i > 0 ? "border-t border-line pt-6" : ""}>
              <div className="text-xs text-meta mb-2">
                {m.role === "user" ? "You asked" : "SupportPilot"}
              </div>

              {m.role === "user" ? (
                <div className="text-[17px] leading-relaxed">{m.content}</div>
              ) : m.insufficientEvidence ? (
                <>
                  <div className="bg-white border border-line border-l-[3px] border-l-steel px-5 py-4 text-[15px] leading-relaxed max-w-[62ch]">
                    {m.content}
                  </div>
                  <FeedbackButtons
                    messageId={m.messageId}
                    feedback={m.feedback}
                    onFeedback={(rating) => handleFeedback(i, rating)}
                  />
                </>
              ) : (
                <>
                  <AnswerWithCitations text={m.content} citations={m.citations ?? []} />
                  {m.citations && m.citations.length > 0 && (
                    <div className="mt-4 flex flex-col gap-2">
                      {m.citations.map((c) => (
                        <div key={c.id} className="flex items-baseline gap-2.5 text-[13px]">
                          <span className="text-clay font-semibold min-w-3.5">{c.id}</span>
                          <span>{c.document_title}</span>
                          <span className="text-meta">page {c.page}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <FeedbackButtons
                    messageId={m.messageId}
                    feedback={m.feedback}
                    onFeedback={(rating) => handleFeedback(i, rating)}
                  />
                </>
              )}
            </div>
          ))}

          {loading && <p className="text-sm text-meta">Thinking…</p>}
          <div ref={bottomRef} />
        </div>
      </main>

      <div className="border-t border-line px-10 py-6 flex justify-center">
        <form onSubmit={handleSubmit} className="w-full max-w-170 flex gap-2.5">
          <label htmlFor="q" className="sr-only">
            Ask a question
          </label>
          <input
            id="q"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question…"
            disabled={loading}
            className="flex-1 border border-line bg-white rounded-md px-4 py-3 text-[15px] outline-none focus:border-steel"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-ink text-canvas rounded-md px-5 text-sm font-medium disabled:opacity-50"
          >
            Ask
          </button>
        </form>
      </div>
    </div>
  );
}

function FeedbackButtons({
  messageId,
  feedback,
  onFeedback,
}: {
  messageId?: string;
  feedback?: "helpful" | "not_helpful" | null;
  onFeedback: (rating: "helpful" | "not_helpful") => void;
}) {
  if (!messageId) return null;

  return (
    <div className="mt-4 flex items-center gap-2">
      <button
        type="button"
        aria-label="Mark helpful"
        onClick={() => onFeedback("helpful")}
        className={`text-xs px-2 py-1 rounded border ${
          feedback === "helpful"
            ? "border-steel text-steel bg-steel/10"
            : "border-line text-meta hover:text-ink"
        }`}
      >
        Helpful
      </button>
      <button
        type="button"
        aria-label="Mark not helpful"
        onClick={() => onFeedback("not_helpful")}
        className={`text-xs px-2 py-1 rounded border ${
          feedback === "not_helpful"
            ? "border-clay text-clay bg-clay/10"
            : "border-line text-meta hover:text-ink"
        }`}
      >
        Not helpful
      </button>
    </div>
  );
}

function AnswerWithCitations({ text, citations }: { text: string; citations: Citation[] }) {
  const parts = text.split(/(\[\d+(?:,\s*\d+)*\])/g);
  return (
    <div className="text-[17px] leading-relaxed max-w-[62ch]">
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+(?:,\s*\d+)*)\]$/);
        if (!match) return <span key={i}>{part}</span>;

        const ids = match[1].split(",").map((s) => parseInt(s.trim()));
        return (
          <span key={i}>
            {ids.map((id) => {
              const exists = citations.some((c) => c.id === id);
              if (!exists) return null;
              return (
                <button
                  key={id}
                  type="button"
                  aria-label={`View source ${id}`}
                  className="inline-flex items-center justify-center w-5 h-5 rounded bg-clay/[0.14] text-clay border border-clay/30 text-[11px] font-semibold mx-0.5 align-middle"
                >
                  {id}
                </button>
              );
            })}
          </span>
        );
      })}
    </div>
  );
}