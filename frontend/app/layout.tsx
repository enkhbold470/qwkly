import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "qwkly",
  description:
    "Autonomous short-form video agent UI with human approvals and backend placeholders."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
