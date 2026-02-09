"use client";

export default function OfferCardSkeleton() {
  return (
    <div className="bg-background-card border border-border rounded-xl overflow-hidden animate-pulse">
      {/* Image placeholder */}
      <div className="h-40 bg-background-secondary" />

      {/* Content */}
      <div className="p-4">
        {/* Title skeleton */}
        <div className="h-5 bg-background-secondary rounded w-3/4 mb-2" />

        {/* Dealer skeleton */}
        <div className="h-4 bg-background-secondary rounded w-1/2 mb-3" />

        {/* Price skeleton */}
        <div className="mb-3">
          <div className="h-7 bg-background-secondary rounded w-24 mb-1" />
          <div className="h-4 bg-background-secondary rounded w-32" />
        </div>

        {/* Terms skeleton */}
        <div className="flex gap-4 mb-3">
          <div className="h-3 bg-background-secondary rounded w-16" />
          <div className="h-3 bg-background-secondary rounded w-20" />
        </div>

        {/* Score skeleton */}
        <div className="flex items-center justify-between mb-4">
          <div className="h-3 bg-background-secondary rounded w-24" />
          <div className="h-3 bg-background-secondary rounded w-16" />
        </div>

        {/* Button skeleton */}
        <div className="h-10 bg-background-secondary rounded-lg" />
      </div>
    </div>
  );
}
