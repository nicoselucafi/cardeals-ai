"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import ChatInput from "@/components/ChatInput";
import { useAuth } from "@/context/AuthContext";
import { Offer } from "@/lib/types";
import OfferCard from "@/components/OfferCard";
import OfferCardSkeleton from "@/components/OfferCardSkeleton";
import { Sparkles, Search, Link as LinkIcon, Bot, ArrowRight, TrendingUp, Car } from "lucide-react";

const exampleQueries = [
  "Cheapest Toyota lease",
  "RAV4 under $350/month",
  "Honda Civic deals",
  "Tesla Model 3 offers",
];

export default function Home() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [featuredOffers, setFeaturedOffers] = useState<Offer[]>([]);
  const [loadingOffers, setLoadingOffers] = useState(true);

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

  const handleSearch = (query: string) => {
    // Redirect to chat page with query
    router.push(`/chat?q=${encodeURIComponent(query)}`);
  };

  // Logged-in user dashboard
  if (!authLoading && user) {
    return (
      <div className="min-h-screen px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Welcome Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              Welcome back{user.email ? `, ${user.email.split("@")[0]}` : ""}
            </h1>
            <p className="text-gray-400">Find your next great car deal</p>
          </div>

          {/* Quick Search */}
          <div className="bg-background-card border border-border rounded-xl p-6 mb-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center border border-accent/30">
                <Bot className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">AI Search</h2>
                <p className="text-sm text-gray-400">Ask anything about car deals</p>
              </div>
            </div>
            <ChatInput
              onSubmit={handleSearch}
              placeholder="Try: 'Best RAV4 lease under $350/month'"
            />
            <div className="flex flex-wrap gap-2 mt-4">
              {exampleQueries.map((query) => (
                <button
                  key={query}
                  onClick={() => handleSearch(query)}
                  className="px-3 py-1.5 rounded-full border border-border text-xs text-gray-400 hover:text-accent hover:border-accent/50 transition-all"
                >
                  {query}
                </button>
              ))}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid md:grid-cols-2 gap-4 mb-8">
            <Link
              href="/chat"
              className="bg-background-card border border-border rounded-xl p-6 hover:border-accent/50 transition-colors group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center border border-accent/30 group-hover:border-accent transition-colors">
                    <Bot className="w-6 h-6 text-accent" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">AI Chat</h3>
                    <p className="text-sm text-gray-400">Search with natural language</p>
                  </div>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-500 group-hover:text-accent transition-colors" />
              </div>
            </Link>

            <Link
              href="/deals"
              className="bg-background-card border border-border rounded-xl p-6 hover:border-accent/50 transition-colors group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center border border-accent/30 group-hover:border-accent transition-colors">
                    <Car className="w-6 h-6 text-accent" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">Browse Deals</h3>
                    <p className="text-sm text-gray-400">Filter and sort all offers</p>
                  </div>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-500 group-hover:text-accent transition-colors" />
              </div>
            </Link>
          </div>

          {/* Featured Deals */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-accent" />
                <h2 className="text-xl font-semibold text-white">Top Deals</h2>
              </div>
              <Link
                href="/deals"
                className="text-sm text-accent hover:underline flex items-center gap-1"
              >
                View all <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {loadingOffers ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <OfferCardSkeleton />
                <OfferCardSkeleton />
                <OfferCardSkeleton />
              </div>
            ) : featuredOffers.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {featuredOffers.map((offer) => (
                  <OfferCard key={offer.id} offer={offer} />
                ))}
              </div>
            ) : (
              <div className="bg-background-card border border-border rounded-xl p-8 text-center">
                <p className="text-gray-400">No deals available right now. Check back soon!</p>
              </div>
            )}
          </div>

          {/* Coverage Info */}
          <div className="text-center text-gray-500 text-sm">
            Currently tracking Toyota, Honda, and Tesla dealers in Los Angeles
          </div>
        </div>
      </div>
    );
  }

  // Landing page for logged-out users
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="flex flex-col items-center justify-center px-4 pt-20 pb-8">
        {/* Glowing orb background effect */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

        <h1 className="text-4xl md:text-5xl font-bold text-center mb-4 relative">
          <span className="text-white">Find Real </span>
          <span className="text-accent glow-text">Car Deals</span>
        </h1>

        <p className="text-gray-400 text-center max-w-xl mb-8 text-lg">
          Search current Toyota, Honda, and Tesla offers in Los Angeles.
          <br />
          Every deal links to its source.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mb-12">
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
        <div className="flex flex-wrap justify-center gap-2 mb-12">
          {exampleQueries.map((query) => (
            <span
              key={query}
              className="px-4 py-2 rounded-full border border-border text-sm text-gray-500"
            >
              "{query}"
            </span>
          ))}
        </div>

        {/* How it works */}
        <div className="grid md:grid-cols-3 gap-8 max-w-4xl w-full mt-8">
          <div className="text-center p-6">
            <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-4 border border-accent/30">
              <Search className="w-6 h-6 text-accent" />
            </div>
            <h3 className="font-semibold mb-2">Ask Naturally</h3>
            <p className="text-gray-400 text-sm">
              Type what you're looking for in plain English
            </p>
          </div>

          <div className="text-center p-6">
            <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-4 border border-accent/30">
              <Sparkles className="w-6 h-6 text-accent" />
            </div>
            <h3 className="font-semibold mb-2">AI Finds Deals</h3>
            <p className="text-gray-400 text-sm">
              Our AI searches real offers from LA dealers
            </p>
          </div>

          <div className="text-center p-6">
            <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-4 border border-accent/30">
              <LinkIcon className="w-6 h-6 text-accent" />
            </div>
            <h3 className="font-semibold mb-2">Verify Source</h3>
            <p className="text-gray-400 text-sm">
              Every deal links directly to the dealer's website
            </p>
          </div>
        </div>

        {/* Footer note */}
        <p className="text-gray-500 text-sm mt-12">
          Currently tracking Toyota, Honda, and Tesla dealers in Los Angeles
        </p>
      </div>
    </div>
  );
}
