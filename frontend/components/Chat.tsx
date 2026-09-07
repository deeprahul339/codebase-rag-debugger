"use client";

import { useState } from "react";
import { askQuestion } from "../lib/api";
import type { AgentEvent, ChatMessageData } from "../types";
import ChatMessage from "./ChatMessage";
import AgentActivity from "./AgentActivity";

interface ChatProps {
  repoId: string;
}

export default function Chat({ repoId }: ChatProps) {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [agentEvents, setAgentEvents] = useState<AgentEvent[]>([]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();

    const question = input.trim();

    if (!question || isLoading) return;

    const userMessage: ChatMessageData = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
      createdAt: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    setIsLoading(true);
    setAgentEvents([]);

    try {
      let finalAnswer = "";

      await askQuestion(repoId, question, (event) => {
        setAgentEvents((prev) => [...prev, event]);

        if (event.type === "FINAL") {
          finalAnswer = event.answer;
        }
      });

      if (finalAnswer) {
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: finalAnswer,
            createdAt: Date.now(),
          },
        ]);
      }
    } catch (err) {
      console.error(err);

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "Sorry, something went wrong answering that.",
          createdAt: Date.now(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex-1 space-y-4 overflow-auto">
        {messages.map((m) => (
          <ChatMessage key={m.id} {...m} />
        ))}

        {isLoading && <AgentActivity events={agentEvents} />}

        {isLoading && <p className="text-sm text-gray-400">Thinking...</p>}
      </div>

      <form onSubmit={handleSend} className="flex gap-2 border-t pt-4">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. What calls handleAuth?"
          className="flex-1 rounded-md border px-3 py-2 text-sm"
          disabled={isLoading}
        />

        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="rounded-md bg-black px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
