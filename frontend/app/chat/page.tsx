"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import ChatInput from "@/components/ChatInput";
import ChatMessages from "@/components/ChatMessages";
import { useAuth } from "@/context/AuthContext";
import { Offer } from "@/lib/types";
import { Bot, Lock, Sparkles, Loader2, AlertCircle, Crown } from "lucide-react";

const exampleQueries = [
  "Cheapest Toyota lease",
  "RAV4 under $350/month",
  "Honda Civic deals",
  "Best deals under $300/mo",
  "Best deals under $400/mo",
  "CR-V lease specials",
];

function UsageCounter({
  remaining,
  limit,
}: {
  remaining: number | null;
  limit: number | null;
}) {
  if (remaining === null || limit === null || limit <= 0) return null;

  const color =
    remaining >= 3
      ? "text-green-400"
      : remaining >= 1
        ? "text-yellow-400"
        : "text-red-400";

  return (
    <div className={`text-sm ${color} flex items-center gap-1.5`}>
      <div
        className={`w-2 h-2 rounded-full ${
          remaining >= 3
            ? "bg-green-400"
            : remaining >= 1
              ? "bg-yellow-400"
              : "bg-red-400"
        }`}
      />
      {remaining} of {limit} free searches remaining today
    </div>
  );
}

function LimitReachedBanner() {
  return (
    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center max-w-lg mx-auto">
      <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
      <h3 className="text-lg font-semibold text-white mb-2">
        Daily limit reached
      </h3>
      <p className="text-gray-400 mb-4">
        You've used all your free AI searches for today. Your limit resets at
        midnight UTC.
      </p>
      <div className="space-y-3">
        <button
          disabled
          className="w-full py-3 px-4 bg-accent/30 text-accent font-semibold rounded-lg cursor-not-allowed flex items-center justify-center gap-2"
        >
          <Crown className="w-4 h-4" />
          Upgrade to Premium — Coming Soon
        </button>
        <Link
          href="/deals"
          className="block w-full py-3 px-4 border border-border hover:border-accent/50 text-white font-medium rounded-lg transition-colors text-center"
        >
          Browse all deals (unlimited)
        </Link>
      </div>
    </div>
  );
}

