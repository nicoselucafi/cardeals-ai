/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      // Allow all HTTPS images — dealer sites use too many different CDNs/hosts
      // to whitelist individually (DealerInspire, DealerOn, Jazel, S3, WordPress, etc.)
      { protocol: "https", hostname: "**" },
    ],
  },
};

export default nextConfig;
