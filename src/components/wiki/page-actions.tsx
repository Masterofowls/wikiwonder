"use client";

import Link from "next/link";
import { MoreHorizontal, Edit, Share, Download, Flag } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface PageActionsProps {
  page: { id: number; slug: string; title: string };
  canEdit: boolean;
}

export function PageActions({ page, canEdit }: PageActionsProps) {
  const share = async () => {
    const url = `${window.location.origin}/wiki/${page.slug}`;
    if (navigator.share) {
      await navigator.share({ title: page.title, url });
    } else {
      await navigator.clipboard.writeText(url);
      toast.success("Link copied to clipboard");
    }
  };

  return (
    <div className="flex items-center gap-2">
      {canEdit && (
        <Button variant="outline" size="sm" asChild>
          <Link href={`/wiki/${page.slug}/edit`}>
            <Edit className="h-3.5 w-3.5 mr-1.5" />
            Edit
          </Link>
        </Button>
      )}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={share}>
            <Share className="mr-2 h-4 w-4" />
            Share
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href={`/api/import/export/${page.slug}?format=md`} download>
              <Download className="mr-2 h-4 w-4" />
              Export Markdown
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href={`/api/import/export/${page.slug}?format=txt`} download>
              <Download className="mr-2 h-4 w-4" />
              Export Text
            </Link>
          </DropdownMenuItem>
          {!canEdit && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href={`/wiki/${page.slug}/suggest`}>
                  <Flag className="mr-2 h-4 w-4" />
                  Suggest Edit
                </Link>
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
