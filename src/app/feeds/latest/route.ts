import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { Feed } from "feed";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://wikiwonder.fly.dev";
const SITE_NAME = process.env.NEXT_PUBLIC_SITE_NAME ?? "WikiWonder";

export async function GET() {
  const pages = await db.wikiPage.findMany({
    where: { status: "PUBLISHED" },
    include: { author: { select: { name: true, username: true } } },
    orderBy: { publishedAt: "desc" },
    take: 30,
  });

  const feed = new Feed({
    title: `${SITE_NAME} — Latest Articles`,
    description: "Latest wiki articles from WikiWonder",
    id: BASE_URL,
    link: BASE_URL,
    language: "en",
    feedLinks: { atom: `${BASE_URL}/feeds/latest` },
    copyright: `© ${new Date().getFullYear()} ${SITE_NAME}`,
    updated: pages[0]?.publishedAt ?? new Date(),
  });

  for (const page of pages) {
    feed.addItem({
      title: page.title,
      id: `${BASE_URL}/wiki/${page.slug}`,
      link: `${BASE_URL}/wiki/${page.slug}`,
      description: page.summary ?? "",
      content: page.content.slice(0, 500),
      date: page.publishedAt ?? page.updatedAt,
      image: page.coverImage ?? `https://picsum.photos/seed/${page.slug}/800/450`,
      author: page.author
        ? [{ name: page.author.name ?? page.author.username }]
        : undefined,
    });
  }

  return new NextResponse(feed.atom1(), {
    headers: {
      "Content-Type": "application/atom+xml; charset=utf-8",
      "Cache-Control": "public, max-age=300, s-maxage=600",
    },
  });
}
