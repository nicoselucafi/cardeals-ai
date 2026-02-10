"use client";

import { useState, useEffect, useRef, FormEvent } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Offer } from "@/lib/types";
import OfferCard from "@/components/OfferCard";
import {
  Bot,
  X,
  Send,
  Loader2,
  Lock,
  AlertCircle,
  Maximize2,
  Minimize2,
} from "lucide-react";

const exampleQueries = [
  "Cheapest Toyota lease",
  "RAV4 under $350/mo",
  "Honda Civic deals",
  "Best deals under $400/mo",
];

interface Message {
  role: "user" | "assistant";
  content: string;
  offers?: Offer[];
}

export default function FloatingChat() {
  const pathname = usePathname();
  const { user, session, loading: authLoading } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [remainingPrompts, setRemainingPrompts] = useState<number | null>(null);
  const [dailyLimit, setDailyLimit] = useState<number | null>(null);
  const [limitReached, setLimitReached] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Listen for external open requests (e.g. from homepage search)
  useEffect(() => {
    const handler = (e: Event) => {
      const query = (e as CustomEvent).detail?.query;
      setIsOpen(true);
      if (query) {
        // Small delay to let panel render before searching
        setTimeout(() => handleSearch(query), 100);
      }
    };
    window.addEventListener("open-floating-chat", handler);
    return () => window.removeEventListener("open-floating-chat", handler);
  }, [session?.access_token]);

  // Hide on /chat page
  if (pathname === "/chat") return null;

  // Fetch usage when panel opens
  useEffect(() => {
    if (isOpen && session?.access_token) {
      fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat/usage`,
        {
          headers: { Authorization: `Bearer ${session.access_token}` },
        }
      )
        .then((res) => res.json())
        .then((data) => {
          if (data.remaining !== undefined) {
            setRemainingPrompts(data.remaining);
            setDailyLimit(data.limit);
            setLimitReached(data.remaining <= 0 && !data.is_premium);
          }
        })
        .catch(() => {});
    }
  }, [isOpen, session?.access_token]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSearch = async (query: string) => {
    if (limitReached || isLoading) return;

    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");
    setIsLoading(true);

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (session?.access_token) {
        headers["Authorization"] = `Bearer ${session.access_token}`;
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat`,
        {
          method: "POST",
          headers,
          body: JSON.stringify({ message: query }),
        }
      );

      if (!response.ok) {
        if (response.status === 429) {
          const errorData = await response.json().catch(() => null);
          if (errorData?.detail === "Daily chat limit reached") {
            setRemainingPrompts(0);
            setLimitReached(true);
            throw new Error("daily_limit_reached");
          }
          throw new Error("rate_limited");
        } else if (response.status === 401) {
          throw new Error("auth_required");
        }
        throw new Error("request_failed");
      }

      const data = await response.json();

      if (data.remaining_prompts !== null && data.remaining_prompts !== undefined) {
        setRemainingPrompts(data.remaining_prompts);
        setDailyLimit(data.daily_limit);
        if (data.remaining_prompts <= 0 && !data.is_premium) {
          setLimitReached(true);
        }
      }

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response, offers: data.offers },
      ]);
    } catch (error) {
      let errorMessage = "Sorry, something went wrong. Please try again.";
      if (error instanceof Error) {
        switch (error.message) {
          case "daily_limit_reached":
            errorMessage = "You've used all 5 free AI searches for today. Browse the Deals page for unlimited access!";
            break;
          case "auth_required":
            errorMessage = "Please sign in to use the AI chat.";
            break;
          case "rate_limited":
            errorMessage = "Too many requests. Please wait a moment.";
            break;
        }
      }
      setMessages((prev) => [...prev, { role: "assistant", content: errorMessage }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      handleSearch(input.trim());
    }
  };

  const usageColor =
    remainingPrompts === null
      ? "text-gray-500"
      : remainingPrompts >= 3
        ? "text-green-400"
        : remainingPrompts >= 1
          ? "text-yellow-400"
          : "text-red-400";

  return (
    <>
      {/* Floating button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-[60] w-14 h-14 rounded-full bg-accent hover:bg-accent-dim text-background flex items-center justify-center shadow-glow hover:shadow-glow-sm transition-all duration-200"
          aria-label="Open AI chat"
        >
          <Bot className="w-7 h-7" />
        </button>
      )}

      {/* Chat panel */}
      {isOpen && (
        <div className={`fixed bottom-6 right-6 z-[60] h-[650px] max-sm:inset-x-4 max-sm:bottom-4 max-sm:top-20 max-sm:w-auto max-sm:h-auto bg-background-card border border-border rounded-2xl shadow-card flex flex-col overflow-hidden animate-slide-up-fade transition-all duration-300 ease-in-out ${isExpanded ? "w-[900px]" : "w-[500px]"}`}>
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-background-secondary/50">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center border border-accent/30">
                <Bot className="w-4 h-4 text-accent" />
              </div>
              <span className="font-semibold text-white text-sm">AI Deal Search</span>
            </div>
            <div className="flex items-center gap-3">
              {remainingPrompts !== null && dailyLimit !== null && dailyLimit > 0 && (
                <span className={`text-xs ${usageColor}`}>
                  {remainingPrompts}/{dailyLimit}
                </span>
              )}
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1 text-gray-400 hover:text-white transition-colors max-sm:hidden"
                aria-label={isExpanded ? "Minimize chat" : "Maximize chat"}
              >
                {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 text-gray-400 hover:text-white transition-colors"
                aria-label="Close chat"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Auth gate */}
            {!authLoading && !user ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <div className="w-14 h-14 rounded-full bg-accent/20 flex items-center justify-center mb-4 border border-accent/30">
                  <Lock className="w-7 h-7 text-accent" />
                </div>
                <p className="text-white font-semibold mb-2">Sign in to search</p>
                <p className="text-gray-400 text-sm mb-4">
                  Create a free account to use the AI search.
                </p>
                <div className="flex gap-2">
                  <Link
                    href="/signup"
                    className="px-4 py-2 bg-accent text-background font-medium rounded-lg text-sm hover:bg-accent-dim transition-colors"
                  >
                    Sign up
                  </Link>
                  <Link
                    href="/login"
                    className="px-4 py-2 border border-border text-white font-medium rounded-lg text-sm hover:border-accent/50 transition-colors"
                  >
                    Sign in
                  </Link>
                </div>
              </div>
            ) : messages.length === 0 && !isLoading ? (
              /* Empty state with example queries */
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Bot className="w-10 h-10 text-accent/40 mb-3" />
                <p className="text-gray-400 text-sm mb-4">
                  Ask me about car deals in LA
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {exampleQueries.map((q) => (
                    <button
                      key={q}
                      onClick={() => handleSearch(q)}
                      className="px-3 py-1.5 rounded-full border border-border text-xs text-gray-400 hover:text-accent hover:border-accent/50 transition-all"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              /* Messages */
              <>
                {messages.map((msg, i) => (
                  <div key={i} className="space-y-2">
                    {/* Message bubble */}
                    <div className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                      {msg.role === "assistant" && (
                        <div className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0 border border-accent/30 mt-1">
                          <Bot className="w-3 h-3 text-accent" />
                        </div>
                      )}
                      <div
                        className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                          msg.role === "user"
                            ? "bg-accent text-background"
                            : "bg-background-secondary border border-border text-white"
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    </div>

                    {/* Offer cards */}
                    {msg.offers && msg.offers.length > 0 && (
                      <div className={`mt-2 ${isExpanded ? "grid grid-cols-2 gap-3" : "space-y-3"}`}>
                        {msg.offers.map((offer) => (
                          <OfferCard key={offer.id} offer={offer} />
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {/* Loading */}
                {isLoading && (
                  <div className="flex gap-2">
                    <div className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0 border border-accent/30">
                      <Bot className="w-3 h-3 text-accent" />
                    </div>
                    <div className="bg-background-secondary border border-border rounded-xl px-3 py-2">
                      <div className="flex items-center gap-2 text-gray-400 text-sm">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span>Searching...</span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Footer */}
          {!authLoading && user && (
            <div className="border-t border-border p-3">
              {limitReached ? (
                <div className="text-center">
                  <p className="text-xs text-red-400 mb-2 flex items-center justify-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    Daily limit reached
                  </p>
                  <Link
                    href="/deals"
                    className="text-xs text-accent hover:underline"
                  >
                    Browse all deals (unlimited)
                  </Link>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask about car deals..."
                    disabled={isLoading}
                    className="flex-1 px-3 py-2 rounded-lg bg-background-secondary border border-border text-white text-sm placeholder-gray-500 focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={!input.trim() || isLoading}
                    className="p-2 rounded-lg bg-accent text-background hover:bg-accent-dim disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </button>
                </form>
              )}
            </div>
          )}
        </div>
      )}
    </>
  );
}
