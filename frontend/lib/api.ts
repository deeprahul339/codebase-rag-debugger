import type { IndexRepoResponse, ChatResponse } from "../types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:4001";

export async function checkRepoStatus(
  repoUrl: string,
): Promise<{
  repoId: string;
  indexed: boolean;
  fileCount: number;
  chunkCount: number;
}> {
  const res = await fetch(`${API_BASE}/api/repository/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repoUrl }),
  });
  if (!res.ok) throw new Error(`Status check failed: ${res.statusText}`);
  return res.json();
}

export async function indexRepository(
  repoUrl: string,
): Promise<IndexRepoResponse> {
  const res = await fetch(`${API_BASE}/api/repository/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repoUrl }),
  });
  if (!res.ok) throw new Error(`Failed to index repository: ${res.statusText}`);
  return res.json();
}

export async function askQuestion(
  repoId: string,
  question: string,
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repoId, question }),
  });
  if (!res.ok) throw new Error(`Failed to get answer: ${res.statusText}`);
  return res.json();
}
