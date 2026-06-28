import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth";
import { WikiEditor } from "@/components/wiki/editor";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "New Wiki Page" };

export default async function NewWikiPage() {
  const { user } = await getSession();
  if (!user) redirect("/auth/signin?next=/wiki/new");

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="font-display text-3xl font-bold mb-6">Create New Page</h1>
      <WikiEditor mode="create" />
    </div>
  );
}
