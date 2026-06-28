import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import { db } from "@/lib/db";
import { detectSourceType, importFromWikipedia, importFromUrl } from "@/lib/import";
import { extractSections } from "@/lib/markdown";
import { slugifyText } from "@/lib/utils";
import { z } from "zod";

const ImportSchema = z.object({
  url: z.string().url(),
  createPage: z.boolean().optional().default(false),
  status: z.enum(["DRAFT", "PUBLISHED"]).optional().default("DRAFT"),
  categoryId: z.number().nullable().optional(),
});

export async function POST(request: NextRequest) {
  const { user } = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  try {
    const body = ImportSchema.parse(await request.json());
    const sourceType = detectSourceType(body.url);

    let result;
    if (sourceType === "wikipedia") {
      result = await importFromWikipedia(body.url);
    } else {
      result = await importFromUrl(body.url);
    }

    if (!body.createPage) {
      return NextResponse.json({ preview: result });
    }

    let slug = slugifyText(result.title);
    let counter = 1;
    while (await db.wikiPage.findUnique({ where: { slug } })) {
      slug = `${slugifyText(result.title)}-${counter++}`;
    }

    const page = await db.wikiPage.create({
      data: {
        title: result.title,
        slug,
        summary: result.summary,
        content: result.content,
        status: body.status,
        sourceUrl: body.url,
        coverImage: result.coverImage ?? null,
        categoryId: body.categoryId ?? null,
        authorId: user.id,
        publishedAt: body.status === "PUBLISHED" ? new Date() : null,
      },
    });

    const sections = extractSections(result.content);
    if (sections.length > 0) {
      await db.wikiSection.createMany({
        data: sections.map((s) => ({ ...s, pageId: page.id })),
      });
    }

    return NextResponse.json({ page: { id: page.id, slug: page.slug } }, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.errors }, { status: 422 });
    }
    console.error("[Import URL]", error);
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}
