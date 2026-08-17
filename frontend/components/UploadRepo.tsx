"use client";

import { useState } from "react";
import { checkRepoStatus, indexRepository } from "../lib/api";
import type { IndexRepoResponse } from "../types";

interface UploadRepoProps {
  onIndexed: (result: IndexRepoResponse) => void;
}

export default function UploadRepo({ onIndexed }: UploadRepoProps) {
  const [repoUrl, setRepoUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!repoUrl.trim()) return;

    setIsLoading(true);
    setError(null);
    setStatusMsg(null);

    try {
      // ── Step 1: Fast check (~50 ms) ──────────────────────────────────────
      setStatusMsg("Checking if already indexed…");
      const { repoId, indexed, fileCount, chunkCount } = await checkRepoStatus(
        repoUrl.trim(),
      );

      if (indexed) {
        // Already in Chroma — load immediately without re-embedding.
        setStatusMsg("Already indexed! Loading…");
        onIndexed({ repoId, fileCount: fileCount, chunkCount: chunkCount });
        return;
      }

      // ── Step 2: Full indexing pipeline (slow, first time only) ───────────
      setStatusMsg("Indexing repository… this may take a minute.");
      const result = await indexRepository(repoUrl.trim());
      console.log("index result", result);
      onIndexed(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsLoading(false);
      setStatusMsg(null);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <label htmlFor="repoUrl" className="text-sm font-medium">
        GitHub repository URL
      </label>
      <div className="flex gap-2">
        <input
          id="repoUrl"
          type="text"
          placeholder="https://github.com/owner/repo"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          className="flex-1 rounded-md border px-3 py-2 text-sm"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !repoUrl.trim()}
          className="rounded-md bg-black px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {isLoading ? "Loading…" : "Load repo"}
        </button>
      </div>
      {statusMsg && <p className="text-sm text-blue-600">{statusMsg}</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}
    </form>
  );
}
