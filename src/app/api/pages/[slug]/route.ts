import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getSession } from "@/lib/auth";

interface Params {
  params: Promise<{ slug: string }>;
}

export async function GET(_req: NextRequest, { params }: Params) {
  const { slug } = await params;
  const page = await db.wikiPage.findUnique({
    where: { slug },
    include: {
      author: { select: { id: true, username: true, name: true } },
      category: true,
      tags: true,
      sections: { orderBy: { order: "asc" } },
    },
  });
  if (!page) return NextResponse.json({ error: "Not found" }, { status: 404 });
  return NextResponse.json(page);
}

export async function PATCH(request: NextRequest, { params }: Params) {
  const { slug } = await params;
  const { user } = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const page = await db.wikiPage.findUnique({ where: { slug } });
  if (!page) return NextResponse.json({ error: "Not found" }, { status: 404 });
  if (!user.isStaff && user.id !== page.authorId) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  try {
    const body = (await request.json()) as Record<string, unknown>;

    await db.pageRevision.create({
      data: {
        pageId: page.id,
        editorId: user.id,
        title: page.title,
        content: page.content,
        changeSummary: (body.changeSummary as string) ?? "",
      },
    });

    const updated = await db.wikiPage.update({
      where: { id: page.id },
      data: {
        title: (body.title as string | undefined) ?? page.title,
        summary: (body.summary as string | undefined) ?? page.summary,
        content: (body.content as string | undefined) ?? page.content,
        status: (body.status as "DRAFT" | "PUBLISHED" | "ARCHIVED" | undefined) ?? page.status,
        categoryId:
          body.categoryId !== undefined ? (body.categoryId as number | null) : page.categoryId,
        sourceUrl: (body.sourceUrl as string | undefined) ?? page.sourceUrl,
        isFeatured: (body.isFeatured as boolean | undefined) ?? page.isFeatured,
        publishedAt:
          body.status === "PUBLISHED" && !page.publishedAt ? new Date() : page.publishedAt,
        tags:
          body.tagIds !== undefined
            ? {
                set: (body.tagIds as number[]).map((id) => ({ id })),
              }
            : undefined,
      },
    });

    return NextResponse.json({ id: updated.id, slug: updated.slug });
  } catch (error) {
    console.error("[Page PATCH]", error);
    return NextResponse.json({ error: "Update failed" }, { status: 500 });
  }
}

export async function DELETE(_req: NextRequest, { params }: Params) {
  const { slug } = await params;
  const { user } = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const page = await db.wikiPage.findUnique({ where: { slug } });
  if (!page) return NextResponse.json({ error: "Not found" }, { status: 404 });
  if (!user.isStaff && user.id !== page.authorId) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  await db.wikiPage.delete({ where: { id: page.id } });
  return NextResponse.json({ success: true });
}
