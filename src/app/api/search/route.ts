import { NextRequest, NextResponse } from "next/server";
import { search } from "@/lib/search";

export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get("q") ?? "";
  const limit = Math.min(50, parseInt(request.nextUrl.searchParams.get("limit") ?? "20"));

  try {
    const results = await search(q, limit);
    return NextResponse.json(results);
  } catch (error) {
    console.error("[Search]", error);
    return NextResponse.json({ error: "Search failed" }, { status: 500 });
  }
}
