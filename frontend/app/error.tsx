"use client";

import Link from "next/link";
import { AlertCircle, RotateCcw, ArrowLeft } from "lucide-react";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-6 border border-red-500/30">
          <AlertCircle className="w-10 h-10 text-red-400" />
        </div>
        <h1 className="text-3xl font-bold text-white mb-2">
          Something went wrong
        </h1>
        <p className="text-gray-400 mb-8">
          An unexpected error occurred. Please try again.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={reset}
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-accent hover:bg-accent-dim text-background font-semibold rounded-lg transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Try Again
          </button>
          <Link
            href="/"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-border hover:border-accent/50 text-white font-medium rounded-lg transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
