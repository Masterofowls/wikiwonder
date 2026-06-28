import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getSession } from "@/lib/auth";
import { slugifyText } from "@/lib/utils";
import { extractSections } from "@/lib/markdown";
import { translateText, isTranslateConfigured } from "@/lib/translate";
import { z } from "zod";

const PageSchema = z.object({
  title: z.string().min(1).max(255),
  slug: z.string().optional(),
  summary: z.string().optional().default(""),
  content: z.string().optional().default(""),
  status: z.enum(["DRAFT", "PUBLISHED", "ARCHIVED"]).optional().default("DRAFT"),
  categoryId: z.number().nullable().optional(),
  tagIds: z.array(z.number()).optional().default([]),
  sourceUrl: z.string().url().optional().or(z.literal("")),
  isFeatured: z.boolean().optional().default(false),
});

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const { user } = await getSession();
  const page = parseInt(searchParams.get("page") ?? "1");
  const pageSize = Math.min(50, parseInt(searchParams.get("pageSize") ?? "20"));

  const pages = await db.wikiPage.findMany({
    where: user ? {} : { status: "PUBLISHED" },
    include: {
      author: { select: { id: true, username: true, name: true } },
      category: true,
      tags: true,
      _count: { select: { sections: true, bookmarks: true } },
    },
    orderBy: { updatedAt: "desc" },
    skip: (page - 1) * pageSize,
    take: pageSize,
  });

  const total = await db.wikiPage.count({
    where: user ? {} : { status: "PUBLISHED" },
  });

  return NextResponse.json({
    results: pages,
    count: total,
    page,
    pageSize,
    totalPages: Math.ceil(total / pageSize),
  });
}

export async function POST(request: NextRequest) {
  const { user } = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  try {
    const body = PageSchema.parse(await request.json());

    let slug = body.slug ?? slugifyText(body.title);
    let counter = 1;
    while (await db.wikiPage.findUnique({ where: { slug } })) {
      slug = `${slugifyText(body.title)}-${counter++}`;
    }

    const publishedAt = body.status === "PUBLISHED" ? new Date() : null;

    const page = await db.wikiPage.create({
      data: {
        title: body.title,
        slug,
        summary: body.summary,
        content: body.content,
        status: body.status,
        categoryId: body.categoryId ?? null,
        sourceUrl: body.sourceUrl || null,
        isFeatured: body.isFeatured,
        authorId: user.id,
        publishedAt,
        tags: body.tagIds.length ? { connect: body.tagIds.map((id) => ({ id })) } : undefined,
      },
    });

    const sections = extractSections(body.content);
    if (sections.length > 0) {
      await db.wikiSection.createMany({
        data: sections.map((s) => ({ ...s, pageId: page.id })),
      });
    }

    if (isTranslateConfigured() && process.env.LARA_AUTO_TRANSLATE === "true") {
      void translateAndSave(page.id, body.title, body.summary, body.content);
    }

    return NextResponse.json({ id: page.id, slug: page.slug }, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.errors }, { status: 422 });
    }
    console.error("[Pages POST]", error);
    return NextResponse.json({ error: "Failed to create page" }, { status: 500 });
  }
}

async function translateAndSave(
  pageId: number,
  title: string,
  summary: string,
  content: string
) {
  try {
    const [titleRu, summaryRu, contentRu] = await Promise.all([
      translateText(title),
      translateText(summary),
      translateText(content),
    ]);
    await db.wikiPage.update({
      where: { id: pageId },
      data: { titleRu, summaryRu, contentRu },
    });
  } catch (e) {
    console.error("[Translate]", e);
  }
}
