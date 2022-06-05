/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/backend/:path*',
        destination: 'http://localhost:8000/backend/:path*', // Matched parameters can be used in the destination
      },
      {
        source: '/socket.io',
        destination:'http://localhost:8000/socket.io'
      }
    ]
  },
}

module.exports = nextConfig
