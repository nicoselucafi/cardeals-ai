"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Offer } from "@/lib/types";
import { formatCurrency, getConfidencePercent, getRelativeTime } from "@/lib/utils";
import {
  ArrowLeft,
  ExternalLink,
  MapPin,
  Calendar,
  Gauge,
  DollarSign,
  Percent,
  Car,
  AlertCircle,
  Loader2,
} from "lucide-react";

export default function OfferDetailPage() {
  const params = useParams();
  const [offer, setOffer] = useState<Offer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchOffer() {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/offers/${params.id}`
        );

        if (!response.ok) {
          if (response.status === 404) {
            setError("Offer not found");
          } else {
            setError("Failed to load offer");
          }
          return;
        }

        const data = await response.json();
        setOffer(data);
      } catch (err) {
        setError("Failed to connect to server");
      } finally {
        setLoading(false);
      }
    }

    if (params.id) {
      fetchOffer();
    }
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-accent animate-spin" />
      </div>
    );
  }

  if (error || !offer) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4">
        <AlertCircle className="w-16 h-16 text-red-400 mb-4" />
        <h1 className="text-2xl font-bold mb-2">{error || "Offer not found"}</h1>
        <p className="text-gray-400 mb-6">
          This offer may have expired or been removed.
        </p>
        <Link
          href="/"
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-background hover:bg-accent-dim transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Search
        </Link>
      </div>
    );
  }

  const confidencePercent = getConfidencePercent(offer.confidence_score);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Back button */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-gray-400 hover:text-accent transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Search
      </Link>

      <div className="bg-background-card border border-border rounded-2xl overflow-hidden">
        {/* Header with car image placeholder */}
        <div className="relative h-64 bg-gradient-to-br from-background-secondary to-background flex items-center justify-center border-b border-border">
          <div className="absolute inset-0 bg-gradient-to-t from-background-card/80 to-transparent" />
          <Car className="w-32 h-32 text-gray-600" />
          <span className="absolute top-4 left-4 px-3 py-1 text-sm font-medium rounded bg-accent/20 text-accent border border-accent/30 uppercase">
            {offer.offer_type}
          </span>
        </div>

        <div className="p-6 md:p-8">
          {/* Title & Price */}
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                {offer.year} {offer.make} {offer.model}
                {offer.trim && <span className="text-gray-400"> {offer.trim}</span>}
              </h1>
              <p className="text-gray-400 flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                {offer.dealer_name}
                {offer.dealer_city && ` • ${offer.dealer_city}, CA`}
              </p>
            </div>

            <div className="text-right">
              {offer.offer_type === "lease" && offer.monthly_payment ? (
                <>
                  <div className="text-4xl font-bold text-accent">
                    {formatCurrency(offer.monthly_payment)}
                    <span className="text-lg text-gray-400">/mo</span>
                  </div>
                  {offer.down_payment && (
                    <p className="text-gray-500">
                      {formatCurrency(offer.down_payment)} due at signing
                    </p>
                  )}
                </>
              ) : offer.offer_type === "finance" && offer.apr ? (
                <>
                  <div className="text-4xl font-bold text-accent">
                    {offer.apr}%
                    <span className="text-lg text-gray-400"> APR</span>
                  </div>
                  {offer.term_months && (
                    <p className="text-gray-500">up to {offer.term_months} months</p>
                  )}
                </>
              ) : (
                <p className="text-gray-400">Contact dealer for pricing</p>
              )}
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {offer.term_months && (
              <div className="bg-background-secondary border border-border rounded-lg p-4">
                <Calendar className="w-5 h-5 text-accent mb-2" />
                <p className="text-sm text-gray-400">Term</p>
                <p className="text-lg font-semibold">{offer.term_months} months</p>
              </div>
            )}

            {offer.annual_mileage && (
              <div className="bg-background-secondary border border-border rounded-lg p-4">
                <Gauge className="w-5 h-5 text-accent mb-2" />
                <p className="text-sm text-gray-400">Annual Miles</p>
                <p className="text-lg font-semibold">{offer.annual_mileage.toLocaleString()}</p>
              </div>
            )}

            {offer.down_payment && (
              <div className="bg-background-secondary border border-border rounded-lg p-4">
                <DollarSign className="w-5 h-5 text-accent mb-2" />
                <p className="text-sm text-gray-400">Due at Signing</p>
                <p className="text-lg font-semibold">{formatCurrency(offer.down_payment)}</p>
              </div>
            )}

            {offer.msrp && (
              <div className="bg-background-secondary border border-border rounded-lg p-4">
                <Car className="w-5 h-5 text-accent mb-2" />
                <p className="text-sm text-gray-400">MSRP</p>
                <p className="text-lg font-semibold">{formatCurrency(offer.msrp)}</p>
              </div>
            )}

            {offer.apr && offer.offer_type === "lease" && (
              <div className="bg-background-secondary border border-border rounded-lg p-4">
                <Percent className="w-5 h-5 text-accent mb-2" />
                <p className="text-sm text-gray-400">Money Factor</p>
                <p className="text-lg font-semibold">{offer.apr}%</p>
              </div>
            )}
          </div>

          {/* AI Score */}
          <div className="flex items-center gap-4 mb-6 p-4 bg-background-secondary border border-border rounded-lg">
            <div className="flex-1">
              <p className="text-sm text-gray-400 mb-1">AI Deal Score</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 bg-background rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent transition-all duration-500"
                    style={{ width: `${confidencePercent}%` }}
                  />
                </div>
                <span className="text-accent font-semibold">{confidencePercent}%</span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-400">Updated</p>
              <p className="text-sm">{getRelativeTime(offer.updated_at)}</p>
            </div>
          </div>

          {/* CTA */}
          {offer.source_url && (
            <a
              href={offer.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 w-full py-4 rounded-xl bg-accent text-background hover:bg-accent-dim transition-colors font-semibold text-lg"
            >
              View at {offer.dealer_name}
              <ExternalLink className="w-5 h-5" />
            </a>
          )}

          {/* Disclaimer */}
          <p className="text-xs text-gray-500 mt-6 text-center">
            Prices and availability subject to change. Contact dealer for current offers.
            This data was automatically extracted and may contain errors.
          </p>
        </div>
      </div>
    </div>
  );
}
