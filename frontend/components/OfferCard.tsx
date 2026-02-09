"use client";

import { useState } from "react";
import Image from "next/image";
import { Offer } from "@/lib/types";
import { formatCurrency, getConfidencePercent, getRelativeTime } from "@/lib/utils";
import { getCarImageConfig, getVehicleType } from "@/lib/carImages";
import { ExternalLink, Car, Truck, Zap } from "lucide-react";
import Link from "next/link";

interface OfferCardProps {
  offer: Offer;
}

function VehicleIcon({ type, className }: { type: string; className?: string }) {
  switch (type) {
    case "truck":
      return <Truck className={className} />;
    case "electric":
      return <Zap className={className} />;
    default:
      return <Car className={className} />;
  }
}

export default function OfferCard({ offer }: OfferCardProps) {
  const [imageError, setImageError] = useState(false);
  const confidencePercent = getConfidencePercent(offer.confidence_score);
  const imageConfig = getCarImageConfig(offer.make, offer.model);
  const vehicleType = getVehicleType(offer.model);
  const hasRealImage = offer.image_url && !imageError;

  const getConfidenceColor = (percent: number) => {
    if (percent >= 90) return "text-green-400";
    if (percent >= 70) return "text-yellow-400";
    return "text-orange-400";
  };

  return (
    <div className="bg-background-card border border-border rounded-xl overflow-hidden hover:border-accent/50 transition-all duration-300 group hover:shadow-glow-sm">
      {/* Car Image - Real image or Model-specific gradient fallback */}
      <div className={`relative h-44 ${!hasRealImage ? `bg-gradient-to-br ${imageConfig.gradient.from} ${imageConfig.gradient.to}` : 'bg-background-secondary'} flex flex-col items-center justify-center border-b border-border overflow-hidden`}>
        {hasRealImage ? (
          <>
            {/* Real vehicle image */}
            <Image
              src={offer.image_url!}
              alt={`${offer.year} ${offer.make} ${offer.model}`}
              fill
              className="object-contain p-2"
              onError={() => setImageError(true)}
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            />
            {/* Gradient overlay for text readability */}
            <div className="absolute inset-0 bg-gradient-to-t from-background-card/90 via-transparent to-background-card/30" />
          </>
        ) : (
          <>
            {/* Fallback: Decorative background pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute inset-0" style={{
                backgroundImage: `radial-gradient(circle at 2px 2px, currentColor 1px, transparent 0)`,
                backgroundSize: '24px 24px',
              }} />
            </div>

            {/* Large vehicle icon */}
            <VehicleIcon
              type={vehicleType}
              className={`w-16 h-16 ${imageConfig.gradient.accent} opacity-40 mb-2`}
            />

            {/* Model name prominently displayed */}
            <div className="text-center z-10 px-4">
              <p className={`text-2xl font-bold ${imageConfig.gradient.accent} drop-shadow-lg`}>
                {offer.model}
              </p>
              <p className="text-sm text-white/60 font-medium">
                {offer.year} {offer.make}
              </p>
            </div>

            {/* Bottom gradient fade */}
            <div className="absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-background-card to-transparent" />
          </>
        )}

        {/* Offer type badge */}
        <span className="absolute top-3 left-3 px-2 py-1 text-xs font-medium rounded bg-black/40 text-white border border-white/20 uppercase backdrop-blur-sm z-10">
          {offer.offer_type}
        </span>

        {/* Year badge */}
        <span className="absolute top-3 right-3 px-2 py-1 text-xs font-bold rounded bg-white/10 text-white border border-white/20 backdrop-blur-sm z-10">
          {offer.year}
        </span>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Vehicle Title */}
        <h3 className="font-semibold text-white mb-1">
          {offer.year} {offer.make} {offer.model}
          {offer.trim && <span className="text-gray-400"> {offer.trim}</span>}
        </h3>

        {/* Dealer */}
        <p className="text-sm text-gray-400 mb-3">
          {offer.dealer_name}
          {offer.dealer_city && ` • ${offer.dealer_city}`}
        </p>

        {/* Price */}
        <div className="mb-3">
          {offer.offer_type === "lease" && offer.monthly_payment ? (
            <>
              <span className="text-2xl font-bold text-accent">
                {formatCurrency(offer.monthly_payment)}
              </span>
              <span className="text-gray-400 text-sm">/mo</span>
              {offer.down_payment && (
                <p className="text-sm text-gray-500">
                  {formatCurrency(offer.down_payment)} due at signing
                </p>
              )}
            </>
          ) : offer.offer_type === "finance" && offer.apr ? (
            <>
              <span className="text-2xl font-bold text-accent">
                {offer.apr}%
              </span>
              <span className="text-gray-400 text-sm"> APR</span>
              {offer.term_months && (
                <p className="text-sm text-gray-500">
                  up to {offer.term_months} months
                </p>
              )}
            </>
          ) : (
            <span className="text-gray-400">Contact dealer for pricing</span>
          )}
        </div>

        {/* Term & Mileage for leases */}
        {offer.offer_type === "lease" && (offer.term_months || offer.annual_mileage) && (
          <div className="flex gap-4 text-xs text-gray-500 mb-3">
            {offer.term_months && <span>{offer.term_months} months</span>}
            {offer.annual_mileage && <span>{offer.annual_mileage.toLocaleString()} mi/yr</span>}
          </div>
        )}

        {/* AI Score */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs text-gray-500">
            AI Deal Score: <span className={getConfidenceColor(confidencePercent)}>{confidencePercent}%</span>
          </span>
          <span className="text-xs text-gray-600">
            {getRelativeTime(offer.updated_at)}
          </span>
        </div>

        {/* Action Button */}
        {offer.source_url ? (
          <a
            href={offer.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg border border-accent text-accent hover:bg-accent hover:text-background transition-all duration-200 font-medium text-sm"
          >
            View Details
            <ExternalLink className="w-4 h-4" />
          </a>
        ) : (
          <Link
            href={`/offer/${offer.id}`}
            className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg border border-accent text-accent hover:bg-accent hover:text-background transition-all duration-200 font-medium text-sm"
          >
            View Details
          </Link>
        )}
      </div>
    </div>
  );
}
