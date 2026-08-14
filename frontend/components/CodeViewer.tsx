interface CodeViewerProps {
  filePath: string;
  content: string;
  highlightStart?: number;
  highlightEnd?: number;
}

/**
 * v1: plain <pre> block. Swap in a real highlighter (e.g. shiki or
 * react-syntax-highlighter) once the core loop works end-to-end —
 * don't waste day 1-2 on syntax highlighting before retrieval works.
 */
export default function CodeViewer({ filePath, content, highlightStart, highlightEnd }: CodeViewerProps) {
  const lines = content.split("\n");

  return (
    <div className="overflow-auto rounded-md border bg-gray-900 text-gray-100">
      <div className="border-b border-gray-700 px-3 py-1.5 text-xs font-mono text-gray-400">
        {filePath}
      </div>
      <pre className="p-3 text-xs leading-5">
        {lines.map((line, i) => {
          const lineNum = i + 1;
          const isHighlighted =
            highlightStart && highlightEnd && lineNum >= highlightStart && lineNum <= highlightEnd;
          return (
            <div key={i} className={isHighlighted ? "bg-yellow-500/20" : ""}>
              <span className="mr-3 select-none text-gray-500">{lineNum}</span>
              {line}
            </div>
          );
        })}
      </pre>
    </div>
  );
}
