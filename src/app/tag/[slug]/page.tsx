import { notFound } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { db } from "@/lib/db";
import { Badge } from "@/components/ui/badge";
import { formatRelativeDate } from "@/lib/utils";
import { Tag } from "lucide-react";
import type { Metadata } from "next";

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const tag = await db.tag.findUnique({ where: { slug }, select: { name: true } });
  return { title: tag ? `#${tag.name}` : "Not Found" };
}

export default async function TagPage({ params }: Props) {
  const { slug } = await params;

  const tag = await db.tag.findUnique({
    where: { slug },
    include: {
      _count: { select: { pages: true } },
    },
  });

  if (!tag) return notFound();

  const pages = await db.wikiPage.findMany({
    where: {
      tags: { some: { slug } },
      status: "PUBLISHED",
    },
    include: { category: true, tags: { take: 3 } },
    orderBy: { publishedAt: "desc" },
    take: 30,
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <Tag className="h-6 w-6 text-primary" />
        <h1 className="font-display text-2xl font-bold">#{tag.name}</h1>
        <Badge variant="secondary">{tag._count.pages} articles</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {pages.map((page) => {
          const coverUrl = page.coverImage ?? `https://picsum.photos/seed/${page.slug}/400/225`;
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
                {page.category && (
                  <Badge variant="secondary" className="text-xs mb-2">
                    {page.category.name}
                  </Badge>
                )}
                <h3 className="font-semibold leading-snug line-clamp-2 group-hover:text-primary transition-colors mb-2">
                  {page.title}
                </h3>
                <div className="flex items-center gap-2">
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
    </div>
  );
}
