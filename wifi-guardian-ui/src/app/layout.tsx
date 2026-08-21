import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'WiFi AC Guardian',
  description: 'High-Speed Wi-Fi 5+ Protection Service for Windows 11',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0D0F10] text-[#F2F4F7] antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
