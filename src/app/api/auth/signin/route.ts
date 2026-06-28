import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { createSession, setSessionCookie } from "@/lib/auth";
import { verifyPassword } from "@/lib/server-utils";
import { z } from "zod";

const SigninSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

export async function POST(request: NextRequest) {
  try {
    const body = SigninSchema.parse(await request.json());

    const user = await db.user.findUnique({ where: { email: body.email } });
    if (!user?.passwordHash) {
      return NextResponse.json({ error: "Invalid credentials" }, { status: 401 });
    }

    const valid = await verifyPassword(user.passwordHash, body.password);
    if (!valid) {
      return NextResponse.json({ error: "Invalid credentials" }, { status: 401 });
    }

    const sessionId = await createSession(user.id);
    await setSessionCookie(sessionId);

    return NextResponse.json({ success: true });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.errors[0]?.message }, { status: 422 });
    }
    console.error("[Signin]", error);
    return NextResponse.json({ error: "Sign in failed" }, { status: 500 });
  }
}
