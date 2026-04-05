import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000",
  },
  allowedDevOrigins: ["172.20.208.1"],
  turbopack: {
    root: path.resolve(process.cwd()),
  },
};

export default nextConfig;
