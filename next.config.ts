import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",

  // Turbopack configuration (top-level, stable in Next.js 15)
  turbopack: {
    // Custom loader rules can go here if needed
    rules: {},
  },

  images: {
    remotePatterns: [
      { protocol: "https", hostname: "upload.wikimedia.org" },
      { protocol: "https", hostname: "commons.wikimedia.org" },
      { protocol: "https", hostname: "picsum.photos" },
      { protocol: "https", hostname: "*.supabase.co" },
    ],
  },

  async headers() {
    return [
      {
        source: "/sw.js",
        headers: [
          { key: "Cache-Control", value: "no-cache" },
          { key: "Service-Worker-Allowed", value: "/" },
        ],
      },
    ];
  },

  async rewrites() {
    return [
      { source: "/robots.txt", destination: "/api/robots" },
    ];
  },
};

export default nextConfig;
