
export interface ImportResult {
  title: string;
  summary: string;
  content: string;
  coverImage?: string;
  sourceUrl: string;
  tags?: string[];
}

/** Detect source type from URL */
export function detectSourceType(url: string): "wikipedia" | "mediawiki" | "rss" | "generic" {
  if (/wikipedia\.org\/wiki\//i.test(url)) return "wikipedia";
  if (/\/w\/api\.php|mediawiki|wiki\./i.test(url)) return "mediawiki";
  if (/\.xml|rss|feed|atom/i.test(url)) return "rss";
  return "generic";
}

/** Import from Wikipedia URL */
export async function importFromWikipedia(url: string): Promise<ImportResult> {
  const match = url.match(/wikipedia\.org\/wiki\/([^#?]+)/i);
  if (!match) throw new Error("Invalid Wikipedia URL");

  const title = decodeURIComponent(match[1].replace(/_/g, " "));
  const lang = url.match(/(\w+)\.wikipedia\.org/)?.[1] ?? "en";

  const apiUrl = `https://${lang}.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(match[1])}`;
  const response = await fetch(apiUrl, {
    headers: { "User-Agent": "WikiWonder/2.0 ImportBot" },
  });

  if (!response.ok) throw new Error(`Wikipedia API error: ${response.status}`);
  const data = (await response.json()) as {
    title: string;
    extract: string;
    thumbnail?: { source: string };
    description?: string;
  };

  const contentUrl = `https://${lang}.wikipedia.org/api/rest_v1/page/html/${encodeURIComponent(match[1])}`;
  const htmlRes = await fetch(contentUrl, {
    headers: { "User-Agent": "WikiWonder/2.0 ImportBot" },
  });

  let markdownContent = "";
  if (htmlRes.ok) {
    const html = await htmlRes.text();
    markdownContent = htmlToMarkdown(html, title);
  } else {
    markdownContent = data.extract ?? "";
  }

  return {
    title: data.title ?? title,
    summary: data.description ?? data.extract?.slice(0, 300) ?? "",
    content: (markdownContent || data.extract) ?? "",
    coverImage: data.thumbnail?.source,
    sourceUrl: url,
    tags: [],
  };
}

/** Import from generic URL */
export async function importFromUrl(url: string): Promise<ImportResult> {
  const response = await fetch(url, {
    headers: { "User-Agent": "WikiWonder/2.0 ImportBot" },
    signal: AbortSignal.timeout(15000),
  });

  if (!response.ok) throw new Error(`Failed to fetch: ${response.status}`);
  const html = await response.text();

  const getMeta = (name: string): string => {
    const match =
      html.match(new RegExp(`<meta[^>]+(?:property|name)=["']${name}["'][^>]+content=["']([^"']+)["']`, "i")) ??
      html.match(new RegExp(`<meta[^>]+content=["']([^"']+)["'][^>]+(?:property|name)=["']${name}["']`, "i"));
    return match?.[1] ?? "";
  };

  const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);

  const title = getMeta("og:title") || getMeta("twitter:title") || titleMatch?.[1] || url;
  const description = getMeta("og:description") || getMeta("twitter:description") || getMeta("description");
  const ogImage = getMeta("og:image");
  const coverImage = ogImage || undefined;

  const content = htmlToMarkdown(html, title);

  return { title: title.trim(), summary: description.slice(0, 300), content, coverImage, sourceUrl: url };
}

/** Convert HTML to Markdown (regex-based, no DOM) */
function htmlToMarkdown(html: string, _title: string): string {
  if (!html) return "";

  return html
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<nav[\s\S]*?<\/nav>/gi, "")
    .replace(/<footer[\s\S]*?<\/footer>/gi, "")
    .replace(/<header[\s\S]*?<\/header>/gi, "")
    .replace(/<aside[\s\S]*?<\/aside>/gi, "")
    .replace(/<h1[^>]*>([\s\S]*?)<\/h1>/gi, (_, t) => `\n# ${stripTags(t).trim()}\n\n`)
    .replace(/<h2[^>]*>([\s\S]*?)<\/h2>/gi, (_, t) => `\n## ${stripTags(t).trim()}\n\n`)
    .replace(/<h3[^>]*>([\s\S]*?)<\/h3>/gi, (_, t) => `\n### ${stripTags(t).trim()}\n\n`)
    .replace(/<h4[^>]*>([\s\S]*?)<\/h4>/gi, (_, t) => `\n#### ${stripTags(t).trim()}\n\n`)
    .replace(/<p[^>]*>([\s\S]*?)<\/p>/gi, (_, t) => `\n${stripTags(t).trim()}\n\n`)
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<(strong|b)[^>]*>([\s\S]*?)<\/\1>/gi, (_, _tag, t) => `**${stripTags(t)}**`)
    .replace(/<(em|i)[^>]*>([\s\S]*?)<\/\1>/gi, (_, _tag, t) => `*${stripTags(t)}*`)
    .replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, (_, t) => `\`${t.trim()}\``)
    .replace(/<pre[^>]*>[\s\S]*?<code[^>]*>([\s\S]*?)<\/code>[\s\S]*?<\/pre>/gi, (_, t) =>
      `\n\`\`\`\n${t.trim()}\n\`\`\`\n\n`
    )
    .replace(/<a[^>]+href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi, (_, href, t) => {
      const text = stripTags(t).trim();
      if (!href || href.startsWith("#") || href.startsWith("javascript:")) return text;
      return `[${text}](${href})`;
    })
    .replace(/<img[^>]+src=["']([^"']+)["'][^>]*alt=["']([^"']*)["'][^>]*>/gi, (_, src, alt) =>
      `\n![${alt}](${src})\n`
    )
    .replace(/<img[^>]+src=["']([^"']+)["'][^>]*>/gi, (_, src) => `\n![](${src})\n`)
    .replace(/<li[^>]*>([\s\S]*?)<\/li>/gi, (_, t) => `- ${stripTags(t).trim()}\n`)
    .replace(/<[^>]+>/g, "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function stripTags(html: string): string {
  return html.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
}

/** Import from text/file content */
export async function importFromText(
  content: string,
  filename?: string
): Promise<ImportResult> {
  const firstLine = content.split("\n").find((l) => l.trim()) ?? filename ?? "Imported Page";
  const title = firstLine.replace(/^#+\s*/, "").slice(0, 255);

  return {
    title,
    summary: content.slice(0, 300).replace(/\n/g, " "),
    content,
    sourceUrl: "",
  };
}
