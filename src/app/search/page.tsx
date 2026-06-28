import Link from "next/link";
import Image from "next/image";
import { db } from "@/lib/db";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { formatRelativeDate } from "@/lib/utils";
import { Search, BookOpen, Tag, FolderOpen } from "lucide-react";
import type { Metadata } from "next";

interface Props {
  searchParams: Promise<{ q?: string; page?: string }>;
}

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const { q } = await searchParams;
  return { title: q ? `Search: ${q}` : "Search" };
}

export default async function SearchPage({ searchParams }: Props) {
  const { q = "", page = "1" } = await searchParams;
  const pageNum = Math.max(1, parseInt(page));
  const pageSize = 12;
  const skip = (pageNum - 1) * pageSize;

  const where = q.trim()
    ? {
        status: "PUBLISHED" as const,
        OR: [
          { title: { contains: q, mode: "insensitive" as const } },
          { summary: { contains: q, mode: "insensitive" as const } },
          { content: { contains: q, mode: "insensitive" as const } },
        ],
      }
    : { status: "PUBLISHED" as const };

  const [pages, total, categories, tags] = await Promise.all([
    db.wikiPage.findMany({
      where,
      include: { category: true, tags: { take: 3 } },
      orderBy: q ? { viewCount: "desc" } : { publishedAt: "desc" },
      skip,
      take: pageSize,
    }),
    db.wikiPage.count({ where }),
    q
      ? db.category.findMany({
          where: { name: { contains: q, mode: "insensitive" } },
          take: 5,
        })
      : Promise.resolve([]),
    q
      ? db.tag.findMany({
          where: { name: { contains: q, mode: "insensitive" } },
          take: 8,
        })
      : Promise.resolve([]),
  ]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="font-display text-2xl font-bold mb-6">
        {q ? `Results for "${q}"` : "Browse All Pages"}
      </h1>

      {/* Search form */}
      <form className="mb-8">
        <div className="relative max-w-xl">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            name="q"
            defaultValue={q}
            placeholder="Search articles, categories, tags..."
            className="pl-9"
          />
        </div>
      </form>

      {/* Category + Tag results */}
      {(categories.length > 0 || tags.length > 0) && (
        <div className="mb-8 flex flex-wrap gap-3">
          {categories.map((cat) => (
            <Link key={cat.id} href={`/category/${cat.slug}`}>
              <Badge variant="secondary" className="gap-1">
                <FolderOpen className="h-3 w-3" />
                {cat.name}
              </Badge>
            </Link>
          ))}
          {tags.map((tag) => (
            <Link key={tag.id} href={`/tag/${tag.slug}`}>
              <Badge variant="outline" className="gap-1">
                <Tag className="h-3 w-3" />#{tag.name}
              </Badge>
            </Link>
          ))}
        </div>
      )}

      {/* Pages */}
      {pages.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-30" />
          <p className="text-lg">No pages found{q ? ` for "${q}"` : ""}.</p>
          <Button asChild className="mt-4">
            <Link href="/wiki/new">Create a page</Link>
          </Button>
        </div>
      ) : (
        <>
          <p className="text-sm text-muted-foreground mb-4">
            {total} result{total !== 1 ? "s" : ""}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {pages.map((page) => {
              const coverUrl =
                page.coverImage ?? `https://picsum.photos/seed/${page.slug}/400/225`;
              return (
                <Link
                  key={page.id}
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
                    <div className="flex items-start gap-2 mb-2">
                      {page.category && (
                        <Badge variant="secondary" className="text-xs shrink-0">
                          {page.category.name}
                        </Badge>
                      )}
                    </div>
                    <h3 className="font-semibold leading-snug line-clamp-2 group-hover:text-primary transition-colors">
                      {page.title}
                    </h3>
                    {page.summary && (
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                        {page.summary}
                      </p>
                    )}
                    <div className="flex items-center gap-2 mt-3 flex-wrap">
                      {page.tags.slice(0, 2).map((t) => (
                        <Badge key={t.id} variant="outline" className="text-xs">
                          #{t.name}
                        </Badge>
                      ))}
                      <span className="text-xs text-muted-foreground ml-auto">
                        {formatRelativeDate(page.publishedAt ?? page.updatedAt)}
                      </span>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              {pageNum > 1 && (
                <Button variant="outline" size="sm" asChild>
                  <Link href={`/search?q=${encodeURIComponent(q)}&page=${pageNum - 1}`}>
                    Previous
                  </Link>
                </Button>
              )}
              <span className="text-sm text-muted-foreground">
                Page {pageNum} of {totalPages}
              </span>
              {pageNum < totalPages && (
                <Button variant="outline" size="sm" asChild>
                  <Link href={`/search?q=${encodeURIComponent(q)}&page=${pageNum + 1}`}>
                    Next
                  </Link>
                </Button>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
