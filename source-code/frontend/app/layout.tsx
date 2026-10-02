import type { Metadata } from 'next';
import { RouteLoadingOverlay } from '@/components/route-loading-overlay';
import './globals.css';
export const metadata: Metadata = {
  title: 'AKURU · Family learning',
  description: 'AKURU is your family’s space to learn, practise and grow.',
  icons: { icon: [{ url: '/favicon.svg?v=akuru-bot', type: 'image/svg+xml' }] },
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
        <RouteLoadingOverlay />
      </body>
    </html>
  );
}
