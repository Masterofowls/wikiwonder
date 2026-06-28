import { notFound, redirect } from "next/navigation";
import { getSession } from "@/lib/auth";
import { db } from "@/lib/db";
import { WikiEditor } from "@/components/wiki/editor";
import type { Metadata } from "next";

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const page = await db.wikiPage.findUnique({ where: { slug }, select: { title: true } });
  return { title: `Edit: ${page?.title ?? slug}` };
}

export default async function EditWikiPage({ params }: Props) {
  const { slug } = await params;
  const { user } = await getSession();
  if (!user) redirect(`/auth/signin?next=/wiki/${slug}/edit`);

  const page = await db.wikiPage.findUnique({
    where: { slug },
    include: { category: true, tags: true },
  });

  if (!page) return notFound();
  if (!user.isStaff && user.id !== page.authorId) return notFound();

  const categories = await db.category.findMany({ orderBy: { name: "asc" } });
  const tags = await db.tag.findMany({ orderBy: { name: "asc" } });

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="font-display text-3xl font-bold mb-6">Edit: {page.title}</h1>
      <WikiEditor
        mode="edit"
        page={{
          id: page.id,
          title: page.title,
          slug: page.slug,
          summary: page.summary ?? "",
          content: page.content,
          status: page.status,
          categoryId: page.categoryId ?? undefined,
          tagIds: page.tags.map((t) => t.id),
          coverImage: page.coverImage ?? undefined,
          sourceUrl: page.sourceUrl ?? undefined,
          isFeatured: page.isFeatured,
        }}
        categories={categories}
        allTags={tags}
      />
    </div>
  );
}
