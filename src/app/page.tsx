import { Suspense } from "react";
import Link from "next/link";
import Image from "next/image";
import { db } from "@/lib/db";
import { formatRelativeDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BookOpen, Star, TrendingUp, Clock, Plus, ArrowRight } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "WikiWonder — Knowledge Platform",
  description: "Discover, create, and explore wiki articles with AI-powered import.",
};

export const revalidate = 60;

async function getHomeData() {
  const [featured, trending, recent, categories] = await Promise.all([
    db.wikiPage.findMany({
      where: { status: "PUBLISHED", isFeatured: true },
      include: { category: true, tags: { take: 3 } },
      orderBy: { publishedAt: "desc" },
      take: 6,
    }),
    db.wikiPage.findMany({
      where: { status: "PUBLISHED" },
      include: { category: true, tags: { take: 3 } },
      orderBy: { viewCount: "desc" },
      take: 6,
    }),
    db.wikiPage.findMany({
      where: { status: "PUBLISHED" },
      include: { category: true, tags: { take: 3 } },
      orderBy: { publishedAt: "desc" },
      take: 6,
    }),
    db.category.findMany({
      include: { _count: { select: { pages: true } } },
      orderBy: { pages: { _count: "desc" } },
      take: 8,
    }),
  ]);

  return { featured, trending, recent, categories };
}

function PageCard({
  page,
}: {
  page: {
    id: number;
    title: string;
    slug: string;
    summary: string | null;
    coverImage: string | null;
    publishedAt: Date | null;
    updatedAt: Date;
    category: { name: string; slug: string } | null;
    tags: { id: number; name: string; slug: string }[];
  };
}) {
  const coverUrl =
    page.coverImage ?? `https://picsum.photos/seed/${page.slug}/400/225`;

  return (
    <Card className="overflow-hidden group hover:shadow-md transition-all duration-200 h-full flex flex-col">
      <Link href={`/wiki/${page.slug}`} className="block relative aspect-video overflow-hidden">
        <Image
          src={coverUrl}
          alt={page.title}
          fill
          className="object-cover group-hover:scale-105 transition-transform duration-300"
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        />
        {page.category && (
          <div className="absolute top-2 left-2">
            <Badge variant="secondary" className="bg-background/80 backdrop-blur-sm text-xs">
              {page.category.name}
            </Badge>
          </div>
        )}
      </Link>
      <CardContent className="p-4 flex flex-col flex-1">
        <Link href={`/wiki/${page.slug}`} className="group-hover:text-primary transition-colors">
          <h3 className="font-display font-semibold text-base leading-snug line-clamp-2 mb-2">
            {page.title}
          </h3>
        </Link>
        {page.summary && (
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3 flex-1">{page.summary}</p>
        )}
        <div className="flex items-center gap-2 flex-wrap">
          {page.tags.slice(0, 2).map((tag) => (
            <Link key={tag.id} href={`/tag/${tag.slug}`}>
              <Badge variant="outline" className="text-xs hover:bg-accent transition-colors">
                #{tag.name}
              </Badge>
            </Link>
          ))}
          <span className="text-xs text-muted-foreground ml-auto">
            {formatRelativeDate(page.publishedAt ?? page.updatedAt)}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

function CategoryCard({
  category,
}: {
  category: { id: number; name: string; slug: string; _count: { pages: number } };
}) {
  return (
    <Link href={`/category/${category.slug}`}>
      <Card className="hover:shadow-md transition-all duration-200 hover:border-primary/30">
        <CardContent className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <BookOpen className="h-4 w-4" />
            </div>
            <div>
              <div className="font-medium text-sm">{category.name}</div>
              <div className="text-xs text-muted-foreground">
                {category._count.pages} articles
              </div>
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground" />
        </CardContent>
      </Card>
    </Link>
  );
}

function PageGrid({
  pages,
}: {
  pages: Parameters<typeof PageCard>[0]["page"][];
}) {
  if (pages.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <BookOpen className="h-10 w-10 mx-auto mb-3 opacity-30" />
        <p>No pages yet. Create the first one!</p>
        <Button asChild className="mt-4">
          <Link href="/wiki/new">
            <Plus className="h-4 w-4 mr-2" />
            Create Page
          </Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {pages.map((page) => (
        <PageCard key={page.id} page={page} />
      ))}
    </div>
  );
}

export default async function HomePage() {
  const { featured, trending, recent, categories } = await getHomeData();

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero */}
      <section className="text-center py-12 mb-10">
        <h1 className="font-display text-4xl md:text-5xl font-bold mb-4 tracking-tight">
          Your Knowledge Wiki
        </h1>
        <p className="text-muted-foreground text-lg max-w-xl mx-auto mb-6">
          Import from Wikipedia, create with AI assistance, explore offline.
        </p>
        <div className="flex flex-wrap gap-3 justify-center">
          <Button asChild size="lg">
            <Link href="/wiki/new">
              <Plus className="h-4 w-4 mr-2" />
              New Page
            </Link>
          </Button>
          <Button variant="outline" size="lg" asChild>
            <Link href="/wiki/import">Import from URL</Link>
          </Button>
        </div>
      </section>

      {/* Pages */}
      <section className="mb-12">
        <Tabs defaultValue="featured">
          <div className="flex items-center justify-between mb-4">
            <TabsList>
              <TabsTrigger value="featured">
                <Star className="h-3.5 w-3.5 mr-1.5" />
                Featured
              </TabsTrigger>
              <TabsTrigger value="trending">
                <TrendingUp className="h-3.5 w-3.5 mr-1.5" />
                Trending
              </TabsTrigger>
              <TabsTrigger value="recent">
                <Clock className="h-3.5 w-3.5 mr-1.5" />
                Recent
              </TabsTrigger>
            </TabsList>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/search">View all</Link>
            </Button>
          </div>
          <Suspense fallback={<div className="h-64 animate-pulse bg-muted rounded-lg" />}>
            <TabsContent value="featured">
              <PageGrid pages={featured} />
            </TabsContent>
            <TabsContent value="trending">
              <PageGrid pages={trending} />
            </TabsContent>
            <TabsContent value="recent">
              <PageGrid pages={recent} />
            </TabsContent>
          </Suspense>
        </Tabs>
      </section>

      {/* Categories */}
      {categories.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-xl font-semibold">Browse by Category</h2>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/search">All categories</Link>
            </Button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {categories.map((cat) => (
              <CategoryCard key={cat.id} category={cat} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
