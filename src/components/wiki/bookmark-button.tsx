"use client";

import { useState } from "react";
import { Bookmark, BookmarkCheck } from "lucide-react";
import { toast } from "sonner";

interface BookmarkButtonProps {
  pageId: number;
  initialBookmarked: boolean;
  count: number;
  disabled?: boolean;
}

export function BookmarkButton({
  pageId,
  initialBookmarked,
  count,
  disabled,
}: BookmarkButtonProps) {
  const [bookmarked, setBookmarked] = useState(initialBookmarked);
  const [bookmarkCount, setBookmarkCount] = useState(count);
  const [loading, setLoading] = useState(false);

  const toggle = async () => {
    if (disabled) {
      toast.error("Sign in to bookmark pages");
      return;
    }
    setLoading(true);
    try {
      const method = bookmarked ? "DELETE" : "POST";
      const res = await fetch("/api/bookmarks", {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pageId }),
      });
      if (!res.ok) throw new Error("Failed");
      setBookmarked(!bookmarked);
      setBookmarkCount((c) => c + (bookmarked ? -1 : 1));
      toast.success(bookmarked ? "Bookmark removed" : "Page bookmarked");
    } catch {
      toast.error("Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={toggle}
      disabled={loading}
      className="flex items-center gap-1.5 hover:text-foreground transition-colors disabled:opacity-50"
      aria-label={bookmarked ? "Remove bookmark" : "Bookmark page"}
    >
      {bookmarked ? (
        <BookmarkCheck className="h-3.5 w-3.5 text-primary" />
      ) : (
        <Bookmark className="h-3.5 w-3.5" />
      )}
      <span className="text-sm">{bookmarkCount}</span>
    </button>
  );
}
