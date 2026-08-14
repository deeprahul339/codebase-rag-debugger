import type { IndexRepoResponse } from "../types";

export default function RepoInfo({ repoId, fileCount, chunkCount }: IndexRepoResponse) {
  return (
    <div className="rounded-md border bg-gray-50 px-4 py-3 text-sm">
      <p className="font-medium">Indexed: {repoId}</p>
      <p className="text-gray-600">
        {fileCount} files &middot; {chunkCount} code chunks
      </p>
    </div>
  );
}
