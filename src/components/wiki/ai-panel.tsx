"use client";

import { useState } from "react";
import { Bot, MessageSquare, List, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ReactMarkdown from "react-markdown";

interface WikiAIPanelProps {
  pageId: number;
  pageTitle: string;
  pageContent: string;
}

export function WikiAIPanel({ pageId, pageTitle, pageContent }: WikiAIPanelProps) {
  const [summary, setSummary] = useState("");
  const [answer, setAnswer] = useState("");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState<"summary" | "ask" | null>(null);
  const [error, setError] = useState("");

  const getSummary = async () => {
    setLoading("summary");
    setError("");
    try {
      const res = await fetch("/api/ai/page/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pageId, content: pageContent, title: pageTitle }),
      });
      if (!res.ok) {
        const data = (await res.json()) as { error?: string };
        throw new Error(data.error ?? "Request failed");
      }
      const data = (await res.json()) as { summary: string };
      setSummary(data.summary);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(null);
    }
  };

  const ask = async () => {
    if (!question.trim()) return;
    setLoading("ask");
    setError("");
    try {
      const res = await fetch("/api/ai/page/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pageId,
          content: pageContent,
          title: pageTitle,
          question,
        }),
      });
      if (!res.ok) {
        const data = (await res.json()) as { error?: string };
        throw new Error(data.error ?? "Request failed");
      }
      const data = (await res.json()) as { answer: string };
      setAnswer(data.answer);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Bot className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-semibold">AI Assistant</h3>
      </div>

      <Tabs defaultValue="summary" className="text-xs">
        <TabsList className="w-full h-8">
          <TabsTrigger value="summary" className="flex-1 text-xs">
            <List className="h-3 w-3 mr-1" />
            Summarize
          </TabsTrigger>
          <TabsTrigger value="ask" className="flex-1 text-xs">
            <MessageSquare className="h-3 w-3 mr-1" />
            Ask
          </TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="mt-3">
          {!summary ? (
            <Button size="sm" className="w-full text-xs" onClick={getSummary} disabled={!!loading}>
              {loading === "summary" ? (
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              ) : null}
              Generate Summary
            </Button>
          ) : (
            <div className="text-xs text-muted-foreground leading-relaxed">
              <ReactMarkdown>{summary}</ReactMarkdown>
            </div>
          )}
        </TabsContent>

        <TabsContent value="ask" className="mt-3 space-y-2">
          <Textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask anything about this article..."
            className="text-xs min-h-[80px] resize-none"
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) ask();
            }}
          />
          <Button size="sm" className="w-full text-xs" onClick={ask} disabled={!!loading}>
            {loading === "ask" ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : null}
            Ask (Ctrl+Enter)
          </Button>
          {answer && (
            <div className="text-xs text-muted-foreground leading-relaxed border-t pt-2 mt-2">
              <ReactMarkdown>{answer}</ReactMarkdown>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {error && (
        <p className="text-xs text-destructive mt-2">{error}</p>
      )}
    </div>
  );
}
