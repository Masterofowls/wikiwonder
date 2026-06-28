import { cookies } from "next/headers";
import { cache } from "react";
import { db } from "./db";
import { generateRandomId } from "./server-utils";

const SESSION_COOKIE = "wikiwonder_session";
const SESSION_DURATION_DAYS = 30;

export interface AuthUser {
  id: string;
  email: string;
  username: string;
  name: string | null;
  isStaff: boolean;
  isSuperuser: boolean;
  avatar: string | null;
}

export async function createSession(userId: string): Promise<string> {
  const sessionId = generateRandomId(32);
  const expiresAt = new Date();
  expiresAt.setDate(expiresAt.getDate() + SESSION_DURATION_DAYS);

  await db.session.create({
    data: { id: sessionId, userId, expiresAt },
  });

  return sessionId;
}

export async function setSessionCookie(sessionId: string): Promise<void> {
  const cookieStore = await cookies();
  const expiresAt = new Date();
  expiresAt.setDate(expiresAt.getDate() + SESSION_DURATION_DAYS);

  cookieStore.set(SESSION_COOKIE, sessionId, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    expires: expiresAt,
    path: "/",
  });
}

export async function clearSessionCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.set(SESSION_COOKIE, "", { maxAge: 0, path: "/" });
}

export const getSession = cache(async (): Promise<{ user: AuthUser | null; sessionId: string | null }> => {
  const cookieStore = await cookies();
  const sessionId = cookieStore.get(SESSION_COOKIE)?.value ?? null;

  if (!sessionId) return { user: null, sessionId: null };

  try {
    const session = await db.session.findUnique({
      where: { id: sessionId },
      include: {
        user: {
          select: {
            id: true,
            email: true,
            username: true,
            name: true,
            isStaff: true,
            isSuperuser: true,
            avatar: true,
          },
        },
      },
    });

    if (!session || session.expiresAt < new Date()) {
      if (session) await db.session.delete({ where: { id: sessionId } });
      return { user: null, sessionId: null };
    }

    return { user: session.user, sessionId };
  } catch {
    return { user: null, sessionId: null };
  }
});

export async function invalidateSession(sessionId: string): Promise<void> {
  try {
    await db.session.delete({ where: { id: sessionId } });
  } catch {}
}

export async function requireAuth(): Promise<AuthUser> {
  const { user } = await getSession();
  if (!user) throw new Error("Authentication required");
  return user;
}

export async function requireStaff(): Promise<AuthUser> {
  const user = await requireAuth();
  if (!user.isStaff && !user.isSuperuser) throw new Error("Staff access required");
  return user;
}
