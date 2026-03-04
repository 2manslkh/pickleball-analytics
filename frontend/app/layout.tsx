import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "🏓 Pickleball Analytics",
  description: "AI-powered pickleball match analysis",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
