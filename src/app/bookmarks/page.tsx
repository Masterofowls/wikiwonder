import { redirect } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { getSession } from "@/lib/auth";
import { db } from "@/lib/db";
import { formatRelativeDate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Bookmark, BookOpen, Search } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "My Bookmarks" };

export default async function BookmarksPage() {
  const { user } = await getSession();
  if (!user) redirect("/auth/signin?next=/bookmarks");

  const bookmarks = await db.bookmark.findMany({
    where: { userId: user.id },
    include: {
      page: {
        include: { category: true, tags: { take: 2 } },
      },
    },
    orderBy: { createdAt: "desc" },
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <Bookmark className="h-6 w-6 text-primary" />
        <h1 className="font-display text-2xl font-bold">My Bookmarks</h1>
        <Badge variant="secondary">{bookmarks.length}</Badge>
      </div>

      {bookmarks.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-30" />
          <p className="text-lg mb-4">No bookmarks yet.</p>
          <Button asChild>
            <Link href="/search">
              <Search className="h-4 w-4 mr-2" />
              Explore articles
            </Link>
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {bookmarks.map((bookmark) => {
            const page = bookmark.page;
            const coverUrl =
              page.coverImage ?? `https://picsum.photos/seed/${page.slug}/400/225`;

            return (
              <Link
                key={bookmark.id}
                href={`/wiki/${page.slug}`}
                className="group border rounded-lg overflow-hidden hover:shadow-md transition-all"
              >
                <div className="relative aspect-video overflow-hidden">
                  <Image
                    src={coverUrl}
                    alt={page.title}
                    fill
                    className="object-cover group-hover:scale-105 transition-transform duration-300"
                    sizes="400px"
                  />
                </div>
                <div className="p-4">
                  {page.category && (
                    <Badge variant="secondary" className="text-xs mb-2">
                      {page.category.name}
                    </Badge>
                  )}
                  <h3 className="font-semibold leading-snug line-clamp-2 group-hover:text-primary transition-colors mb-1">
                    {page.title}
                  </h3>
                  {page.summary && (
                    <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                      {page.summary}
                    </p>
                  )}
                  {bookmark.note && (
                    <p className="text-xs text-primary italic mb-2">📝 {bookmark.note}</p>
                  )}
                  <div className="flex items-center gap-2">
                    {page.tags.map((t) => (
                      <Badge key={t.id} variant="outline" className="text-xs">
                        #{t.name}
                      </Badge>
                    ))}
                    <span className="text-xs text-muted-foreground ml-auto">
                      {formatRelativeDate(bookmark.createdAt)}
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
