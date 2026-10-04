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

const API = process.env.NEXT_PUBLIC_API_URL;

const EXAMPLE_QUESTIONS = [
  "Can I get a refund?",
  "How do I unlock a locked customer account?",
  "What happens if a customer downgrades their plan?",
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleReset() {
    setMessages([]);
    setConversationId(null);
    setInput("");
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "", citations: [], feedback: null },
    ]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, conversation_id: conversationId }),
      });

      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.trim()) continue;
          const event = JSON.parse(line);

          if (event.type === "start") {
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                insufficientEvidence: event.insufficient_evidence,
              };
              return updated;
            });
          } else if (event.type === "token") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              updated[updated.length - 1] = { ...last, content: last.content + event.content };
              return updated;
            });
          } else if (event.type === "done") {
            setConversationId(event.conversation_id);
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              updated[updated.length - 1] = {
                ...last,
                citations: event.citations,
                insufficientEvidence: event.insufficient_evidence,
                messageId: event.message_id,
              };
              return updated;
            });
          } else if (event.type === "error") {
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                role: "assistant",
                content: event.message || "Something went wrong.",
                insufficientEvidence: true,
              };
              return updated;
            });
          }
        }
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Something went wrong reaching SupportPilot.",
          insufficientEvidence: true,
        };
        return updated;
      });
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

  const hasMessages = messages.length > 0;

  return (
    <div className="min-h-screen flex flex-col max-w-7xl mx-auto">
      <header className="flex items-center justify-between px-4 sm:px-6 md:px-10 py-4 md:py-5 border-b border-line">
        <button
          type="button"
          onClick={handleReset}
          className="font-serif-display font-semibold text-lg md:text-[22px] tracking-tight"
        >
          SupportPilot
        </button>
        <nav className="flex gap-4 sm:gap-7 text-sm">
          <a href="/" className="text-ink border-b-2 border-steel pb-0.5">
            Chat
          </a>
          <a href="/documents" className="text-meta">
            Documents
          </a>
        </nav>
      </header>

      <main className="flex-1 px-4 sm:px-6 md:px-10 py-8 md:py-12 flex justify-center overflow-y-auto">
        <div className="w-full max-w-170 flex flex-col gap-6 md:gap-8">
          {!hasMessages && (
            <div className="flex flex-col gap-6">
              <div>
                <h1 className="font-serif-display text-xl md:text-2xl font-semibold mb-2">
                  Ask SupportPilot
                </h1>
                <p className="text-sm text-meta leading-relaxed max-w-[56ch]">
                  SupportPilot answers questions using the documents in your knowledge base.
                  Every answer is grounded in a specific source, shown as a citation below the
                  response. If the knowledge base doesn&apos;t contain the answer, SupportPilot
                  will say so rather than guess.
                </p>
              </div>

              <ChatInputForm
                input={input}
                setInput={setInput}
                loading={loading}
                onSubmit={handleSubmit}
              />

              <div>
                <p className="text-xs text-meta mb-2 uppercase tracking-wide">
                  Try asking
                </p>
                <div className="flex flex-col gap-2">
                  {EXAMPLE_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      type="button"
                      onClick={() => setInput(q)}
                      className="text-left text-sm border border-line bg-white rounded-md px-4 py-2.5 hover:border-steel transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>

              <details className="text-sm">
                <summary className="text-meta cursor-pointer hover:text-ink">
                  How does this work?
                </summary>
                <div className="mt-3 flex flex-col gap-2 text-meta leading-relaxed max-w-[56ch]">
                  <p>
                    Questions are matched against document content using a combination of
                    keyword and semantic search, then re-ranked for relevance before an answer
                    is generated.
                  </p>
                  <p>
                    Citations link each claim back to the specific document and page it came
                    from, so you can verify an answer before relaying it to a customer.
                  </p>
                  <p>
                    No documents yet?{" "}
                    <a href="/documents" className="text-steel underline">
                      Upload some
                    </a>{" "}
                    to get started.
                  </p>
                </div>
              </details>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={i > 0 ? "border-t border-line pt-6" : ""}>
              <div className="text-xs text-meta mb-2">
                {m.role === "user" ? "You asked" : "SupportPilot"}
              </div>

              {m.role === "user" ? (
                <div className="text-base md:text-[17px] leading-relaxed">{m.content}</div>
              ) : m.insufficientEvidence ? (
                <>
                  <div className="bg-white border border-line border-l-[3px] border-l-steel px-4 md:px-5 py-4 text-sm md:text-[15px] leading-relaxed max-w-[62ch]">
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
                        <div
                          key={c.id}
                          className="flex items-baseline gap-2.5 text-xs md:text-[13px]"
                        >
                          <span className="text-clay font-semibold min-w-3.5">{c.id}</span>
                          <span className="wrap-break-word">{c.document_title}</span>
                          <span className="text-meta whitespace-nowrap">page {c.page}</span>
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

          <div ref={bottomRef} />
        </div>
      </main>

      {hasMessages && (
        <div className="border-t border-line px-4 sm:px-6 md:px-10 py-4 md:py-6 flex justify-center">
          <ChatInputForm
            input={input}
            setInput={setInput}
            loading={loading}
            onSubmit={handleSubmit}
          />
        </div>
      )}
    </div>
  );
}

function ChatInputForm({
  input,
  setInput,
  loading,
  onSubmit,
}: {
  input: string;
  setInput: (v: string) => void;
  loading: boolean;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form onSubmit={onSubmit} className="w-full flex gap-2 md:gap-2.5">
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
        className="flex-1 min-w-0 border border-line bg-white rounded-md px-3 md:px-4 py-2.5 md:py-3 text-sm md:text-[15px] outline-none focus:border-steel"
      />
      <button
        type="submit"
        disabled={loading}
        className="bg-ink text-canvas rounded-md px-4 md:px-5 text-sm font-medium disabled:opacity-50 whitespace-nowrap"
      >
        Ask
      </button>
    </form>
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
    <div className="mt-4 flex flex-wrap items-center gap-2">
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
    <div className="text-base md:text-[17px] leading-relaxed max-w-[62ch]">
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