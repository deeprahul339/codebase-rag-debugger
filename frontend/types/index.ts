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
