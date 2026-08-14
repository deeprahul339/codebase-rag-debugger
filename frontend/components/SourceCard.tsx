import type { Source } from "../types";

export default function SourceCard({ filePath, startLine, endLine, symbolName }: Source) {
  return (
    <div className="rounded border px-3 py-2 text-xs text-gray-700">
      <span className="font-mono">
        {filePath}:{startLine}-{endLine}
      </span>
      {symbolName && <span className="ml-2 text-gray-500">({symbolName})</span>}
    </div>
  );
}
