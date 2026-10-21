import type { NextConfig } from "next";

const gatewayOrigin = process.env.GATEWAY_ORIGIN ?? "http://127.0.0.1:8790";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${gatewayOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
