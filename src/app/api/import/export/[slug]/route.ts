import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getSession } from "@/lib/auth";

interface Params {
  params: Promise<{ slug: string }>;
}

export async function GET(request: NextRequest, { params }: Params) {
  const { slug } = await params;
  const format = request.nextUrl.searchParams.get("format") ?? "md";
  const { user } = await getSession();

  const page = await db.wikiPage.findUnique({
    where: { slug },
    include: { category: true, tags: true },
  });

  if (!page) return NextResponse.json({ error: "Not found" }, { status: 404 });
  if (page.status !== "PUBLISHED" && !user?.isStaff && user?.id !== page.authorId) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const filename = `${page.slug}`;

  if (format === "json") {
    return NextResponse.json(
      {
        title: page.title,
        slug: page.slug,
        summary: page.summary,
        content: page.content,
        status: page.status,
        category: page.category?.name,
        tags: page.tags.map((t) => t.name),
        sourceUrl: page.sourceUrl,
        createdAt: page.createdAt,
        updatedAt: page.updatedAt,
      },
      {
        headers: {
          "Content-Disposition": `attachment; filename="${filename}.json"`,
        },
      }
    );
  }

  if (format === "txt") {
    const text = `${page.title}\n${"=".repeat(page.title.length)}\n\n${page.summary ? page.summary + "\n\n" : ""}${page.content.replace(/[#*`_~\[\]]/g, "")}`;
    return new Response(text, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Content-Disposition": `attachment; filename="${filename}.txt"`,
      },
    });
  }

  const frontmatter = `---
title: "${page.title}"
slug: "${page.slug}"
status: "${page.status}"
${page.summary ? `summary: "${page.summary}"` : ""}
${page.category ? `category: "${page.category.name}"` : ""}
${page.tags.length ? `tags: [${page.tags.map((t) => `"${t.name}"`).join(", ")}]` : ""}
date: "${page.updatedAt.toISOString()}"
---

`;

  return new Response(frontmatter + page.content, {
    headers: {
      "Content-Type": "text/markdown; charset=utf-8",
      "Content-Disposition": `attachment; filename="${filename}.md"`,
    },
  });
}
