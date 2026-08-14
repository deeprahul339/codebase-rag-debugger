import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "Codebase RAG Debugger",
  description: "Ask questions about any GitHub repo, grounded with real citations.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
