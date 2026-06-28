import { notFound } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { db } from "@/lib/db";
import { markdownToHtml, extractToc } from "@/lib/markdown";
import { getSession } from "@/lib/auth";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { WikiAIPanel } from "@/components/wiki/ai-panel";
import { BookmarkButton } from "@/components/wiki/bookmark-button";
import { TableOfContents } from "@/components/wiki/toc";
import { PageActions } from "@/components/wiki/page-actions";
import {
  Calendar,
  Eye,
  User,
  Tag as TagIcon,
  Globe,
} from "lucide-react";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const page = await db.wikiPage.findUnique({
    where: { slug },
    select: { title: true, summary: true, coverImage: true, slug: true },
  });
  if (!page) return { title: "Not Found" };
  const siteName = process.env.NEXT_PUBLIC_SITE_NAME ?? "WikiWonder";
  return {
    title: `${page.title} | ${siteName}`,
    description: page.summary ?? `${page.title} — wiki article`,
    openGraph: {
      title: page.title,
      description: page.summary ?? "",
      images: page.coverImage
        ? [page.coverImage]
        : [`https://picsum.photos/seed/${page.slug}/1200/630`],
      type: "article",
    },
    twitter: {
      card: "summary_large_image",
      title: page.title,
      description: page.summary ?? "",
    },
  };
}

export default async function WikiPageDetail({ params }: PageProps) {
  const { slug } = await params;
  const { user } = await getSession();

  const page = await db.wikiPage.findUnique({
    where: { slug },
    include: {
      author: { select: { id: true, username: true, name: true, avatar: true } },
      category: true,
      tags: true,
      sections: { orderBy: { order: "asc" } },
      _count: { select: { bookmarks: true } },
    },
  });

  if (!page) {
    const alias = await db.wikiPageAlias.findFirst({
      where: { alias: { equals: slug, mode: "insensitive" } },
      include: { page: true },
    });
    if (alias) {
      return notFound();
    }
    return notFound();
  }

  if (page.status !== "PUBLISHED" && !user?.isStaff && user?.id !== page.authorId) {
    return notFound();
  }

  await db.wikiPage.update({ where: { id: page.id }, data: { viewCount: { increment: 1 } } });

  const htmlContent = await markdownToHtml(page.content);
  const toc = extractToc(page.content);

  const isBookmarked = user
    ? !!(await db.bookmark.findUnique({
        where: { userId_pageId: { userId: user.id, pageId: page.id } },
      }))
    : false;

  const canEdit = user && (user.isStaff || user.id === page.authorId);

  const coverUrl = page.coverImage ?? `https://picsum.photos/seed/${page.slug}/1400/500`;

  return (
    <article className="min-h-screen">
      {/* Cover */}
      <div className="relative h-48 md:h-72 overflow-hidden">
        <Image src={coverUrl} alt={page.title} fill className="object-cover" priority />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent" />
      </div>

      <div className="container mx-auto px-4 -mt-16 relative z-10">
        <div className="max-w-5xl mx-auto">
          {/* Breadcrumb */}
          <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
            <Link href="/" className="hover:text-foreground transition-colors">Home</Link>
            <span>→</span>
            {page.category && (
              <>
                <Link
                  href={`/category/${page.category.slug}`}
                  className="hover:text-foreground transition-colors"
                >
                  {page.category.name}
                </Link>
                <span>→</span>
              </>
            )}
            <span className="text-foreground">{page.title}</span>
          </nav>

          {/* Header */}
          <div className="bg-background rounded-xl border shadow-sm p-6 mb-6">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div className="flex-1 min-w-0">
                {page.status !== "PUBLISHED" && (
                  <Badge variant="secondary" className="mb-2">
                    {page.status.toLowerCase()}
                  </Badge>
                )}
                <h1 className="font-display text-3xl md:text-4xl font-bold leading-tight">
                  {page.title}
                </h1>
                {page.summary && (
                  <p className="text-muted-foreground mt-2 text-base leading-relaxed">
                    {page.summary}
                  </p>
                )}
              </div>
              <PageActions
                page={{ id: page.id, slug: page.slug, title: page.title }}
                canEdit={!!canEdit}
              />
            </div>

            {/* Meta */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
              {page.author && (
                <div className="flex items-center gap-1.5">
                  <User className="h-3.5 w-3.5" />
                  <span>{page.author.name ?? page.author.username}</span>
                </div>
              )}
              <div className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5" />
                <time dateTime={(page.publishedAt ?? page.updatedAt).toISOString()}>
                  {formatDate(page.publishedAt ?? page.updatedAt)}
                </time>
              </div>
              <div className="flex items-center gap-1.5">
                <Eye className="h-3.5 w-3.5" />
                <span>{page.viewCount.toLocaleString()} views</span>
              </div>
              {page.sourceUrl && (
                <a
                  href={page.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 hover:text-foreground transition-colors"
                >
                  <Globe className="h-3.5 w-3.5" />
                  <span>Source</span>
                </a>
              )}
              <BookmarkButton
                pageId={page.id}
                initialBookmarked={isBookmarked}
                count={page._count.bookmarks}
                disabled={!user}
              />
            </div>

            {/* Tags */}
            {page.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-4">
                <TagIcon className="h-3.5 w-3.5 text-muted-foreground mt-0.5" />
                {page.tags.map((tag) => (
                  <Link key={tag.id} href={`/tag/${tag.slug}`}>
                    <Badge variant="outline" className="hover:bg-accent transition-colors text-xs">
                      #{tag.name}
                    </Badge>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Main layout: content + sidebar */}
          <div className="flex gap-6">
            {/* Sidebar: TOC + AI */}
            <aside className="hidden lg:flex flex-col gap-4 w-64 shrink-0">
              {toc.length > 0 && (
                <div className="bg-background rounded-xl border p-4 sticky top-20">
                  <h3 className="text-sm font-semibold mb-3">Contents</h3>
                  <TableOfContents items={toc} />
                </div>
              )}
              {user && (
                <div className="bg-background rounded-xl border p-4 sticky top-72">
                  <WikiAIPanel
                    pageId={page.id}
                    pageTitle={page.title}
                    pageContent={page.content}
                  />
                </div>
              )}
            </aside>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="bg-background rounded-xl border p-6 md:p-8">
                <div
                  className="wiki-content"
                  dangerouslySetInnerHTML={{ __html: htmlContent }}
                />

                {page.sections.length > 0 && (
                  <>
                    <Separator className="my-8" />
                    <div className="text-sm text-muted-foreground">
                      <h3 className="font-semibold mb-3 text-foreground">Sections</h3>
                      <ul className="space-y-1">
                        {page.sections.map((s) => (
                          <li key={s.id}>
                            <a
                              href={`#${s.anchor}`}
                              className="hover:text-foreground transition-colors"
                            >
                              {s.title}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </>
                )}
              </div>

              {/* Edit suggestion */}
              {user && !canEdit && (
                <div className="mt-4 rounded-xl border p-4 bg-muted/30 text-sm">
                  <p className="text-muted-foreground">
                    Found an error?{" "}
                    <Link
                      href={`/wiki/${page.slug}/suggest`}
                      className="text-primary hover:underline"
                    >
                      Suggest an edit
                    </Link>
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Structured data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Article",
            headline: page.title,
            description: page.summary ?? "",
            dateModified: page.updatedAt.toISOString(),
            datePublished: (page.publishedAt ?? page.createdAt).toISOString(),
            author: { "@type": "Person", name: page.author?.name ?? page.author?.username },
          }),
        }}
      />
    </article>
  );
}
