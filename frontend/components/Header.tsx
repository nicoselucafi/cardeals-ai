"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { LogOut, User } from "lucide-react";
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

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/deals", label: "Deals" },
    { href: "/chat", label: "AI Chat" },
  ];

  return (
    <nav className="fixed top-4 left-1/2 -translate-x-1/2 z-50">
      <div className="flex items-center gap-1 px-1.5 py-1.5 rounded-full bg-background-card/80 backdrop-blur-xl border border-border/80 shadow-lg shadow-black/20">
        {navLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 whitespace-nowrap ${
              isActive(link.href)
                ? "bg-accent text-background shadow-sm"
                : "text-gray-400 hover:text-white hover:bg-white/5"
            }`}
          >
            {link.label}
          </Link>
        ))}

        {/* Divider */}
        <div className="w-px h-5 bg-border/60 mx-1" />

        {/* Auth section */}
        {loading ? (
          <div className="w-7 h-7 rounded-full bg-background-secondary animate-pulse mx-1" />
        ) : user ? (
          <div className="flex items-center gap-1">
            <div className="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center border border-accent/40">
              <User className="w-3.5 h-3.5 text-accent" />
            </div>
            <button
              onClick={handleSignOut}
              className="p-1.5 text-gray-500 hover:text-red-400 transition-colors rounded-full hover:bg-white/5"
              title="Sign out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <Link
            href="/login"
            className="px-3 py-1.5 text-sm font-medium text-gray-400 hover:text-white transition-colors rounded-full hover:bg-white/5"
          >
            Sign in
          </Link>
        )}
      </div>
    </nav>
  );
}
