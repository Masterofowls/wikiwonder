import { createHash, randomBytes } from "crypto";

export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16).toString("hex");
  const hash = createHash("sha256")
    .update(salt + password + (process.env.SESSION_SECRET ?? "wikiwonder-secret"))
    .digest("hex");
  return `${salt}:${hash}`;
}

export async function verifyPassword(passwordHash: string, password: string): Promise<boolean> {
  const [salt, hash] = passwordHash.split(":");
  if (!salt || !hash) return false;
  const computed = createHash("sha256")
    .update(salt + password + (process.env.SESSION_SECRET ?? "wikiwonder-secret"))
    .digest("hex");
  return computed === hash;
}

export function generateRandomId(bytes = 16): string {
  return randomBytes(bytes).toString("hex");
}
