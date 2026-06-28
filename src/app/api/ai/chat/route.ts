import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";
import { streamChat, isAiConfigured } from "@/lib/ai";

export async function POST(request: NextRequest) {
  const { user } = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  if (!isAiConfigured()) return NextResponse.json({ error: "AI not configured" }, { status: 503 });

  const { messages } = (await request.json()) as {
    messages: Array<{ role: "user" | "assistant" | "system"; content: string }>;
  };

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of streamChat(messages)) {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ delta: chunk })}\n\n`));
        }
        controller.enqueue(encoder.encode("data: [DONE]\n\n"));
      } catch (error) {
        console.error("[AI chat stream]", error);
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ error: "Stream error" })}\n\n`));
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
