export const dynamic = "force-dynamic";
export const revalidate = 3600;

import type { MetadataRoute } from "next";
import { db } from "@/lib/db";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://wikiwonder.fly.dev";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const pages = await db.wikiPage.findMany({
    where: { status: "PUBLISHED" },
    select: { slug: true, updatedAt: true },
    orderBy: { updatedAt: "desc" },
    take: 5000,
  });

  const categories = await db.category.findMany({
    select: { slug: true, updatedAt: true },
    take: 500,
  });

  const tags = await db.tag.findMany({
    select: { slug: true },
    take: 500,
  });

  const wikiPages: MetadataRoute.Sitemap = pages.map((p) => ({
    url: `${BASE_URL}/wiki/${p.slug}`,
    lastModified: p.updatedAt,
    changeFrequency: "weekly",
    priority: 0.8,
  }));

  const categoryPages: MetadataRoute.Sitemap = categories.map((c) => ({
    url: `${BASE_URL}/category/${c.slug}`,
    lastModified: c.updatedAt,
    changeFrequency: "weekly",
    priority: 0.6,
  }));

  const tagPages: MetadataRoute.Sitemap = tags.map((t) => ({
    url: `${BASE_URL}/tag/${t.slug}`,
    changeFrequency: "monthly" as const,
    priority: 0.4,
  }));

  return [
    { url: BASE_URL, changeFrequency: "daily", priority: 1.0 },
    { url: `${BASE_URL}/search`, changeFrequency: "daily", priority: 0.9 },
    ...wikiPages,
    ...categoryPages,
    ...tagPages,
  ];
}
