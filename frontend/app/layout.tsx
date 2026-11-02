import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Genesis — Business Decoding & Replication Engine",
  description:
    "Zero-cost, open-source intelligence platform: decode any company or raw idea into structure, features, compliance, pricing, friction, failure modes, and an execution playbook.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
