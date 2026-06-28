import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import { summarizePage, isAiConfigured, checkQuota, incrementQuota } from "@/lib/ai";

export async function POST(request: NextRequest) {
  const { user } = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  if (!isAiConfigured()) return NextResponse.json({ error: "AI not configured" }, { status: 503 });

  const { content, title } = (await request.json()) as {
    pageId: number;
    content: string;
    title: string;
  };

  if (!user.isStaff) {
    const quota = await checkQuota(user.id);
    if (quota.remaining <= 0) {
      return NextResponse.json(
        { error: "Daily quota exceeded", quota },
        { status: 429 }
      );
    }
  }

  try {
    const summary = await summarizePage(content, title);
    if (!user.isStaff) await incrementQuota(user.id);
    return NextResponse.json({ summary });
  } catch (error) {
    console.error("[AI summarize]", error);
    return NextResponse.json({ error: "AI request failed" }, { status: 500 });
  }
}
