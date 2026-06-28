export async function translateText(text: string, targetLang = "ru"): Promise<string> {
  const accessKeyId = process.env.LARA_ACCESS_KEY_ID;
  const accessKeySecret = process.env.LARA_ACCESS_KEY_SECRET;

  if (!accessKeyId || !accessKeySecret) {
    return text;
  }

  const CHUNK_SIZE = 5000;
  const chunks = chunkText(text, CHUNK_SIZE);
  const translated: string[] = [];

  for (const chunk of chunks) {
    try {
      const result = await translateChunk(chunk, targetLang, accessKeyId, accessKeySecret);
      translated.push(result);
    } catch (error) {
      console.error("[Lara] Translation error:", error);
      translated.push(chunk);
    }
  }

  return translated.join("\n\n");
}

async function translateChunk(
  text: string,
  targetLang: string,
  keyId: string,
  keySecret: string
): Promise<string> {
  const body = JSON.stringify({
    q: text,
    source: "en",
    target: targetLang,
  });

  const timestamp = Date.now();
  const signature = await createHmacSignature(`${timestamp}:${body}`, keySecret);

  const response = await fetch("https://api.laratranslate.com/v1/translate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Access-Key-Id": keyId,
      "X-Timestamp": String(timestamp),
      "X-Signature": signature,
    },
    body,
  });

  if (!response.ok) {
    throw new Error(`Lara API error: ${response.status}`);
  }

  const data = (await response.json()) as { translatedText?: string };
  return data.translatedText ?? text;
}

async function createHmacSignature(message: string, secret: string): Promise<string> {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secret);
  const messageData = encoder.encode(message);

  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    keyData,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );

  const signature = await crypto.subtle.sign("HMAC", cryptoKey, messageData);
  return Buffer.from(signature).toString("hex");
}

function chunkText(text: string, maxSize: number): string[] {
  if (text.length <= maxSize) return [text];
  const chunks: string[] = [];
  let current = "";

  for (const paragraph of text.split("\n\n")) {
    if ((current + paragraph).length > maxSize && current) {
      chunks.push(current.trim());
      current = "";
    }
    current += paragraph + "\n\n";
  }

  if (current.trim()) chunks.push(current.trim());
  return chunks;
}

export function isTranslateConfigured(): boolean {
  return Boolean(process.env.LARA_ACCESS_KEY_ID && process.env.LARA_ACCESS_KEY_SECRET);
}
