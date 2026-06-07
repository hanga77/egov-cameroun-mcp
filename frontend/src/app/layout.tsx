import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "eGov Cameroun — Assistant IA",
  description: "Plateforme IA pour les services gouvernementaux du Cameroun : DGI, CNPS, statistiques.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="h-screen flex flex-col overflow-hidden">{children}</body>
    </html>
  );
}
