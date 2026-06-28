import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { createSession, setSessionCookie } from "@/lib/auth";
import { hashPassword } from "@/lib/server-utils";
import { generateRandomId } from "@/lib/server-utils";
import { z } from "zod";

const SignupSchema = z.object({
  email: z.string().email(),
  username: z.string().min(3).max(32).regex(/^[a-zA-Z0-9_-]+$/),
  password: z.string().min(8),
  name: z.string().optional(),
});

export async function POST(request: NextRequest) {
  try {
    const body = SignupSchema.parse(await request.json());

    const existing = await db.user.findFirst({
      where: {
        OR: [
          { email: body.email },
          { username: { equals: body.username, mode: "insensitive" } },
        ],
      },
    });

    if (existing) {
      return NextResponse.json(
        { error: existing.email === body.email ? "Email already in use" : "Username taken" },
        { status: 409 }
      );
    }

    const passwordHash = await hashPassword(body.password);
    const userId = generateRandomId(10);

    await db.user.create({
      data: {
        id: userId,
        email: body.email,
        username: body.username,
        name: body.name ?? null,
        passwordHash,
      },
    });

    const sessionId = await createSession(userId);
    await setSessionCookie(sessionId);

    return NextResponse.json({ success: true }, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.errors[0]?.message }, { status: 422 });
    }
    console.error("[Signup]", error);
    return NextResponse.json({ error: "Registration failed" }, { status: 500 });
  }
}
