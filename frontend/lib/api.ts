import type { IndexRepoResponse } from "../types";
import type { AgentEvent } from "../types";
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function checkRepoStatus(repoUrl: string): Promise<{
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
  onEvent: (event: AgentEvent) => void,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      repoId,
      question,
    }),
  });

  if (!res.ok) {
    throw new Error(`Failed to get answer: ${res.statusText}`);
  }

  if (!res.body) {
    throw new Error("Response body is empty");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");

    // Keep incomplete line for the next chunk
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) {
        continue;
      }

      const json = line.slice(6).trim();

      if (!json) {
        continue;
      }

      try {
        const event: AgentEvent = JSON.parse(json);

        onEvent(event);
      } catch (error) {
        console.error("Failed to parse SSE event:", json);
      }
    }
  }
}
