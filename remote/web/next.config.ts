import type { NextConfig } from "next";

const gatewayOrigin = process.env.GATEWAY_ORIGIN ?? "http://127.0.0.1:8790";
// In production the whole local panel is served through the gateway at the same URLs (`/p/...`, `/flow`, ...),
// so its root-relative links keep working. The remote control stays at `/remote`. Off by default (tests, dev).
const panelProxy = process.env.PANEL_PROXY === "1";
const panelPaths = [
  "/p/:path*", "/plans", "/plans/:path*", "/events", "/now", "/flow", "/flow/:path*", "/metrics", "/metrics/:path*",
  "/learnings", "/static/:path*", "/live", "/go/:path*", "/__panel/:path*",
];

const nextConfig: NextConfig = {
  async rewrites() {
    const api = { source: "/api/:path*", destination: `${gatewayOrigin}/api/:path*` };
    if (!panelProxy) return [api];
    return {
      beforeFiles: [{ source: "/", destination: `${gatewayOrigin}/__panel_root` }],
      afterFiles: [api],
      fallback: panelPaths.map((source) => ({ source, destination: `${gatewayOrigin}${source}` })),
    };
  },
};

export default nextConfig;
