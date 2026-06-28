"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Globe, FileText, Loader2, Upload, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

interface ImportPreview {
  title: string;
  summary: string;
  content: string;
  coverImage?: string;
  sourceUrl: string;
}

export default function ImportPage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState<"DRAFT" | "PUBLISHED">("DRAFT");
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  // Text import state
  const [textContent, setTextContent] = useState("");
  const [textTitle, setTextTitle] = useState("");

  const handleUrlPreview = async () => {
    if (!url.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("/api/import/url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, createPage: false }),
      });
      if (!res.ok) throw new Error("Import failed");
      const data = (await res.json()) as { preview: ImportPreview };
      setPreview(data.preview);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleUrlImport = async () => {
    if (!url.trim()) return;
    setCreating(true);
    try {
      const res = await fetch("/api/import/url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, createPage: true, status }),
      });
      if (!res.ok) throw new Error("Import failed");
      const data = (await res.json()) as { page: { slug: string } };
      toast.success("Page imported!");
      router.push(`/wiki/${data.page.slug}`);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const handleFileImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    setTextContent(text);
    setTextTitle(file.name.replace(/\.[^.]+$/, ""));
    toast.success(`Loaded: ${file.name}`);
  };

  const handleTextImport = async () => {
    if (!textContent.trim()) return;
    setCreating(true);
    try {
      const res = await fetch("/api/pages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: textTitle || "Imported Page",
          content: textContent,
          status,
        }),
      });
      if (!res.ok) throw new Error("Import failed");
      const data = (await res.json()) as { slug: string };
      toast.success("Page created!");
      router.push(`/wiki/${data.slug}`);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const isWikipedia = /wikipedia\.org/i.test(url);

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <h1 className="font-display text-3xl font-bold mb-2">Import Content</h1>
      <p className="text-muted-foreground mb-6">
        Import from Wikipedia, any URL, or paste/upload text files.
      </p>

      <Tabs defaultValue="url">
        <TabsList className="mb-6">
          <TabsTrigger value="url">
            <Globe className="h-4 w-4 mr-2" />
            From URL
          </TabsTrigger>
          <TabsTrigger value="text">
            <FileText className="h-4 w-4 mr-2" />
            Text / File
          </TabsTrigger>
        </TabsList>

        {/* URL Import */}
        <TabsContent value="url">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Import from URL</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>URL</Label>
                <div className="flex gap-2 mt-1">
                  <Input
                    value={url}
                    onChange={(e) => {
                      setUrl(e.target.value);
                      setPreview(null);
                    }}
                    placeholder="https://en.wikipedia.org/wiki/..."
                    type="url"
                  />
                  <Button variant="outline" onClick={handleUrlPreview} disabled={loading || !url}>
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Preview"}
                  </Button>
                </div>
                {isWikipedia && (
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1 flex items-center gap-1">
                    <Check className="h-3 w-3" />
                    Wikipedia article detected — full import with citations
                  </p>
                )}
              </div>

              {preview && (
                <div className="border rounded-lg p-4 bg-muted/30 space-y-2">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="secondary">Preview</Badge>
                    <span className="text-sm font-medium">{preview.title}</span>
                  </div>
                  {preview.summary && (
                    <p className="text-sm text-muted-foreground">{preview.summary}</p>
                  )}
                  {preview.coverImage ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={preview.coverImage} alt="" className="rounded-md h-24 object-cover w-full" />
                  ) : null}
                  <p className="text-xs text-muted-foreground">
                    ~{preview.content.split(/\s+/).length} words
                  </p>
                </div>
              )}

              <div>
                <Label>Import as</Label>
                <Select value={status} onValueChange={(v) => setStatus(v as typeof status)}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DRAFT">Draft</SelectItem>
                    <SelectItem value="PUBLISHED">Published</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button
                className="w-full"
                onClick={handleUrlImport}
                disabled={creating || !url}
              >
                {creating ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Globe className="h-4 w-4 mr-2" />}
                Import Page
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Text/File Import */}
        <TabsContent value="text">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Import from Text or File</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Upload File (Markdown, TXT)</Label>
                <label className="mt-1 flex items-center gap-3 border-2 border-dashed rounded-lg p-4 cursor-pointer hover:bg-muted/30 transition-colors">
                  <Upload className="h-5 w-5 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    Click to upload .md, .txt file
                  </span>
                  <input
                    type="file"
                    accept=".md,.txt,.markdown"
                    className="hidden"
                    onChange={handleFileImport}
                  />
                </label>
              </div>

              <div>
                <Label>Title</Label>
                <Input
                  value={textTitle}
                  onChange={(e) => setTextTitle(e.target.value)}
                  placeholder="Page title"
                  className="mt-1"
                />
              </div>

              <div>
                <Label>Content (Markdown)</Label>
                <Textarea
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  placeholder="Paste markdown content here..."
                  className="mt-1 min-h-[200px] font-mono text-sm"
                />
              </div>

              <div>
                <Label>Status</Label>
                <Select value={status} onValueChange={(v) => setStatus(v as typeof status)}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DRAFT">Draft</SelectItem>
                    <SelectItem value="PUBLISHED">Published</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button
                className="w-full"
                onClick={handleTextImport}
                disabled={creating || !textContent}
              >
                {creating ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <FileText className="h-4 w-4 mr-2" />
                )}
                Create Page
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
