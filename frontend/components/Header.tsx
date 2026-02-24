"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { LogOut, User, Crown, Settings, ChevronDown } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function Header() {
  const { user, loading, isPremium, signOut } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const isActive = (path: string) => {
    if (path === "/") return pathname === "/";
    return pathname.startsWith(path);
  };

  const handleSignOut = async () => {
    setDropdownOpen(false);
    await signOut();
    router.push("/");
    router.refresh();
  };

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    if (dropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [dropdownOpen]);

  // Close dropdown on navigation
  useEffect(() => {
    setDropdownOpen(false);
  }, [pathname]);

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/deals", label: "Deals" },
    { href: "/chat", label: "AI Chat" },
  ];

  return (
    <nav className="fixed top-4 left-1/2 -translate-x-1/2 z-50 max-w-[calc(100vw-2rem)]">
      <div className="flex items-center gap-0.5 sm:gap-1 px-1 sm:px-1.5 py-1.5 rounded-full bg-background-card/80 backdrop-blur-xl border border-border/80 shadow-lg shadow-black/20">
        {navLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`px-2.5 sm:px-4 py-1.5 rounded-full text-xs sm:text-sm font-medium transition-all duration-200 whitespace-nowrap ${
              isActive(link.href)
                ? "bg-accent text-background shadow-sm"
                : "text-gray-400 hover:text-white hover:bg-white/5"
            }`}
          >
            {link.label}
          </Link>
        ))}

        {/* Divider */}
        <div className="w-px h-5 bg-border/60 mx-0.5 sm:mx-1" />

        {/* Auth section */}
        {loading ? (
          <div className="w-7 h-7 rounded-full bg-background-secondary animate-pulse mx-1" />
        ) : user ? (
          <div className="relative flex items-center gap-0.5 sm:gap-1" ref={dropdownRef}>
            {/* Premium/Free badge */}
            {isPremium ? (
              <span className="flex items-center gap-0.5 sm:gap-1 px-1.5 sm:px-2 py-0.5 text-[10px] sm:text-xs font-semibold rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
                <Crown className="w-3 h-3" />
                <span className="hidden sm:inline">Pro</span>
              </span>
            ) : (
              <span className="px-1.5 sm:px-2 py-0.5 text-[10px] sm:text-xs font-medium rounded-full bg-accent/10 text-accent border border-accent/30">
                Free
              </span>
            )}

            {/* Avatar button — toggles dropdown */}
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-0.5 pl-0.5 pr-1 py-0.5 rounded-full hover:bg-white/5 transition-colors"
            >
              <div className="w-6 h-6 sm:w-7 sm:h-7 rounded-full bg-accent/20 flex items-center justify-center border border-accent/40">
                <User className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-accent" />
              </div>
              <ChevronDown className={`w-3 h-3 text-gray-400 transition-transform duration-200 ${dropdownOpen ? "rotate-180" : ""}`} />
            </button>

            {/* Dropdown menu */}
            {dropdownOpen && (
              <div className="absolute top-full right-0 mt-2 w-44 bg-background-card border border-border rounded-xl shadow-card overflow-hidden animate-slide-up-fade">
                <div className="px-3 py-2 border-b border-border">
                  <p className="text-xs text-white font-medium truncate">
                    {user.user_metadata?.full_name || user.email}
                  </p>
                  <p className="text-[10px] text-gray-500 truncate">{user.email}</p>
                </div>
                <Link
                  href="/settings"
                  className="flex items-center gap-2 px-3 py-2.5 text-sm text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
                >
                  <Settings className="w-3.5 h-3.5" />
                  Settings
                </Link>
                <button
                  onClick={handleSignOut}
                  className="flex items-center gap-2 w-full px-3 py-2.5 text-sm text-gray-400 hover:text-red-400 hover:bg-white/5 transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        ) : (
          <Link
            href="/login"
            className="px-2.5 sm:px-3 py-1.5 text-xs sm:text-sm font-medium text-gray-400 hover:text-white transition-colors rounded-full hover:bg-white/5"
          >
            Sign in
          </Link>
        )}
      </div>
    </nav>
  );
}
