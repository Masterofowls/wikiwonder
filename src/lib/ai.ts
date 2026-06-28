import Cerebras from "@cerebras/cerebras_cloud_sdk";
import { db } from "./db";

const DEFAULT_MODEL = process.env.CEREBRAS_MODEL ?? "gpt-oss-120b";
const DAILY_QUOTA = 10;

interface CerebrasChoice {
  message?: { content?: string };
  delta?: { content?: string };
}

interface CerebrasResponse {
  choices: CerebrasChoice[];
}

function getCerebrasClient(): Cerebras {
  const apiKey = process.env.CEREBRAS_API_KEY;
  if (!apiKey) throw new Error("CEREBRAS_API_KEY is not configured");
  return new Cerebras({ apiKey });
}

export async function formatTextToMarkdown(
  rawText: string,
  hint?: string
): Promise<{ title: string; summary: string; content: string }> {
  const client = getCerebrasClient();
  const prompt = `You are a Wikipedia-style article formatter.

Convert the following raw text into a well-structured markdown article.
Return a JSON object with keys: "title", "summary" (2-3 sentences), "content" (full markdown).

${hint ? `Context hint: ${hint}\n` : ""}
Raw text:
---
${rawText.slice(0, 8000)}
---

JSON response only, no explanation:`;

  const response = await client.chat.completions.create({
    model: DEFAULT_MODEL,
    messages: [{ role: "user", content: prompt }],
    temperature: 0.3,
    max_completion_tokens: 4000,
  }) as unknown as CerebrasResponse;

  const text = response.choices[0]?.message?.content ?? "{}";
  try {
    const cleaned = text.replace(/```json\n?/g, "").replace(/```\n?/g, "").trim();
    return JSON.parse(cleaned) as { title: string; summary: string; content: string };
  } catch {
    return { title: "Untitled", summary: "", content: rawText };
  }
}

export async function summarizePage(content: string, title: string): Promise<string> {
  const client = getCerebrasClient();
  const response = await client.chat.completions.create({
    model: DEFAULT_MODEL,
    messages: [
      {
        role: "user",
        content: `Summarize the following article "${title}" in 5-7 bullet points (markdown list):\n\n${content.slice(0, 6000)}`,
      },
    ],
    temperature: 0.4,
    max_completion_tokens: 500,
  }) as unknown as CerebrasResponse;
  return response.choices[0]?.message?.content ?? "";
}

export async function askAboutPage(
  content: string,
  title: string,
  question: string
): Promise<string> {
  const client = getCerebrasClient();
  const response = await client.chat.completions.create({
    model: DEFAULT_MODEL,
    messages: [
      {
        role: "system",
        content: `You are a helpful assistant answering questions about a wiki article titled "${title}". Answer concisely based on the article content.`,
      },
      {
        role: "user",
        content: `Article content:\n${content.slice(0, 6000)}\n\nQuestion: ${question}`,
      },
    ],
    temperature: 0.5,
    max_completion_tokens: 600,
  }) as unknown as CerebrasResponse;
  return response.choices[0]?.message?.content ?? "";
}

export async function suggestTitle(content: string): Promise<string> {
  const client = getCerebrasClient();
  const response = await client.chat.completions.create({
    model: DEFAULT_MODEL,
    messages: [
      {
        role: "user",
        content: `Suggest a concise, descriptive title for this article (3-8 words, no quotes):\n\n${content.slice(0, 2000)}`,
      },
    ],
    temperature: 0.7,
    max_completion_tokens: 50,
  }) as unknown as CerebrasResponse;
  return (response.choices[0]?.message?.content ?? "Untitled").trim();
}

export async function* streamChat(
  messages: Array<{ role: "user" | "assistant" | "system"; content: string }>
): AsyncGenerator<string> {
  const client = getCerebrasClient();
  const stream = await client.chat.completions.create({
    model: DEFAULT_MODEL,
    messages,
    stream: true,
    temperature: 0.7,
    max_completion_tokens: 1000,
  });

  for await (const chunk of stream as AsyncIterable<CerebrasResponse>) {
    const delta = chunk.choices[0]?.delta?.content;
    if (delta) yield delta;
  }
}

export async function checkQuota(
  userId: string
): Promise<{ used: number; limit: number; remaining: number }> {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const usage = await db.aIUsageDaily.findUnique({
    where: { userId_date: { userId, date: today } },
  });

  const used = usage?.requestCount ?? 0;
  return { used, limit: DAILY_QUOTA, remaining: Math.max(0, DAILY_QUOTA - used) };
}

export async function incrementQuota(userId: string): Promise<void> {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  await db.aIUsageDaily.upsert({
    where: { userId_date: { userId, date: today } },
    update: { requestCount: { increment: 1 } },
    create: { userId, date: today, requestCount: 1 },
  });
}

export function isAiConfigured(): boolean {
  return Boolean(process.env.CEREBRAS_API_KEY);
}
