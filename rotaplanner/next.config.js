/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/backend/:slug',
        destination: 'http://localhost:8000/:slug', // Matched parameters can be used in the destination
      }
    ]
  },
}

module.exports = nextConfig
