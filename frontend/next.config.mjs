/**
 * next.config.mjs — Next.js build/runtime configuration.
 *
 * We allow remote images from BookMyShow's CDN so <img> posters load. Next is
 * strict about external image hosts for security/perf; we whitelist the CDN.
 * (We use plain <img> tags here for simplicity, so this is mostly future-proofing.)
 */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "assets-in.bmscdn.com" },
      { protocol: "https", hostname: "assets-in-gm.bmscdn.com" },
    ],
  },
};

export default nextConfig;
