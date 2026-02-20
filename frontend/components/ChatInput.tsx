"use client";

import { useState, FormEvent, KeyboardEvent } from "react";
import { Send, Mic, Loader2 } from "lucide-react";

interface ChatInputProps {
  onSubmit: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSubmit,
  isLoading = false,
  placeholder = "Ask anything about car deals, market trends, or specific models...",
}: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSubmit(input.trim());
      setInput("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative w-full">
      <div className="relative flex items-center">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isLoading}
          className="w-full px-4 sm:px-6 py-3 sm:py-4 pr-20 sm:pr-24 rounded-full bg-background-secondary border border-border
                     text-sm sm:text-base text-white placeholder-gray-500
                     focus:outline-none focus:border-accent focus:shadow-glow
                     transition-all duration-300
                     disabled:opacity-50 disabled:cursor-not-allowed"
        />

        <div className="absolute right-1.5 sm:right-2 flex items-center gap-0.5 sm:gap-1">
          {/* Mic button (decorative for now) */}
          <button
            type="button"
            className="p-1.5 sm:p-2 text-gray-400 hover:text-accent transition-colors hidden sm:block"
            title="Voice input (coming soon)"
          >
            <Mic className="w-5 h-5" />
          </button>

          {/* Submit button */}
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="p-2 rounded-full bg-accent text-background hover:bg-accent-dim
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all duration-200"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
            ) : (
              <Send className="w-4 h-4 sm:w-5 sm:h-5" />
            )}
          </button>
        </div>
      </div>
    </form>
  );
}
