/** @type {import('next').NextConfig} */
// NEXT_EXPORT=1 builds a fully static bundle (out/) for single-port hosting —
// the cloud demo serves it from FastAPI itself, same origin as /api, so no
// proxy or CORS is ever involved. Local runs keep the normal server build.
const nextConfig =
  process.env.NEXT_EXPORT === "1"
    ? { reactStrictMode: true, output: "export", images: { unoptimized: true } }
    : { reactStrictMode: true };

export default nextConfig;
