import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sarjy — your voice assistant",
  description: "Talks, remembers, checks the weather. Built for Sarj.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
