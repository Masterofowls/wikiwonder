import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import { askAboutPage, isAiConfigured, checkQuota, incrementQuota } from "@/lib/ai";

export async function POST(request: NextRequest) {
  const { user } = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  if (!isAiConfigured()) return NextResponse.json({ error: "AI not configured" }, { status: 503 });

  const { content, title, question } = (await request.json()) as {
    pageId: number;
    content: string;
    title: string;
    question: string;
  };

  if (!question) return NextResponse.json({ error: "question required" }, { status: 400 });

  if (!user.isStaff) {
    const quota = await checkQuota(user.id);
    if (quota.remaining <= 0) {
      return NextResponse.json({ error: "Daily quota exceeded", quota }, { status: 429 });
    }
  }

  try {
    const answer = await askAboutPage(content, title, question);
    if (!user.isStaff) await incrementQuota(user.id);
    return NextResponse.json({ answer });
  } catch (error) {
    console.error("[AI ask]", error);
    return NextResponse.json({ error: "AI request failed" }, { status: 500 });
  }
}
