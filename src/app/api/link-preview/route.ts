import { NextRequest, NextResponse } from "next/server";
import { extractOpenGraph } from "@/lib/utils";

export async function GET(request: NextRequest) {
  const url = request.nextUrl.searchParams.get("url");
  if (!url) return NextResponse.json({ error: "url required" }, { status: 400 });

  try {
    const response = await fetch(url, {
      headers: { "User-Agent": "WikiWonder/2.0 LinkPreview Bot" },
      signal: AbortSignal.timeout(5000),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    const data = extractOpenGraph(html, url);

    return NextResponse.json(data, {
      headers: { "Cache-Control": "public, max-age=3600, s-maxage=86400" },
    });
  } catch (error) {
    console.error("[Link preview]", error);
    return NextResponse.json({ error: "Preview unavailable" }, { status: 502 });
  }
}
