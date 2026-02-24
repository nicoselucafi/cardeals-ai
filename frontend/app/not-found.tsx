import Link from "next/link";
import { AlertCircle, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-6 border border-accent/30">
          <AlertCircle className="w-10 h-10 text-accent" />
        </div>
        <h1 className="text-4xl font-bold text-white mb-2">404</h1>
        <p className="text-gray-400 text-lg mb-8">
          This page doesn't exist or has been moved.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-6 py-3 bg-accent hover:bg-accent-dim text-background font-semibold rounded-lg transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
      </div>
    </div>
  );
}
