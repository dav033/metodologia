import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";

const manrope = localFont({
  src: "../../public/fonts/Manrope-400-latin.woff2",
  variable: "--font-sans",
  display: "swap",
  weight: "400",
});

const jetBrainsMono = localFont({
  src: "../../public/fonts/JetBrainsMono-400-latin.woff2",
  variable: "--font-mono",
  display: "swap",
  weight: "400",
});

export const metadata: Metadata = {
  title: "Flow Remote",
  description: "Panel remoto de ejecuciones de Flow.",
  applicationName: "Flow Remote",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "Flow Remote",
    statusBarStyle: "black-translucent",
  },
  icons: {
    icon: "/icon.svg",
    apple: "/apple-icon.svg",
  },
};

export const viewport: Viewport = {
  themeColor: "#1e1e2e",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es" className={`${manrope.variable} ${jetBrainsMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
