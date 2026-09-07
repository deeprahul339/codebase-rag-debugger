export interface IndexRepoResponse {
  repoId: string;
  fileCount: number;
  chunkCount: number;
}

export interface Source {
  filePath: string;
  startLine: number;
  endLine: number;
  symbolName?: string;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}

export interface ChatMessageData {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  createdAt: number;
}

export type AgentEvent =
  | {
      type: "TOOL_START";
      tool: string;
      arguments: Record<string, unknown>;
    }
  | {
      type: "TOOL_RESULT";
      tool: string;
      message: string;
    }
  | {
      type: "FINAL";
      answer: string;
    }
  | {
      type: "ERROR";
      message: string;
    };
