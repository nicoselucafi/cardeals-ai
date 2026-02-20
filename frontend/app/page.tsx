"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Offer } from "@/lib/types";
import ChatInput from "@/components/ChatInput";
import OfferCard from "@/components/OfferCard";
import OfferCardSkeleton from "@/components/OfferCardSkeleton";
import { Sparkles, Search, Link as LinkIcon, Bot, ArrowRight, TrendingUp } from "lucide-react";

const exampleQueries = [
  "Cheapest Toyota lease",
  "RAV4 under $350/month",
  "Honda Civic deals",
  "Best deals under $300/mo",
];

export default function Home() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [featuredOffers, setFeaturedOffers] = useState<Offer[]>([]);
  const [loadingOffers, setLoadingOffers] = useState(true);

  const handleSearch = (query: string) => {
    router.push(`/chat?q=${encodeURIComponent(query)}`);
  };

  // Fetch featured offers for logged-in users
  useEffect(() => {
    if (user) {
      fetchFeaturedOffers();
    }
  }, [user]);

  const fetchFeaturedOffers = async () => {
    setLoadingOffers(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/offers/search?sort_by=confidence_score&limit=3`
      );
      if (response.ok) {
        const data = await response.json();
        setFeaturedOffers(data.offers || []);
      }
    } catch (err) {
      console.error("Failed to fetch featured offers:", err);
    } finally {
      setLoadingOffers(false);
    }
  };

  // Logged-in user dashboard
  if (!authLoading && user) {
    return (
      <div className="min-h-screen px-3 sm:px-4 py-6 sm:py-8">
        <div className="max-w-6xl mx-auto">
          {/* Welcome Header */}
          <div className="mb-6 sm:mb-8">
            <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">
              Welcome back{user.user_metadata?.full_name ? `, ${user.user_metadata.full_name}` : user.email ? `, ${user.email.split("@")[0]}` : ""}
            </h1>
            <p className="text-sm sm:text-base text-gray-400">Find your next great car deal</p>
          </div>

          {/* Quick Search */}
          <div className="bg-background-card border border-border rounded-xl p-4 sm:p-6 mb-6 sm:mb-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-accent/20 flex items-center justify-center border border-accent/30">
                <Bot className="w-4 h-4 sm:w-5 sm:h-5 text-accent" />
              </div>
              <div>
                <h2 className="text-base sm:text-lg font-semibold text-white">AI Search</h2>
                <p className="text-xs sm:text-sm text-gray-400">Ask anything about car deals</p>
              </div>
            </div>
            <ChatInput
              onSubmit={handleSearch}
              placeholder="Try: 'Best RAV4 lease under $350/month'"
            />
            <div className="flex flex-wrap gap-1.5 sm:gap-2 mt-3 sm:mt-4">
              {exampleQueries.map((query) => (
                <button
                  key={query}
                  onClick={() => handleSearch(query)}
                  className="px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-full border border-border text-[11px] sm:text-xs text-gray-400 hover:text-accent hover:border-accent/50 transition-all"
                >
                  {query}
                </button>
              ))}
            </div>
          </div>

          {/* Featured Deals */}
          <div className="mb-6 sm:mb-8">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-accent" />
                <h2 className="text-lg sm:text-xl font-semibold text-white">Top Deals</h2>
              </div>
              <Link
                href="/deals"
                className="text-xs sm:text-sm text-accent hover:underline flex items-center gap-1"
              >
                View all <ArrowRight className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
              </Link>
            </div>

            {loadingOffers ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                <OfferCardSkeleton />
                <OfferCardSkeleton />
                <OfferCardSkeleton />
              </div>
            ) : featuredOffers.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {featuredOffers.map((offer) => (
                  <OfferCard key={offer.id} offer={offer} />
                ))}
              </div>
            ) : (
              <div className="bg-background-card border border-border rounded-xl p-6 sm:p-8 text-center">
                <p className="text-gray-400 text-sm sm:text-base">No deals available right now. Check back soon!</p>
              </div>
            )}
          </div>

          {/* Coverage Info */}
          <div className="text-center text-gray-500 text-xs sm:text-sm">
            Currently tracking Toyota and Honda dealers in Los Angeles
          </div>
        </div>
      </div>
    );
  }

  // Landing page for logged-out users
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="flex flex-col items-center justify-center px-4 pt-12 sm:pt-20 pb-8">
        {/* Glowing orb background effect */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-64 sm:w-96 h-64 sm:h-96 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

        <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-center mb-3 sm:mb-4 relative">
          <span className="text-white">Find Real </span>
          <span className="text-accent glow-text">Car Deals</span>
        </h1>

        <p className="text-gray-400 text-center max-w-xl mb-6 sm:mb-8 text-base sm:text-lg">
          Search current Toyota and Honda offers in Los Angeles.
          <br />
          Every deal links to its source.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-8 sm:mb-12 w-full sm:w-auto px-4 sm:px-0">
          <Link
            href="/signup"
            className="px-8 py-3 bg-accent hover:bg-accent/90 text-background font-semibold rounded-lg transition-colors text-center"
          >
            Get Started Free
          </Link>
          <Link
            href="/login"
            className="px-8 py-3 border border-border hover:border-accent/50 text-white font-medium rounded-lg transition-colors text-center"
          >
            Sign In
          </Link>
        </div>

        {/* Example Queries Preview */}
        <div className="flex flex-wrap justify-center gap-1.5 sm:gap-2 mb-8 sm:mb-12">
          {exampleQueries.map((query) => (
            <span
              key={query}
              className="px-3 sm:px-4 py-1.5 sm:py-2 rounded-full border border-border text-xs sm:text-sm text-gray-500"
            >
              &ldquo;{query}&rdquo;
            </span>
          ))}
        </div>

        {/* How it works */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-8 max-w-4xl w-full mt-4 sm:mt-8">
          <div className="text-center p-4 sm:p-6">
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-3 sm:mb-4 border border-accent/30">
              <Search className="w-5 h-5 sm:w-6 sm:h-6 text-accent" />
            </div>
            <h3 className="font-semibold mb-1 sm:mb-2 text-sm sm:text-base">Ask Naturally</h3>
            <p className="text-gray-400 text-xs sm:text-sm">
              Type what you're looking for in plain English
            </p>
          </div>

          <div className="text-center p-4 sm:p-6">
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-3 sm:mb-4 border border-accent/30">
              <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 text-accent" />
            </div>
            <h3 className="font-semibold mb-1 sm:mb-2 text-sm sm:text-base">AI Finds Deals</h3>
            <p className="text-gray-400 text-xs sm:text-sm">
              Our AI searches real offers from LA dealers
            </p>
          </div>

          <div className="text-center p-4 sm:p-6">
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-3 sm:mb-4 border border-accent/30">
              <LinkIcon className="w-5 h-5 sm:w-6 sm:h-6 text-accent" />
            </div>
            <h3 className="font-semibold mb-1 sm:mb-2 text-sm sm:text-base">Verify Source</h3>
            <p className="text-gray-400 text-xs sm:text-sm">
              Every deal links directly to the dealer's website
            </p>
          </div>
        </div>

        {/* Footer note */}
        <p className="text-gray-500 text-xs sm:text-sm mt-8 sm:mt-12">
          Currently tracking Toyota and Honda dealers in Los Angeles
        </p>
      </div>
    </div>
  );
}
