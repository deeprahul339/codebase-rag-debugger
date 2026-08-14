"use client";

import { useState } from "react";
import UploadRepo from "../components/UploadRepo";
import RepoInfo from "../components/RepoInfo";
import Chat from "../components/Chat";
import type { IndexRepoResponse } from "../types";

export default function Home() {
  const [repo, setRepo] = useState<IndexRepoResponse | null>(null);
  console.log("repo", repo)
  return (
    <main className="mx-auto flex h-screen max-w-3xl flex-col gap-6 p-8">
      <div>
        <h1 className="text-xl font-semibold">Codebase RAG Debugger</h1>
        <p className="text-sm text-gray-500">
          Point it at a GitHub repo, then ask questions with real file:line citations.
        </p>
      </div>

      <UploadRepo onIndexed={setRepo} />

      {repo && (
        <>
          <RepoInfo {...repo} />
          <div className="flex-1 overflow-hidden">
            <Chat repoId={repo.repoId} />
          </div>
        </>
      )}
    </main>
  );
}
