import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function slugifyText(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .slice(0, 255);
}

export function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen - 3) + "...";
}

export function formatDate(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
}

export function formatRelativeDate(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
  return `${Math.floor(diffDays / 365)} years ago`;
}

export function generateSlug(base: string, existing: string[] = []): string {
  let slug = slugifyText(base) || "page";
  let counter = 1;
  while (existing.includes(slug)) {
    slug = `${slugifyText(base)}-${counter++}`;
  }
  return slug;
}

export function extractOpenGraph(html: string, url: string) {
  const getMeta = (name: string): string => {
    const match =
      html.match(
        new RegExp(
          `<meta[^>]+(?:property|name)=["']${name}["'][^>]+content=["']([^"']+)["']`,
          "i"
        )
      ) ??
      html.match(
        new RegExp(
          `<meta[^>]+content=["']([^"']+)["'][^>]+(?:property|name)=["']${name}["']`,
          "i"
        )
      );
    return match?.[1] ?? "";
  };

  const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);

  return {
    title: getMeta("og:title") || getMeta("twitter:title") || titleMatch?.[1] || url,
    description:
      getMeta("og:description") ||
      getMeta("twitter:description") ||
      getMeta("description"),
    imageUrl: getMeta("og:image") || getMeta("twitter:image") || undefined,
    siteName: getMeta("og:site_name") || undefined,
    faviconUrl: (() => {
      const match = html.match(
        /<link[^>]+rel=["'](?:shortcut icon|icon)["'][^>]+href=["']([^"']+)["']/i
      );
      if (match?.[1]) {
        const favicon = match[1];
        if (favicon.startsWith("http")) return favicon;
        try {
          const base = new URL(url);
          return `${base.origin}${favicon.startsWith("/") ? "" : "/"}${favicon}`;
        } catch {
          return undefined;
        }
      }
      try {
        return new URL(url).origin + "/favicon.ico";
      } catch {
        return undefined;
      }
    })(),
  };
}
