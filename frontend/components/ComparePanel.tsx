"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import ReactMarkdown from "react-markdown";
import { Offer } from "@/lib/types";
import { formatCurrency, getConfidencePercent } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
import {
  X,
  Send,
  Loader2,
  Bot,
  Trash2,
} from "lucide-react";

interface ComparePanelProps {
  selectedOffers: Offer[];
  onClose: () => void;
  onRemoveOffer: (id: string) => void;
}

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface DynamicRow {
  label: string;
  values: Record<string, string>;
  best: string | null;
}

function getBestValue(offers: Offer[], field: "monthly_payment" | "down_payment" | "confidence_score"): string | null {
  const values = offers
    .map((o) => ({ id: o.id, val: o[field] ? parseFloat(o[field] as string) : null }))
    .filter((v) => v.val !== null);
  if (values.length === 0) return null;
  if (field === "confidence_score") {
    return values.reduce((best, v) => (v.val! > best.val! ? v : best)).id;
  }
  return values.reduce((best, v) => (v.val! < best.val! ? v : best)).id;
}

function buildCompareContext(offers: Offer[]): string {
  return offers
    .map(
      (o, i) =>
        `Offer ${i + 1} (ID: ${o.id}): ${o.year} ${o.make} ${o.model} ${o.trim || ""} - ` +
        `${o.offer_type} at ${o.dealer_name} (${o.dealer_city || "LA"})` +
        (o.monthly_payment ? `, $${o.monthly_payment}/mo` : "") +
        (o.down_payment ? `, $${o.down_payment} down` : "") +
        (o.term_months ? `, ${o.term_months}mo term` : "") +
        (o.annual_mileage ? `, ${o.annual_mileage.toLocaleString()} mi/yr` : "") +
        (o.apr ? `, ${o.apr}% APR` : "")
    )
    .join("\n");
}

function buildWelcomeMessage(offers: Offer[]): string {
  const names = offers.map((o) => `${o.year} ${o.make} ${o.model}`);
  if (names.length === 2) {
    return `Here's the side-by-side comparison of the **${names[0]}** and **${names[1]}**. Ask me anything — I can add specs like horsepower, fuel economy, or cargo space to the table.`;
  }
  const last = names.pop();
  return `Here's the comparison of the **${names.join("**, **")}**, and **${last}**. Ask me to compare any feature and I'll add it to the table.`;
}

const COMPARE_DATA_REGEX = /\[COMPARE_DATA\]([\s\S]*?)\[\/COMPARE_DATA\]/g;

function parseCompareData(text: string): { cleanText: string; rows: DynamicRow[] } {
  const rows: DynamicRow[] = [];
  const cleanText = text.replace(COMPARE_DATA_REGEX, (_, json) => {
    try {
      const parsed = JSON.parse(json.trim());
      // Support both single object and array
      const items = Array.isArray(parsed) ? parsed : [parsed];
      for (const item of items) {
        if (item.label && item.values && typeof item.values === "object") {
          rows.push({
            label: item.label,
            values: item.values,
            best: item.best || null,
          });
        }
      }
    } catch {
      // If JSON parse fails, just strip the block
    }
    return "";
  }).trim();
  return { cleanText, rows };
}

function buildSystemInstruction(offers: Offer[]): string {
  const idList = offers.map((o) => `"${o.id}"`).join(", ");
  return (
    `\n\nIMPORTANT: When the user asks to compare a feature or spec (horsepower, fuel economy, cargo space, safety rating, etc.), ` +
    `include the comparison data in this exact format on its own line so it can be added to the comparison table:\n` +
    `[COMPARE_DATA]{"label":"Feature Name","values":{${offers.map((o) => `"${o.id}":"value"`).join(",")}},"best":"id_of_best_or_null"}[/COMPARE_DATA]\n` +
    `The offer IDs are: ${idList}. Use these exact IDs as keys in "values". ` +
    `Set "best" to the offer ID with the objectively better value, or null if subjective. ` +
    `You can include multiple [COMPARE_DATA] blocks if comparing multiple features. ` +
    `Also include a brief text explanation alongside the data.`
  );
}

