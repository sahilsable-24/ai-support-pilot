"use client";

import { useState, useEffect } from "react";

type Document = {
  id: string;
  title: string;
  source: string;
  status: string;
  created_at: string;
};

const API = process.env.NEXT_PUBLIC_API_URL;

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function fetchDocuments() {
    const res = await fetch(`${API}/documents`);
    if (res.ok) setDocuments(await res.json());
  }

  useEffect(() => {
    fetchDocuments();
  }, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API}/documents`, { method: "POST", body: formData });
      if (!res.ok) {
        const body = await res.json();
        throw new Error(body.detail || "Upload failed");
      }
      const doc: Document = await res.json();

      await fetch(`${API}/documents/${doc.id}/process`, { method: "POST" });

      await fetchDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function handleDelete(id: string) {
    const confirmed = confirm("Delete this document? This cannot be undone.");
    if (!confirmed) return;

    const res = await fetch(`${API}/documents/${id}`, { method: "DELETE" });
    if (res.ok) {
      await fetchDocuments();
    } else {
      setError("Failed to delete document.");
    }
  }

  return (
    <div className="min-h-screen flex flex-col max-w-7xl mx-auto">
      <header className="flex items-center justify-between px-4 sm:px-6 md:px-10 py-4 md:py-5 border-b border-line">
        <a
          href="/"
          className="font-serif-display font-semibold text-lg md:text-[22px] tracking-tight"
        >
          SupportPilot
        </a>
        <nav className="flex gap-4 sm:gap-7 text-sm">
          <a href="/" className="text-meta">
            Chat
          </a>
          <a href="/documents" className="text-ink border-b-2 border-steel pb-0.5">
            Documents
          </a>
        </nav>
      </header>

      <main className="flex-1 px-4 sm:px-6 md:px-10 py-8 md:py-12 flex justify-center">
        <div className="w-full max-w-170 flex flex-col gap-6 md:gap-8">
          <div>
            <h1 className="font-serif-display text-xl md:text-2xl font-semibold mb-1">
              Knowledge base
            </h1>
            <p className="text-sm text-meta leading-relaxed max-w-[56ch]">
              Documents uploaded here are what SupportPilot searches to answer questions in
              chat. Only content from a document marked{" "}
              <span className="text-steel">ready</span> is used, documents still processing
              or that failed aren&apos;t included in answers.
            </p>
          </div>

          <label className="border border-line bg-white rounded-md px-4 md:px-6 py-8 md:py-10 flex flex-col items-center justify-center text-center cursor-pointer hover:border-steel transition-colors">
            <span className="text-sm font-medium mb-1">
              {uploading ? "Uploading…" : "Choose a file to upload"}
            </span>
            <span className="text-xs text-meta">.pdf, .md, .txt — up to 20MB</span>
            <input
              type="file"
              accept=".pdf,.md,.txt"
              onChange={handleUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>

          {error && (
            <div className="text-sm text-clay border border-clay/30 bg-clay/10 rounded-md px-4 py-3">
              {error}
            </div>
          )}

          <div className="flex flex-col gap-2">
            {documents.length === 0 && (
              <p className="text-sm text-meta">No documents uploaded yet.</p>
            )}
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between gap-3 border-b border-line py-3 text-sm"
              >
                <span className="truncate min-w-0">{doc.title}</span>
                <div className="flex items-center gap-2 md:gap-3 shrink-0">
                  <StatusBadge status={doc.status} />
                  <button
                    type="button"
                    onClick={() => handleDelete(doc.id)}
                    aria-label={`Delete ${doc.title}`}
                    className="text-meta hover:text-clay text-xs"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    ready: "text-steel bg-steel/10",
    pending: "text-meta bg-meta/10",
    processing: "text-meta bg-meta/10",
    failed: "text-clay bg-clay/10",
  };
  return (
    <span className={`text-xs px-2 py-1 rounded whitespace-nowrap ${styles[status] || styles.pending}`}>
      {status}
    </span>
  );
}