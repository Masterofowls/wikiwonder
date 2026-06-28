import { NextResponse } from "next/server";
import { getSession, invalidateSession, clearSessionCookie } from "@/lib/auth";

export async function POST() {
  const { sessionId } = await getSession();
  if (sessionId) {
    await invalidateSession(sessionId);
  }
  await clearSessionCookie();
  return NextResponse.json({ success: true });
}