export default function ComparePanel({ selectedOffers, onClose, onRemoveOffer }: ComparePanelProps) {
  const { session } = useAuth();
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<Message[]>(() => [
    { role: "assistant", content: buildWelcomeMessage(selectedOffers) },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [dynamicRows, setDynamicRows] = useState<DynamicRow[]>([]);

  const bestPayment = getBestValue(selectedOffers, "monthly_payment");
  const bestDown = getBestValue(selectedOffers, "down_payment");
  const bestScore = getBestValue(selectedOffers, "confidence_score");

  // Scroll only the chat container, not the whole page
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const askComparison = async (question: string) => {
    setIsLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: question }]);

    try {
      const context = buildCompareContext(selectedOffers);
      const instruction = buildSystemInstruction(selectedOffers);
      const fullMessage = `I'm comparing these car deals:\n${context}${instruction}\n\nUser question: ${question}`;

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
          body: JSON.stringify({ message: fullMessage, source: "compare" }),
        }
      );

      if (!response.ok) throw new Error("Failed to get comparison");

      const data = await response.json();
      const { cleanText, rows } = parseCompareData(data.response);

      // Add any new comparison rows to the table (avoid duplicates by label)
      if (rows.length > 0) {
        setDynamicRows((prev) => {
          const existing = new Set(prev.map((r) => r.label.toLowerCase()));
          const newRows = rows.filter((r) => !existing.has(r.label.toLowerCase()));
          // Also update existing rows if re-asked
          const updated = prev.map((r) => {
            const match = rows.find((nr) => nr.label.toLowerCase() === r.label.toLowerCase());
            return match || r;
          });
          return [...updated, ...newRows];
        });
      }

      setMessages((prev) => [...prev, { role: "assistant", content: cleanText || data.response }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I couldn't analyze these offers right now. Please try again." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      askComparison(input.trim());
      setInput("");
    }
  };

  const staticRows: { label: string; getValue: (o: Offer) => string; bestId: string | null }[] = [
    {
      label: "Payment",
      getValue: (o) => (o.monthly_payment ? `${formatCurrency(o.monthly_payment)}/mo` : "N/A"),
      bestId: bestPayment,
    },
    {
      label: "Down Payment",
      getValue: (o) => (o.down_payment ? formatCurrency(o.down_payment) : "N/A"),
      bestId: bestDown,
    },
    {
      label: "Term",
      getValue: (o) => (o.term_months ? `${o.term_months} months` : "N/A"),
      bestId: null,
    },
    {
      label: "Mileage",
      getValue: (o) => (o.annual_mileage ? `${o.annual_mileage.toLocaleString()} mi/yr` : "N/A"),
      bestId: null,
    },
    {
      label: "Dealer",
      getValue: (o) => `${o.dealer_name}${o.dealer_city ? ` \u00b7 ${o.dealer_city}` : ""}`,
      bestId: null,
    },
    {
      label: "Deal Score",
      getValue: (o) => `${getConfidencePercent(o.confidence_score)}%`,
      bestId: bestScore,
    },
  ];

  return (
    <div className="bg-background-card border border-border rounded-xl shadow-lg animate-slide-down mx-2 sm:mx-4 lg:mx-auto lg:max-w-7xl mt-2">
      {/* Header */}
      <div className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 border-b border-border">
        <h2 className="text-base sm:text-lg font-bold text-white">
          Compare {selectedOffers.length} Offers
        </h2>
        <button
          onClick={onClose}
          className="p-2 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-white/5"
          aria-label="Close comparison"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Main content: table left + chat right */}
      <div className="flex flex-col lg:flex-row">
        {/* Comparison table */}
        <div className="flex-1 lg:border-r lg:border-border px-3 sm:px-6 py-4 overflow-x-auto">
          <table className="w-full min-w-0">
            <thead>
              <tr>
                <th className="text-left text-xs text-gray-500 font-medium pb-3 pr-2 sm:pr-4 w-20 sm:w-28 sticky left-0 bg-background-card z-10"></th>
                {selectedOffers.map((offer) => (
                  <th key={offer.id} className="text-left pb-3 px-2 sm:px-3 min-w-[120px] sm:min-w-[150px]">
                    <div className="flex items-start justify-between gap-1 sm:gap-2">
                      <div>
                        <p className="text-xs sm:text-sm font-semibold text-white">
                          {offer.year} {offer.model}
                        </p>
                        <p className="text-[10px] sm:text-xs text-gray-400">
                          {offer.make} {offer.trim || ""}
                        </p>
                      </div>
                      <button
                        onClick={() => onRemoveOffer(offer.id)}
                        className="p-1 text-gray-500 hover:text-red-400 transition-colors flex-shrink-0"
                        aria-label={`Remove ${offer.model} from comparison`}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Static rows from offer data */}
              {staticRows.map((row) => (
                <tr key={row.label} className="border-t border-border/50">
                  <td className="text-[10px] sm:text-xs text-gray-500 font-medium py-2 sm:py-2.5 pr-2 sm:pr-4 sticky left-0 bg-background-card z-10">{row.label}</td>
                  {selectedOffers.map((offer) => (
                    <td
                      key={offer.id}
                      className={`text-xs sm:text-sm py-2 sm:py-2.5 px-2 sm:px-3 ${
                        row.bestId === offer.id ? "text-green-400 font-semibold" : "text-gray-300"
                      }`}
                    >
                      {row.getValue(offer)}
                    </td>
                  ))}
                </tr>
              ))}

              {/* Dynamic rows added by AI */}
              {dynamicRows.map((row) => (
                <tr key={row.label} className="border-t border-accent/20 bg-accent/5">
                  <td className="text-[10px] sm:text-xs text-accent font-medium py-2 sm:py-2.5 pr-2 sm:pr-4 sticky left-0 bg-accent/5 z-10">{row.label}</td>
                  {selectedOffers.map((offer) => (
                    <td
                      key={offer.id}
                      className={`text-xs sm:text-sm py-2 sm:py-2.5 px-2 sm:px-3 ${
                        row.best === offer.id ? "text-green-400 font-semibold" : "text-gray-300"
                      }`}
                    >
                      {row.values[offer.id] || "N/A"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* AI Chat — right side on desktop, below on mobile */}
        <div className="lg:w-[380px] flex flex-col border-t lg:border-t-0 border-border min-h-[280px] sm:min-h-[320px]">
          {/* Chat header */}
          <div className="flex items-center gap-2 px-4 py-2.5 sm:py-3 border-b border-border/50">
            <div className="w-5 h-5 rounded-full bg-accent/20 flex items-center justify-center border border-accent/30">
              <Bot className="w-3 h-3 text-accent" />
            </div>
            <span className="text-sm font-medium text-white">AI Analysis</span>
          </div>

          {/* Messages */}
          <div ref={chatContainerRef} className="flex-1 max-h-[200px] sm:max-h-[260px] overflow-y-auto px-3 sm:px-4 py-3 space-y-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                {msg.role === "assistant" && (
                  <div className="w-5 h-5 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0 border border-accent/30 mt-0.5">
                    <Bot className="w-3 h-3 text-accent" />
                  </div>
                )}
                <div
                  className={`max-w-[90%] rounded-lg px-3 py-2 text-xs sm:text-sm ${
                    msg.role === "user"
                      ? "bg-accent text-background"
                      : "bg-background-secondary border border-border text-white"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <div className="prose prose-invert prose-sm max-w-none [&>p]:my-1 [&>ul]:my-1 [&>ol]:my-1">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p>{msg.content}</p>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-2">
                <div className="w-5 h-5 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0 border border-accent/30">
                  <Bot className="w-3 h-3 text-accent" />
                </div>
                <div className="bg-background-secondary border border-border rounded-lg px-3 py-2">
                  <div className="flex items-center gap-2 text-gray-400 text-xs sm:text-sm">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span>Analyzing...</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Chat input */}
          <div className="px-3 sm:px-4 py-2.5 sm:py-3 border-t border-border/50 mt-auto">
            <form onSubmit={handleSubmit} className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Compare horsepower, MPG..."
                disabled={isLoading}
                className="flex-1 px-3 py-2 rounded-lg bg-background-secondary border border-border text-white text-xs sm:text-sm placeholder-gray-500 focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="p-2 rounded-lg bg-accent text-background hover:bg-accent-dim disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-shrink-0"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