function ChatContent() {
  const { user, session, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<
    Array<{
      role: "user" | "assistant";
      content: string;
      offers?: Offer[];
    }>
  >([]);
  const [isLoading, setIsLoading] = useState(false);
  const [remainingPrompts, setRemainingPrompts] = useState<number | null>(null);
  const [dailyLimit, setDailyLimit] = useState<number | null>(null);
  const [limitReached, setLimitReached] = useState(false);
  const initialQueryProcessed = useRef(false);

  // Fetch usage on mount
  useEffect(() => {
    if (session?.access_token) {
      fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat/usage`,
        {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
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
  }, [session?.access_token]);

  const handleSearch = async (query: string) => {
    if (limitReached) return;

    // Add user message
    setMessages((prev) => [...prev, { role: "user", content: query }]);
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
          body: JSON.stringify({ message: query, source: "chat" }),
        }
      );

      if (!response.ok) {
        const status = response.status;
        if (status === 429) {
          const errorData = await response.json().catch(() => null);
          if (errorData?.detail === "Daily chat limit reached") {
            setRemainingPrompts(0);
            setLimitReached(true);
            throw new Error("daily_limit_reached");
          }
          throw new Error("rate_limited");
        } else if (status === 401) {
          throw new Error("auth_required");
        } else if (status === 503) {
          throw new Error("service_unavailable");
        } else if (status >= 500) {
          throw new Error("server_error");
        }
        throw new Error("request_failed");
      }

      const data = await response.json();

      // Update usage counter from response
      if (
        data.remaining_prompts !== null &&
        data.remaining_prompts !== undefined
      ) {
        setRemainingPrompts(data.remaining_prompts);
        setDailyLimit(data.daily_limit);
        if (data.remaining_prompts <= 0 && !data.is_premium) {
          setLimitReached(true);
        }
      }

      // Add assistant message
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          offers: data.offers,
        },
      ]);
    } catch (error) {
      let errorMessage = "Sorry, I encountered an error. Please try again.";

      if (error instanceof TypeError && error.message.includes("fetch")) {
        errorMessage =
          "Unable to connect to the server. Please check your connection and try again.";
      } else if (error instanceof Error) {
        switch (error.message) {
          case "daily_limit_reached":
            errorMessage =
              "You've used all your free AI searches for today. Your limit resets at midnight UTC. In the meantime, you can browse all deals on the Deals page!";
            break;
          case "auth_required":
            errorMessage = "Please sign in to use the AI chat.";
            break;
          case "service_unavailable":
            errorMessage =
              "The service is temporarily unavailable. Please try again in a moment.";
            break;
          case "rate_limited":
            errorMessage =
              "Too many requests. Please wait a moment before trying again.";
            break;
          case "server_error":
            errorMessage =
              "Server error occurred. Our team has been notified.";
            break;
        }
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: errorMessage,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle initial query from URL parameter
  useEffect(() => {
    if (!authLoading && user && !initialQueryProcessed.current && !limitReached) {
      const query = searchParams.get("q");
      if (query) {
        initialQueryProcessed.current = true;
        handleSearch(query);
      }
    }
  }, [authLoading, user, searchParams, limitReached]);

  const handleExampleClick = (query: string) => {
    handleSearch(query);
  };

  // Show auth prompt if not logged in
  if (!authLoading && !user) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-6 border border-accent/30">
            <Lock className="w-10 h-10 text-accent" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-4">
            Sign in to use AI Chat
          </h1>
          <p className="text-gray-400 mb-8">
            Create a free account to search for car deals using our AI
            assistant.
          </p>
          <div className="space-y-3">
            <Link
              href="/signup"
              className="block w-full py-3 px-4 bg-accent hover:bg-accent/90 text-background font-semibold rounded-lg transition-colors text-center"
            >
              Create free account
            </Link>
            <Link
              href="/login"
              className="block w-full py-3 px-4 border border-border hover:border-accent/50 text-white font-medium rounded-lg transition-colors text-center"
            >
              Sign in
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Empty state - show when no messages */}
      {messages.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center px-4 pt-8 sm:pt-16 pb-8">
          {/* AI Bot Icon */}
          <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-accent/20 flex items-center justify-center mb-4 sm:mb-6 border border-accent/30">
            <Bot className="w-8 h-8 sm:w-10 sm:h-10 text-accent" />
          </div>

          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center mb-3 sm:mb-4">
            <span className="text-white">AI-Powered </span>
            <span className="text-accent">Deal Search</span>
          </h1>

          <p className="text-gray-400 text-center max-w-xl mb-4 text-sm sm:text-lg">
            Ask me anything about Toyota and Honda lease and finance
            offers in Los Angeles. I'll find the best matches for you.
          </p>

          {/* Usage counter */}
          <div className="mb-6 sm:mb-8">
            <UsageCounter remaining={remainingPrompts} limit={dailyLimit} />
          </div>

          {/* Limit reached banner */}
          {limitReached ? (
            <div className="w-full max-w-lg mb-8 px-2">
              <LimitReachedBanner />
            </div>
          ) : (
            <>
              {/* Search Input */}
              <div className="w-full max-w-2xl mb-6 sm:mb-8">
                <ChatInput
                  onSubmit={handleSearch}
                  isLoading={isLoading}
                  placeholder="Try: 'Best RAV4 lease under $350/month'"
                />
              </div>

              {/* Example Queries */}
              <div className="flex flex-wrap justify-center gap-1.5 sm:gap-2 mb-8 sm:mb-12">
                {exampleQueries.map((query) => (
                  <button
                    key={query}
                    onClick={() => handleExampleClick(query)}
                    className="px-3 sm:px-4 py-1.5 sm:py-2 rounded-full border border-border text-xs sm:text-sm text-gray-400 hover:text-accent hover:border-accent/50 transition-all"
                  >
                    {query}
                  </button>
                ))}
              </div>
            </>
          )}

          {/* Capabilities */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 max-w-3xl w-full">
            <div className="bg-background-card border border-border rounded-xl p-4 sm:p-5 text-center">
              <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 text-accent mx-auto mb-2 sm:mb-3" />
              <h3 className="font-medium mb-1 sm:mb-2 text-sm sm:text-base">Natural Language</h3>
              <p className="text-gray-400 text-xs sm:text-sm">
                Ask in plain English, no filters needed
              </p>
            </div>
            <div className="bg-background-card border border-border rounded-xl p-4 sm:p-5 text-center">
              <Bot className="w-5 h-5 sm:w-6 sm:h-6 text-accent mx-auto mb-2 sm:mb-3" />
              <h3 className="font-medium mb-1 sm:mb-2 text-sm sm:text-base">Smart Matching</h3>
              <p className="text-gray-400 text-xs sm:text-sm">
                AI finds deals that match your criteria
              </p>
            </div>
            <div className="bg-background-card border border-border rounded-xl p-4 sm:p-5 text-center">
              <svg
                className="w-5 h-5 sm:w-6 sm:h-6 text-accent mx-auto mb-2 sm:mb-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                />
              </svg>
              <h3 className="font-medium mb-1 sm:mb-2 text-sm sm:text-base">Verified Sources</h3>
              <p className="text-gray-400 text-xs sm:text-sm">
                Every deal links to the dealer's site
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Chat Messages - Show when there are messages */}
      {(messages.length > 0 || isLoading) && (
        <div className="max-w-4xl mx-auto px-3 sm:px-4 pt-4 sm:pt-8 pb-36 sm:pb-44">
          <ChatMessages messages={messages} isLoading={isLoading} />

          {/* Limit reached inline */}
          {limitReached && (
            <div className="mt-6">
              <LimitReachedBanner />
            </div>
          )}

          {/* Floating input at bottom */}
          {!limitReached && (
            <div className="fixed bottom-0 left-0 right-0 z-50 p-2.5 sm:p-4 bg-background border-t border-border">
              <div className="max-w-2xl mx-auto">
                <div className="flex flex-col items-center gap-1.5 sm:gap-2">
                  <UsageCounter
                    remaining={remainingPrompts}
                    limit={dailyLimit}
                  />
                  <ChatInput onSubmit={handleSearch} isLoading={isLoading} />
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ChatLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex items-center gap-3 text-gray-400">
        <Loader2 className="w-6 h-6 animate-spin" />
        <span>Loading...</span>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<ChatLoading />}>
      <ChatContent />
    </Suspense>
  );
}
