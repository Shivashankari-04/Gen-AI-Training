import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aura - Enterprise AI Financial Intelligence",
  description: "AI-powered expense analytics and intelligence platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
