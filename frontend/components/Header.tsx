"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { Settings, LogOut, User, Crown } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function Header() {
  const { user, loading, signOut } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const isActive = (path: string) => {
    if (path === "/") return pathname === "/";
    return pathname.startsWith(path);
  };

  const handleSignOut = async () => {
    await signOut();
    router.push("/");
    router.refresh();
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center border border-accent/50 group-hover:border-accent transition-colors">
              <Settings className="w-5 h-5 text-accent" />
            </div>
            <span className="text-xl font-bold">
              <span className="text-white">CarDeals</span>
              <span className="text-accent">AI</span>
            </span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="/"
              className={`transition-colors font-medium ${
                isActive("/") ? "text-accent" : "text-gray-400 hover:text-accent"
              }`}
            >
              Home
            </Link>
            <Link
              href="/deals"
              className={`transition-colors font-medium ${
                isActive("/deals") ? "text-accent" : "text-gray-400 hover:text-accent"
              }`}
            >
              Deals
            </Link>

            {/* Auth section */}
            <div className="ml-4 pl-4 border-l border-border flex items-center gap-3">
              {loading ? (
                <div className="w-8 h-8 rounded-full bg-background-secondary animate-pulse" />
              ) : user ? (
                <>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center border border-accent/50">
                      <User className="w-4 h-4 text-accent" />
                    </div>
                    <span className="text-sm text-gray-400 max-w-[120px] truncate">
                      {user.user_metadata?.full_name || user.email}
                    </span>
                  </div>
                  <span className="px-2 py-1 text-xs font-medium rounded-full bg-accent/10 text-accent border border-accent/30">
                    Free
                  </span>
                  <button
                    onClick={handleSignOut}
                    className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                    title="Sign out"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="text-gray-400 hover:text-white transition-colors font-medium text-sm"
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/signup"
                    className="px-4 py-2 bg-accent hover:bg-accent/90 text-background font-medium text-sm rounded-lg transition-colors"
                  >
                    Sign up
                  </Link>
                </>
              )}
            </div>
          </nav>

          {/* Mobile menu button */}
          <button className="md:hidden text-gray-400 hover:text-accent">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
