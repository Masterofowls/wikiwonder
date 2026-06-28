"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Sparkles, Upload, Eye, Code } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface EditorProps {
  mode: "create" | "edit";
  page?: {
    id: number;
    title: string;
    slug: string;
    summary: string;
    content: string;
    status: string;
    categoryId?: number;
    tagIds?: number[];
    coverImage?: string;
    sourceUrl?: string;
    isFeatured?: boolean;
  };
  categories?: Array<{ id: number; name: string; slug: string }>;
  allTags?: Array<{ id: number; name: string; slug: string }>;
}

export function WikiEditor({ mode, page, categories = [], allTags = [] }: EditorProps) {
  const router = useRouter();
  const [title, setTitle] = useState(page?.title ?? "");
  const [slug, setSlug] = useState(page?.slug ?? "");
  const [summary, setSummary] = useState(page?.summary ?? "");
  const [content, setContent] = useState(page?.content ?? "");
  const [status, setStatus] = useState(page?.status ?? "DRAFT");
  const [categoryId, setCategoryId] = useState(page?.categoryId?.toString() ?? "");
  const [selectedTags, setSelectedTags] = useState<number[]>(page?.tagIds ?? []);
  const [sourceUrl, setSourceUrl] = useState(page?.sourceUrl ?? "");
  const [isFeatured, setIsFeatured] = useState(page?.isFeatured ?? false);
  const [saving, setSaving] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [previewTab, setPreviewTab] = useState<"write" | "preview">("write");
  const fileRef = useRef<HTMLInputElement>(null);

  const generateSlugFromTitle = (t: string) =>
    t
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .trim()
      .replace(/\s+/g, "-")
      .slice(0, 100);

  const handleTitleChange = (val: string) => {
    setTitle(val);
    if (mode === "create") setSlug(generateSlugFromTitle(val));
  };

  const handleAIFormat = async () => {
    if (!content && !title) {
      toast.error("Enter some content first");
      return;
    }
    setAiLoading(true);
    try {
      const res = await fetch("/api/ai/format", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: content || title }),
      });
      if (!res.ok) throw new Error("AI unavailable");
      const data = (await res.json()) as {
        title?: string;
        summary?: string;
        content?: string;
      };
      if (data.title && !title) setTitle(data.title);
      if (data.summary) setSummary(data.summary);
      if (data.content) setContent(data.content);
      toast.success("Formatted with AI");
    } catch {
      toast.error("AI formatting failed");
    } finally {
      setAiLoading(false);
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      if (!res.ok) throw new Error("Upload failed");
      const data = (await res.json()) as { url: string };
      const imgMd = `\n![${file.name}](${data.url})\n`;
      setContent((c) => c + imgMd);
      toast.success("Image inserted");
    } catch {
      toast.error("Upload failed");
    }
  };

  const toggleTag = (id: number) => {
    setSelectedTags((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    );
  };

  const handleSave = async () => {
    if (!title.trim()) {
      toast.error("Title is required");
      return;
    }
    setSaving(true);
    try {
      const body = {
        title,
        slug: slug || generateSlugFromTitle(title),
        summary,
        content,
        status,
        categoryId: categoryId ? parseInt(categoryId) : null,
        tagIds: selectedTags,
        sourceUrl,
        isFeatured,
      };

      const url = mode === "edit" ? `/api/pages/${page!.slug}` : "/api/pages";
      const method = mode === "edit" ? "PATCH" : "POST";

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const data = (await res.json()) as { error?: string };
        throw new Error(data.error ?? "Save failed");
      }

      const data = (await res.json()) as { slug: string };
      toast.success(mode === "create" ? "Page created!" : "Page saved!");
      router.push(`/wiki/${data.slug}`);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <Label htmlFor="title">Title *</Label>
        <Input
          id="title"
          value={title}
          onChange={(e) => handleTitleChange(e.target.value)}
          placeholder="Page title"
          className="mt-1 text-lg font-display"
          required
        />
      </div>

      {/* Slug */}
      <div>
        <Label htmlFor="slug">Slug</Label>
        <Input
          id="slug"
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
          placeholder="page-slug"
          className="mt-1 font-mono text-sm"
        />
      </div>

      {/* Summary */}
      <div>
        <Label htmlFor="summary">Summary</Label>
        <Textarea
          id="summary"
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          placeholder="Short description (for cards and SEO)..."
          className="mt-1 min-h-[80px]"
        />
      </div>

      {/* Content editor */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <Label>Content (Markdown)</Label>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleAIFormat}
              disabled={aiLoading}
              className="text-xs"
            >
              {aiLoading ? (
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              ) : (
                <Sparkles className="h-3 w-3 mr-1" />
              )}
              AI Format
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs"
              onClick={() => fileRef.current?.click()}
            >
              <Upload className="h-3 w-3 mr-1" />
              Upload Image
            </Button>
            <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleImageUpload} />
          </div>
        </div>

        <Tabs
          value={previewTab}
          onValueChange={(v) => setPreviewTab(v as "write" | "preview")}
        >
          <TabsList className="h-8 mb-2">
            <TabsTrigger value="write" className="text-xs">
              <Code className="h-3 w-3 mr-1" />
              Write
            </TabsTrigger>
            <TabsTrigger value="preview" className="text-xs">
              <Eye className="h-3 w-3 mr-1" />
              Preview
            </TabsTrigger>
          </TabsList>
          <TabsContent value="write">
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Write your content in Markdown...

## Introduction
Use ## for sections.

[[Link to another wiki page]]

```code
// Code blocks
```"
              className="min-h-[400px] font-mono text-sm resize-y"
            />
          </TabsContent>
          <TabsContent value="preview">
            <div className="min-h-[400px] border rounded-md p-4 wiki-content overflow-auto">
              {content ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
              ) : (
                <p className="text-muted-foreground text-sm">Nothing to preview yet.</p>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Metadata row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <Label>Status</Label>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="mt-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="DRAFT">Draft</SelectItem>
              <SelectItem value="PUBLISHED">Published</SelectItem>
              <SelectItem value="ARCHIVED">Archived</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label>Category</Label>
          <Select value={categoryId} onValueChange={setCategoryId}>
            <SelectTrigger className="mt-1">
              <SelectValue placeholder="Select category..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">None</SelectItem>
              {categories.map((c) => (
                <SelectItem key={c.id} value={c.id.toString()}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label>Source URL</Label>
          <Input
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
            placeholder="https://en.wikipedia.org/..."
            className="mt-1 text-sm"
          />
        </div>
      </div>

      {/* Tags */}
      <div>
        <Label>Tags</Label>
        <div className="flex flex-wrap gap-2 mt-2">
          {allTags.map((tag) => (
            <button key={tag.id} onClick={() => toggleTag(tag.id)} type="button">
              <Badge
                variant={selectedTags.includes(tag.id) ? "default" : "outline"}
                className="cursor-pointer hover:opacity-80 transition-opacity"
              >
                #{tag.name}
              </Badge>
            </button>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 border-t pt-4">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
          {mode === "create" ? "Create Page" : "Save Changes"}
        </Button>
        <Button variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
        <div className="ml-auto flex items-center gap-2">
          <input
            type="checkbox"
            id="featured"
            checked={isFeatured}
            onChange={(e) => setIsFeatured(e.target.checked)}
            className="rounded"
          />
          <Label htmlFor="featured" className="cursor-pointer text-sm">
            Featured
          </Label>
        </div>
      </div>
    </div>
  );
}
