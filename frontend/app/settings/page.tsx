"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { createClient } from "@/lib/supabase/client";
import { Offer } from "@/lib/types";
import OfferCard from "@/components/OfferCard";
import OfferCardSkeleton from "@/components/OfferCardSkeleton";
import { getSavedOffers, clearAllSaved } from "@/lib/savedOffers";
import {
  User,
  Heart,
  Crown,
  Save,
  Trash2,
  Loader2,
  Check,
} from "lucide-react";

export default function SettingsPage() {
  const { user, loading: authLoading, isPremium } = useAuth();
  const router = useRouter();

  // Profile state
  const [fullName, setFullName] = useState("");
  const [savingName, setSavingName] = useState(false);
  const [nameSaved, setNameSaved] = useState(false);

  // Saved offers state
  const [savedOffers, setSavedOffers] = useState<Offer[]>([]);
  const [loadingSaved, setLoadingSaved] = useState(true);

  // Redirect if not logged in
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [authLoading, user, router]);

  // Load profile data
  useEffect(() => {
    if (user) {
      setFullName(user.user_metadata?.full_name || "");
    }
  }, [user]);

  // Load saved offers
  useEffect(() => {
    if (user) {
      fetchSavedOffers();
    }
  }, [user]);

  const fetchSavedOffers = async () => {
    setLoadingSaved(true);
    const ids = getSavedOffers();
    if (ids.length === 0) {
      setSavedOffers([]);
      setLoadingSaved(false);
      return;
    }

    const offers: Offer[] = [];
    for (const id of ids) {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/offers/${id}`
        );
        if (res.ok) {
          const data = await res.json();
          offers.push(data);
        }
      } catch {
        // Skip failed fetches
      }
    }
    setSavedOffers(offers);
    setLoadingSaved(false);
  };

  const handleSaveName = async () => {
    setSavingName(true);
    setNameSaved(false);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.updateUser({
        data: { full_name: fullName },
      });
      if (!error) {
        setNameSaved(true);
        setTimeout(() => setNameSaved(false), 3000);
      }
    } catch {
      // Silently fail
    } finally {
      setSavingName(false);
    }
  };

  const handleClearSaved = () => {
    clearAllSaved();
    setSavedOffers([]);
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-accent animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen px-3 sm:px-4 py-6 sm:py-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-6 sm:mb-8">
          Settings
        </h1>

        {/* ─── Profile Section ─── */}
        <section className="bg-background-card border border-border rounded-xl p-5 sm:p-6 mb-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center border border-accent/30">
              <User className="w-5 h-5 text-accent" />
            </div>
            <h2 className="text-lg font-semibold text-white">Profile</h2>
          </div>

          <div className="space-y-4">
            {/* Email (read-only) */}
            <div>
              <label className="block text-sm text-gray-400 mb-1">Email</label>
              <div className="px-4 py-2.5 rounded-lg bg-background-secondary border border-border text-gray-400 text-sm">
                {user.email}
              </div>
            </div>

            {/* Display Name (editable) */}
            <div>
              <label className="block text-sm text-gray-400 mb-1">
                Display name
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Enter your name"
                  className="flex-1 px-4 py-2.5 rounded-lg bg-background-secondary border border-border text-white text-sm placeholder-gray-500 focus:outline-none focus:border-accent transition-colors"
                />
                <button
                  onClick={handleSaveName}
                  disabled={savingName}
                  className="px-4 py-2.5 rounded-lg bg-accent hover:bg-accent-dim text-background font-medium text-sm transition-colors disabled:opacity-50 flex items-center gap-1.5"
                >
                  {savingName ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : nameSaved ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  {nameSaved ? "Saved" : "Save"}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* ─── Saved Listings Section ─── */}
        <section className="bg-background-card border border-border rounded-xl p-5 sm:p-6 mb-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center border border-accent/30">
                <Heart className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">
                  Saved Listings
                </h2>
                <p className="text-xs text-gray-500">
                  {savedOffers.length} deal{savedOffers.length !== 1 ? "s" : ""} saved
                </p>
              </div>
            </div>

            {savedOffers.length > 0 && (
              <button
                onClick={handleClearSaved}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gray-400 hover:text-red-400 border border-border hover:border-red-500/30 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Clear all
              </button>
            )}
          </div>

          {loadingSaved ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <OfferCardSkeleton />
              <OfferCardSkeleton />
            </div>
          ) : savedOffers.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {savedOffers.map((offer) => (
                <OfferCard key={offer.id} offer={offer} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Heart className="w-10 h-10 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400 text-sm mb-1">No saved deals yet</p>
              <p className="text-gray-500 text-xs">
                Tap the heart icon on any deal to save it here
              </p>
            </div>
          )}
        </section>

        {/* ─── Subscription Section ─── */}
        <section className="bg-background-card border border-border rounded-xl p-5 sm:p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center border border-accent/30">
              <Crown className="w-5 h-5 text-accent" />
            </div>
            <h2 className="text-lg font-semibold text-white">Subscription</h2>
          </div>

          {/* Current Plan */}
          <div className="bg-background-secondary border border-border rounded-xl p-5 mb-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-gray-400">Current plan</span>
              {isPremium ? (
                <span className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
                  <Crown className="w-3 h-3" />
                  Pro
                </span>
              ) : (
                <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-accent/10 text-accent border border-accent/30">
                  Free
                </span>
              )}
            </div>

            {isPremium ? (
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-green-400" />
                  Unlimited AI searches
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-green-400" />
                  Unlimited comparisons
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-green-400" />
                  Priority support
                </li>
              </ul>
            ) : (
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-accent" />
                  10 AI searches per day
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-accent" />
                  10 comparisons per day
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-accent" />
                  Unlimited deal browsing
                </li>
              </ul>
            )}
          </div>

          {!isPremium && (
            <button
              disabled
              className="w-full py-3 px-4 bg-accent/20 text-accent font-semibold rounded-xl cursor-not-allowed flex items-center justify-center gap-2 border border-accent/20"
            >
              <Crown className="w-4 h-4" />
              Upgrade to Pro
              <span className="ml-1 px-2 py-0.5 text-[10px] rounded-full bg-accent/20 border border-accent/30">
                Coming Soon
              </span>
            </button>
          )}
        </section>
      </div>
    </div>
  );
}
