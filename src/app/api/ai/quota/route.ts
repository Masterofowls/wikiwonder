import { NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import { checkQuota } from "@/lib/ai";

export async function GET() {
  const { user } = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const quota = await checkQuota(user.id);
  return NextResponse.json({ ...quota, isStaff: user.isStaff });
}
