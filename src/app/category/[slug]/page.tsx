import { notFound } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { db } from "@/lib/db";
import { Badge } from "@/components/ui/badge";
import { formatRelativeDate } from "@/lib/utils";
import { FolderOpen } from "lucide-react";
import type { Metadata } from "next";

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const cat = await db.category.findUnique({ where: { slug }, select: { name: true } });
  if (!cat) return { title: "Not Found" };
  return { title: `Category: ${cat.name}` };
}

export default async function CategoryPage({ params }: Props) {
  const { slug } = await params;

  const category = await db.category.findUnique({
    where: { slug },
    include: {
      children: { include: { _count: { select: { pages: true } } } },
      _count: { select: { pages: true } },
    },
  });

  if (!category) return notFound();

  const pages = await db.wikiPage.findMany({
    where: { categoryId: category.id, status: "PUBLISHED" },
    include: { tags: { take: 3 } },
    orderBy: { publishedAt: "desc" },
    take: 30,
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <FolderOpen className="h-6 w-6 text-primary" />
        <div>
          <h1 className="font-display text-2xl font-bold">{category.name}</h1>
          {category.description && (
            <p className="text-muted-foreground text-sm">{category.description}</p>
          )}
        </div>
        <Badge variant="secondary" className="ml-auto">
          {category._count.pages} articles
        </Badge>
      </div>

      {category.children.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-medium text-muted-foreground mb-2">Subcategories</h2>
          <div className="flex flex-wrap gap-2">
            {category.children.map((child) => (
              <Link key={child.id} href={`/category/${child.slug}`}>
                <Badge variant="outline" className="hover:bg-accent transition-colors py-1.5">
                  <FolderOpen className="h-3 w-3 mr-1" />
                  {child.name} ({child._count.pages})
                </Badge>
              </Link>
            ))}
          </div>
        </div>
      )}

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
                <h3 className="font-semibold leading-snug line-clamp-2 group-hover:text-primary transition-colors mb-2">
                  {page.title}
                </h3>
                {page.summary && (
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{page.summary}</p>
                )}
                <div className="flex items-center gap-2 flex-wrap">
                  {page.tags.map((t) => (
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
