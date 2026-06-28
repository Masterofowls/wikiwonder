import type { Metadata, Viewport } from "next";
import { DM_Sans, Fraunces } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { Toaster } from "@/components/ui/toast";
import { getSession } from "@/lib/auth";
import "./globals.css";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const SITE_NAME = process.env.NEXT_PUBLIC_SITE_NAME ?? "WikiWonder";
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://wikiwonder.fly.dev";
const SITE_DESCRIPTION =
  "Self-hosted Wikipedia-style knowledge platform with AI import, offline support, and rich media.";

export const metadata: Metadata = {
  title: {
    default: `${SITE_NAME} — Knowledge Platform`,
    template: `%s | ${SITE_NAME}`,
  },
  description: SITE_DESCRIPTION,
  metadataBase: new URL(SITE_URL),
  openGraph: {
    type: "website",
    siteName: SITE_NAME,
    title: `${SITE_NAME} — Knowledge Platform`,
    description: SITE_DESCRIPTION,
  },
  twitter: { card: "summary_large_image" },
  manifest: "/manifest.json",
  applicationName: SITE_NAME,
  keywords: ["wiki", "knowledge", "notes", "documentation"],
  authors: [{ name: SITE_NAME }],
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#09090b" },
  ],
  width: "device-width",
  initialScale: 1,
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const { user } = await getSession();

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />
      </head>
      <body className={`${dmSans.variable} ${fraunces.variable} min-h-screen flex flex-col`}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <Header user={user} />
          <main className="flex-1">{children}</main>
          <Footer />
          <Toaster richColors />
        </ThemeProvider>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', () => {
                  navigator.serviceWorker.register('/sw.js').catch(console.error);
                });
              }
            `,
          }}
        />
      </body>
    </html>
  );
}
