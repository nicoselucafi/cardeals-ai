"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import OfferCard from "@/components/OfferCard";
import OfferCardSkeleton from "@/components/OfferCardSkeleton";
import { Offer } from "@/lib/types";
import { Filter, SlidersHorizontal, Lock } from "lucide-react";

const MAKES = ["All Makes", "Toyota", "Honda", "Tesla"];
const MODELS: Record<string, string[]> = {
  "All Makes": ["All Models"],
  "Toyota": ["All Models", "RAV4", "Camry", "Corolla", "Highlander", "Tacoma", "4Runner", "Prius", "Sienna", "Tundra", "Corolla Cross", "Venza", "bZ4X"],
  "Honda": ["All Models", "Accord", "Civic", "CR-V", "HR-V", "Pilot", "Passport", "Odyssey", "Ridgeline", "Prologue"],
  "Tesla": ["All Models", "Model 3", "Model Y", "Model S", "Model X", "Cybertruck"],
};
const OFFER_TYPES = ["All Types", "lease", "finance"];
const SORT_OPTIONS = [
  { value: "monthly_payment", label: "Lowest Payment" },
  { value: "down_payment", label: "Lowest Down Payment" },
  { value: "confidence_score", label: "Best Deal Score" },
];

export default function DealsPage() {
  const { user, loading: authLoading } = useAuth();
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedMake, setSelectedMake] = useState("All Makes");
  const [selectedModel, setSelectedModel] = useState("All Models");
  const [selectedType, setSelectedType] = useState("All Types");
  const [sortBy, setSortBy] = useState("monthly_payment");
  const [showFilters, setShowFilters] = useState(false);

  // Reset model when make changes
  useEffect(() => {
    setSelectedModel("All Models");
  }, [selectedMake]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }

    fetchOffers();
  }, [user, authLoading, selectedMake, selectedModel, selectedType, sortBy]);

  const fetchOffers = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (selectedMake !== "All Makes") params.append("make", selectedMake);
      if (selectedModel !== "All Models") params.append("model", selectedModel);
      if (selectedType !== "All Types") params.append("offer_type", selectedType);
      params.append("sort_by", sortBy);
      params.append("limit", "50");

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/offers/search?${params}`
      );

      if (!response.ok) throw new Error("Failed to fetch offers");

      const data = await response.json();
      setOffers(data.offers);
    } catch (err) {
      setError("Failed to load deals. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Show auth prompt if not logged in
  if (!authLoading && !user) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-6 border border-accent/30">
            <Lock className="w-10 h-10 text-accent" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-4">Sign in to browse deals</h1>
          <p className="text-gray-400 mb-8">
            Create a free account to browse all current lease and finance offers.
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
    <div className="min-h-screen px-4 py-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Current Deals</h1>
          <p className="text-gray-400">
            Browse all active lease and finance offers from dealers in LA
          </p>
        </div>

        {/* Filters Bar */}
        <div className="bg-background-card border border-border rounded-xl p-4 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            {/* Make Filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">Make:</label>
              <select
                value={selectedMake}
                onChange={(e) => setSelectedMake(e.target.value)}
                className="bg-background-secondary border border-border rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent"
              >
                {MAKES.map((make) => (
                  <option key={make} value={make}>
                    {make}
                  </option>
                ))}
              </select>
            </div>

            {/* Model Filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">Model:</label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="bg-background-secondary border border-border rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent"
              >
                {(MODELS[selectedMake] || MODELS["All Makes"]).map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>

            {/* Type Filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-400">Type:</label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="bg-background-secondary border border-border rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent"
              >
                {OFFER_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type === "All Types" ? type : type.charAt(0).toUpperCase() + type.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort */}
            <div className="flex items-center gap-2 ml-auto">
              <label className="text-sm text-gray-400">Sort:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-background-secondary border border-border rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent"
              >
                {SORT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Results count */}
        {!loading && !error && (
          <p className="text-sm text-gray-500 mb-4">
            Showing {offers.length} deal{offers.length !== 1 ? "s" : ""}
          </p>
        )}

        {/* Error state */}
        {error && (
          <div className="text-center py-12">
            <p className="text-red-400 mb-4">{error}</p>
            <button
              onClick={fetchOffers}
              className="px-4 py-2 bg-accent text-background rounded-lg font-medium"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <OfferCardSkeleton key={i} />
            ))}
          </div>
        )}

        {/* Offers grid */}
        {!loading && !error && offers.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {offers.map((offer) => (
              <OfferCard key={offer.id} offer={offer} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && offers.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400 mb-2">No deals found matching your filters.</p>
            <button
              onClick={() => {
                setSelectedMake("All Makes");
                setSelectedModel("All Models");
                setSelectedType("All Types");
              }}
              className="text-accent hover:underline"
            >
              Clear filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
