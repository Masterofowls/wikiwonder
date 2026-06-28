import Link from "next/link";
import { BookOpen, Rss } from "lucide-react";
import { Separator } from "@/components/ui/separator";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t bg-muted/30 mt-auto">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center gap-2 font-display font-bold text-base mb-2">
              <BookOpen className="h-4 w-4" />
              WikiWonder
            </Link>
            <p className="text-sm text-muted-foreground">
              Self-hosted Wikipedia-style knowledge platform with AI import and offline support.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold mb-3">Browse</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link href="/" className="hover:text-foreground transition-colors">Home</Link></li>
              <li><Link href="/search" className="hover:text-foreground transition-colors">Search</Link></li>
              <li><Link href="/links" className="hover:text-foreground transition-colors">Links</Link></li>
              <li><Link href="/bookmarks" className="hover:text-foreground transition-colors">Bookmarks</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold mb-3">Create</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link href="/wiki/new" className="hover:text-foreground transition-colors">New Page</Link></li>
              <li><Link href="/wiki/import" className="hover:text-foreground transition-colors">Import</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold mb-3">API</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link href="/api/pages" className="hover:text-foreground transition-colors">REST API</Link></li>
              <li><Link href="/api/mcp" className="hover:text-foreground transition-colors">MCP</Link></li>
              <li>
                <Link href="/feeds/latest" className="hover:text-foreground transition-colors flex items-center gap-1">
                  <Rss className="h-3 w-3" />
                  RSS Feed
                </Link>
              </li>
              <li><Link href="/sitemap.xml" className="hover:text-foreground transition-colors">Sitemap</Link></li>
            </ul>
          </div>
        </div>

        <Separator />

        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 text-sm text-muted-foreground">
          <p>© {currentYear} WikiWonder. Open source, self-hosted.</p>
          <div className="flex items-center gap-4">
            <Link href="/offline" className="hover:text-foreground transition-colors">Offline</Link>
            <Link href="/robots.txt" className="hover:text-foreground transition-colors">robots.txt</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
