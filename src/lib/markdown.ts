import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import remarkRehype from "remark-rehype";
import rehypeSlug from "rehype-slug";
import rehypeHighlight from "rehype-highlight";
import rehypeKatex from "rehype-katex";
import rehypeRaw from "rehype-raw";
import rehypeStringify from "rehype-stringify";
import { visit } from "unist-util-visit";
import type { Element, Root } from "hast";

export interface TocItem {
  id: string;
  text: string;
  level: number;
}

/** Process wikilinks [[Page Title]] → <a data-wikilink> */
function remarkWikilinks() {
  return (tree: Parameters<typeof visit>[0]) => {
    visit(tree, "text", (node: { type: string; value: string; [k: string]: unknown }) => {
      const regex = /\[\[([^\]]+)\]\]/g;
      const text = node.value;
      if (!regex.test(text)) return;

      const parts: unknown[] = [];
      let lastIndex = 0;
      regex.lastIndex = 0;
      let match: RegExpExecArray | null;

      while ((match = regex.exec(text)) !== null) {
        if (match.index > lastIndex) {
          parts.push({ type: "text", value: text.slice(lastIndex, match.index) });
        }
        const [, inner] = match;
        const [slug, label] = inner.includes("|") ? inner.split("|") : [inner, inner];
        parts.push({
          type: "link",
          url: `/wiki/${encodeURIComponent(slug.trim().toLowerCase().replace(/\s+/g, "-"))}`,
          data: { hProperties: { "data-wikilink": "true" } },
          children: [{ type: "text", value: label.trim() }],
        });
        lastIndex = match.index + match[0].length;
      }

      if (lastIndex < text.length) {
        parts.push({ type: "text", value: text.slice(lastIndex) });
      }

      if (parts.length > 1) {
        Object.assign(node, { type: "paragraph", children: parts });
      }
    });
  };
}

/** Add copy buttons to code blocks */
function rehypeCopyButtons() {
  return (tree: Root) => {
    visit(tree, "element", (node: Element) => {
      if (node.tagName === "pre") {
        const codeEl = node.children.find(
          (c): c is Element => c.type === "element" && c.tagName === "code"
        );
        if (!codeEl) return;
        const lang = (codeEl.properties?.className as string[] | undefined)
          ?.find((c) => c.startsWith("language-"))
          ?.replace("language-", "") ?? "";

        node.properties = {
          ...node.properties,
          "data-lang": lang,
          className: ["relative", "group", ...(node.properties?.className as string[] ?? [])],
        };
      }
    });
  };
}

export async function markdownToHtml(content: string): Promise<string> {
  const result = await unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkMath)
    .use(remarkWikilinks)
    .use(remarkRehype, { allowDangerousHtml: true })
    .use(rehypeRaw)
    .use(rehypeSlug)
    .use(rehypeHighlight)
    .use(rehypeKatex)
    .use(rehypeCopyButtons)
    .use(rehypeStringify)
    .process(content);

  return String(result);
}

export function extractToc(content: string): TocItem[] {
  const lines = content.split("\n");
  const toc: TocItem[] = [];

  for (const line of lines) {
    const match = line.match(/^(#{1,4})\s+(.+)$/);
    if (match) {
      const level = match[1].length;
      const text = match[2].replace(/\*\*/g, "").replace(/\*/g, "").trim();
      const id = text
        .toLowerCase()
        .replace(/[^\w\s-]/g, "")
        .replace(/\s+/g, "-")
        .replace(/-+/g, "-");
      toc.push({ id, text, level });
    }
  }

  return toc;
}

export function extractSections(
  content: string
): Array<{ title: string; slug: string; anchor: string; content: string; order: number }> {
  const parts = content.split(/^## /m);
  const sections: Array<{
    title: string;
    slug: string;
    anchor: string;
    content: string;
    order: number;
  }> = [];

  for (let i = 1; i < parts.length; i++) {
    const [titleLine, ...rest] = parts[i].split("\n");
    const title = titleLine.trim();
    const anchor = title
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .replace(/\s+/g, "-");
    const slug = anchor;
    sections.push({
      title,
      slug,
      anchor,
      content: rest.join("\n").trim(),
      order: i - 1,
    });
  }

  return sections;
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .slice(0, 255);
}
