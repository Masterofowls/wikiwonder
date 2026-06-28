import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import { formatTextToMarkdown, isAiConfigured } from "@/lib/ai";

export async function POST(request: NextRequest) {
  const { user } = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  if (!isAiConfigured()) {
    return NextResponse.json({ error: "AI not configured" }, { status: 503 });
  }

  const { text, hint } = (await request.json()) as { text: string; hint?: string };
  if (!text) return NextResponse.json({ error: "text required" }, { status: 400 });

  try {
    const result = await formatTextToMarkdown(text, hint);
    return NextResponse.json(result);
  } catch (error) {
    console.error("[AI format]", error);
    return NextResponse.json({ error: "AI request failed" }, { status: 500 });
  }
}
