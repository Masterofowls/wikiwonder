"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { BookOpen, Search, Plus, Moon, Sun, Menu, X, User, LogOut, Settings } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import type { SearchResult } from "@/lib/search";

interface HeaderProps {
  user?: {
    id: string;
    username: string;
    name?: string | null;
    isStaff?: boolean;
    avatar?: string | null;
  } | null;
}

export function Header({ user }: HeaderProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  const { theme, setTheme } = useTheme();
  const router = useRouter();
  const searchRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearch = (value: string) => {
    setQuery(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (value.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      const res = await fetch(`/api/search?q=${encodeURIComponent(value)}&limit=8`);
      if (res.ok) {
        const data = (await res.json()) as SearchResult[];
        setResults(data);
        setOpen(data.length > 0);
      }
    }, 250);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      setOpen(false);
    }
  };

  const handleSignOut = async () => {
    await fetch("/api/auth/signout", { method: "POST" });
    router.refresh();
  };

  const typeIcons: Record<string, string> = {
    page: "📄",
    category: "📁",
    tag: "#",
    link: "🔗",
  };

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-14 items-center gap-4 px-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 font-display font-bold text-lg shrink-0">
          <BookOpen className="h-5 w-5 text-primary" />
          <span className="hidden sm:block">WikiWonder</span>
        </Link>

        {/* Search */}
        <div ref={searchRef} className="relative flex-1 max-w-lg">
          <form onSubmit={handleSubmit}>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Search wiki..."
                className="pl-9 h-9"
                aria-label="Search"
              />
            </div>
          </form>
          {open && results.length > 0 && (
            <div className="absolute top-full mt-1 w-full rounded-md border bg-popover shadow-lg z-50 overflow-hidden">
              {results.map((r) => (
                <Link
                  key={`${r.type}-${r.id}`}
                  href={r.url}
                  className="flex items-center gap-3 px-3 py-2 hover:bg-accent transition-colors text-sm"
                  onClick={() => setOpen(false)}
                >
                  <span className="text-base">{typeIcons[r.type] ?? "•"}</span>
                  <div className="min-w-0">
                    <div className="font-medium truncate">{r.title}</div>
                    {r.description && (
                      <div className="text-xs text-muted-foreground truncate">{r.description}</div>
                    )}
                  </div>
                </Link>
              ))}
              <Link
                href={`/search?q=${encodeURIComponent(query)}`}
                className="flex items-center justify-center px-3 py-2 text-sm text-primary hover:bg-accent border-t transition-colors"
                onClick={() => setOpen(false)}
              >
                See all results →
              </Link>
            </div>
          )}
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="ghost" size="sm" asChild className="hidden md:flex">
            <Link href="/wiki/new">
              <Plus className="h-4 w-4 mr-1" />
              New Page
            </Link>
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label="Toggle theme"
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>

          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="rounded-full">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src={user.avatar ?? ""} alt={user.username} />
                    <AvatarFallback>
                      {(user.name ?? user.username).slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <div className="px-2 py-1.5 text-sm">
                  <div className="font-medium">{user.name ?? user.username}</div>
                  <div className="text-xs text-muted-foreground">@{user.username}</div>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/bookmarks">
                    <BookOpen className="mr-2 h-4 w-4" />
                    Bookmarks
                  </Link>
                </DropdownMenuItem>
                {user.isStaff && (
                  <DropdownMenuItem asChild>
                    <Link href="/admin">
                      <Settings className="mr-2 h-4 w-4" />
                      Admin
                    </Link>
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleSignOut} className="text-destructive">
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button variant="outline" size="sm" asChild>
              <Link href="/auth/signin">
                <User className="h-4 w-4 mr-1" />
                Sign in
              </Link>
            </Button>
          )}

          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileMenu(!mobileMenu)}
            aria-label="Toggle menu"
          >
            {mobileMenu ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenu && (
        <div className="border-t md:hidden">
          <div className="container mx-auto px-4 py-3 space-y-2">
            <Button variant="ghost" size="sm" asChild className="w-full justify-start">
              <Link href="/wiki/new" onClick={() => setMobileMenu(false)}>
                <Plus className="h-4 w-4 mr-2" />
                New Page
              </Link>
            </Button>
            <Button variant="ghost" size="sm" asChild className="w-full justify-start">
              <Link href="/wiki/import" onClick={() => setMobileMenu(false)}>
                <Search className="h-4 w-4 mr-2" />
                Import
              </Link>
            </Button>
          </div>
        </div>
      )}
    </header>
  );
}
