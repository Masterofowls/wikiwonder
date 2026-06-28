import Link from "next/link";
import { WifiOff, BookOpen, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Offline" };

export default function OfflinePage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center">
            <WifiOff className="h-10 w-10 text-muted-foreground" />
          </div>
        </div>
        <h1 className="font-display text-3xl font-bold mb-3">You&apos;re Offline</h1>
        <p className="text-muted-foreground mb-6">
          You don&apos;t have an internet connection right now. Some pages you&apos;ve bookmarked are
          still available offline.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button asChild>
            <Link href="/bookmarks">
              <BookOpen className="h-4 w-4 mr-2" />
              Cached Pages
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/">
              <Home className="h-4 w-4 mr-2" />
              Try Home
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
