/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Add experimental flag if needed for older Next.js versions, 
  // but transpilePackages is stable now.
  // experimental: {
  //   esmExternals: 'loose', // or true, depending on version/needs
  // },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*', // Proxy to Backend
      },
    ]
  },
  // Your other configurations...
  // Example: If you had output: 'export' for static builds, keep it
  // output: 'export', 
}

module.exports = nextConfig 