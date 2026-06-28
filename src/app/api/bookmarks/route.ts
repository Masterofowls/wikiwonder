import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getSession } from "@/lib/auth";

export async function GET() {
  const { user } = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const bookmarks = await db.bookmark.findMany({
    where: { userId: user.id },
    include: {
      page: {
        select: {
          id: true, title: true, slug: true, summary: true, coverImage: true,
          status: true, updatedAt: true, publishedAt: true,
        },
      },
    },
    orderBy: { createdAt: "desc" },
  });

  return NextResponse.json(bookmarks);
}

export async function POST(request: NextRequest) {
  const { user } = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { pageId, note } = (await request.json()) as { pageId: number; note?: string };
  if (!pageId) return NextResponse.json({ error: "pageId required" }, { status: 400 });

  const bookmark = await db.bookmark.upsert({
    where: { userId_pageId: { userId: user.id, pageId } },
    update: { note: note ?? null },
    create: { userId: user.id, pageId, note: note ?? null },
  });

  return NextResponse.json(bookmark, { status: 201 });
}

export async function DELETE(request: NextRequest) {
  const { user } = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { pageId } = (await request.json()) as { pageId: number };
  if (!pageId) return NextResponse.json({ error: "pageId required" }, { status: 400 });

  await db.bookmark.deleteMany({ where: { userId: user.id, pageId } });
  return NextResponse.json({ success: true });
}
