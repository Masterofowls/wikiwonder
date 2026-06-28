import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import { writeFile, mkdir } from "fs/promises";
import path from "path";

const UPLOAD_DIR = path.join(process.cwd(), "public", "uploads");
const MAX_SIZE = 10 * 1024 * 1024; // 10MB

export async function POST(request: NextRequest) {
  const { user } = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  try {
    const formData = await request.formData();
    const file = formData.get("file") as File | null;

    if (!file) return NextResponse.json({ error: "No file" }, { status: 400 });
    if (file.size > MAX_SIZE) return NextResponse.json({ error: "File too large (max 10MB)" }, { status: 413 });

    const allowed = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"];
    if (!allowed.includes(file.type)) {
      return NextResponse.json({ error: "File type not allowed" }, { status: 415 });
    }

    await mkdir(UPLOAD_DIR, { recursive: true });

    const ext = file.name.split(".").pop() ?? "bin";
    const filename = `${Date.now()}-${Math.random().toString(36).slice(2)}.${ext}`;
    const filepath = path.join(UPLOAD_DIR, filename);

    const buffer = Buffer.from(await file.arrayBuffer());
    await writeFile(filepath, buffer);

    return NextResponse.json({ url: `/uploads/${filename}` }, { status: 201 });
  } catch (error) {
    console.error("[Upload]", error);
    return NextResponse.json({ error: "Upload failed" }, { status: 500 });
  }
}
