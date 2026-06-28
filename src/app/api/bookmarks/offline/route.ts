import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getSession } from "@/lib/auth";

export async function GET() {
  const { user } = await getSession();
  if (!user) return NextResponse.json({ urls: [] });

  const bookmarks = await db.bookmark.findMany({
    where: { userId: user.id },
    select: { page: { select: { slug: true } } },
  });

  const urls = bookmarks.map((b) => `/wiki/${b.page.slug}`);
  return NextResponse.json({ urls });
}
