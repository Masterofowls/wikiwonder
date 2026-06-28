import { db } from "./db";
import type { WikiPage, Category, Tag, SharedLink } from "@prisma/client";

export interface SearchResult {
  type: "page" | "category" | "tag" | "link";
  id: string | number;
  title: string;
  slug: string;
  description?: string;
  url: string;
}

export async function search(query: string, limit = 20): Promise<SearchResult[]> {
  if (!query || query.trim().length < 2) return [];

  const q = query.trim();
  const results: SearchResult[] = [];

  const [pages, categories, tags, links] = await Promise.all([
    searchPages(q, limit),
    searchCategories(q, 5),
    searchTags(q, 5),
    searchLinks(q, 5),
  ]);

  results.push(
    ...pages.map((p) => ({
      type: "page" as const,
      id: p.id,
      title: p.title,
      slug: p.slug,
      description: p.summary ?? undefined,
      url: `/wiki/${p.slug}`,
    }))
  );

  results.push(
    ...categories.map((c) => ({
      type: "category" as const,
      id: c.id,
      title: c.name,
      slug: c.slug,
      description: c.description ?? undefined,
      url: `/category/${c.slug}`,
    }))
  );

  results.push(
    ...tags.map((t) => ({
      type: "tag" as const,
      id: t.id,
      title: `#${t.name}`,
      slug: t.slug,
      url: `/tag/${t.slug}`,
    }))
  );

  results.push(
    ...links.map((l) => ({
      type: "link" as const,
      id: l.id,
      title: l.title,
      slug: l.slug,
      description: l.description ?? undefined,
      url: `/links/${l.slug}`,
    }))
  );

  return results.slice(0, limit);
}

async function searchPages(q: string, limit: number): Promise<WikiPage[]> {
  return db.wikiPage.findMany({
    where: {
      status: "PUBLISHED",
      OR: [
        { title: { contains: q, mode: "insensitive" } },
        { summary: { contains: q, mode: "insensitive" } },
        { content: { contains: q, mode: "insensitive" } },
      ],
    },
    take: limit,
    orderBy: [{ isFeatured: "desc" }, { viewCount: "desc" }, { updatedAt: "desc" }],
  });
}

async function searchCategories(q: string, limit: number): Promise<Category[]> {
  return db.category.findMany({
    where: {
      OR: [
        { name: { contains: q, mode: "insensitive" } },
        { description: { contains: q, mode: "insensitive" } },
      ],
    },
    take: limit,
  });
}

async function searchTags(q: string, limit: number): Promise<Tag[]> {
  return db.tag.findMany({
    where: { name: { contains: q, mode: "insensitive" } },
    take: limit,
  });
}

async function searchLinks(q: string, limit: number): Promise<SharedLink[]> {
  return db.sharedLink.findMany({
    where: {
      OR: [
        { title: { contains: q, mode: "insensitive" } },
        { description: { contains: q, mode: "insensitive" } },
      ],
    },
    take: limit,
  });
}
