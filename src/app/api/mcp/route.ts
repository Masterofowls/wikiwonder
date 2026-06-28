import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { search } from "@/lib/search";
import { importFromWikipedia, importFromUrl } from "@/lib/import";

const MCP_TOOLS = [
  {
    name: "search_wiki",
    description: "Search wiki pages, categories, tags, and links",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Search query" },
        limit: { type: "number", description: "Max results (default 10)" },
      },
      required: ["query"],
    },
  },
  {
    name: "get_page",
    description: "Get a wiki page by slug",
    inputSchema: {
      type: "object",
      properties: { slug: { type: "string" } },
      required: ["slug"],
    },
  },
  {
    name: "list_pages",
    description: "List published wiki pages",
    inputSchema: {
      type: "object",
      properties: {
        limit: { type: "number" },
        category: { type: "string" },
      },
    },
  },
  {
    name: "preview_import",
    description: "Preview importing content from a URL",
    inputSchema: {
      type: "object",
      properties: { url: { type: "string" } },
      required: ["url"],
    },
  },
  {
    name: "export_page",
    description: "Export a page as markdown",
    inputSchema: {
      type: "object",
      properties: { slug: { type: "string" } },
      required: ["slug"],
    },
  },
];

async function handleToolCall(name: string, args: Record<string, unknown>) {
  switch (name) {
    case "search_wiki":
      return await search(args.query as string, (args.limit as number | undefined) ?? 10);

    case "get_page": {
      const page = await db.wikiPage.findUnique({
        where: { slug: args.slug as string, status: "PUBLISHED" },
        include: { category: true, tags: true, sections: true },
      });
      if (!page) throw new Error(`Page not found: ${args.slug}`);
      return page;
    }

    case "list_pages": {
      const where: Record<string, unknown> = { status: "PUBLISHED" };
      if (args.category) {
        where.category = { slug: args.category };
      }
      return await db.wikiPage.findMany({
        where,
        select: { title: true, slug: true, summary: true, publishedAt: true },
        take: (args.limit as number | undefined) ?? 20,
        orderBy: { publishedAt: "desc" },
      });
    }

    case "preview_import": {
      const url = args.url as string;
      if (/wikipedia\.org/i.test(url)) {
        return await importFromWikipedia(url);
      }
      return await importFromUrl(url);
    }

    case "export_page": {
      const page = await db.wikiPage.findUnique({
        where: { slug: args.slug as string, status: "PUBLISHED" },
      });
      if (!page) throw new Error(`Page not found: ${args.slug}`);
      return { markdown: page.content, title: page.title };
    }

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

export async function GET() {
  return NextResponse.json({ tools: MCP_TOOLS, version: "2.0" });
}

export async function POST(request: NextRequest) {
  let body: { id?: unknown; method: string; params?: Record<string, unknown> };

  try {
    body = await request.json() as typeof body;
  } catch {
    return NextResponse.json(
      { jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } },
      { status: 400 }
    );
  }

  const { id = null, method, params = {} } = body;
  const respond = (result: unknown) => NextResponse.json({ jsonrpc: "2.0", id, result });
  const error = (code: number, message: string) =>
    NextResponse.json({ jsonrpc: "2.0", id, error: { code, message } }, { status: 400 });

  try {
    if (method === "initialize") {
      return respond({
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: { name: "wikiwonder-mcp", version: "2.0" },
      });
    }

    if (method === "tools/list") {
      return respond({ tools: MCP_TOOLS });
    }

    if (method === "tools/call") {
      const toolName = (params.name ?? params.tool) as string;
      const toolArgs = (params.arguments ?? params.args ?? {}) as Record<string, unknown>;
      const result = await handleToolCall(toolName, toolArgs);
      return respond({ content: [{ type: "text", text: JSON.stringify(result, null, 2) }] });
    }

    return error(-32601, "Method not found");
  } catch (e) {
    return NextResponse.json(
      { jsonrpc: "2.0", id, error: { code: -32000, message: String(e) } },
      { status: 500 }
    );
  }
}
