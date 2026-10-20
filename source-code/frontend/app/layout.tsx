import type { Metadata } from 'next';
import { RouteLoadingOverlay } from '@/components/route-loading-overlay';
import './globals.css';
import './ui-adoption.css';
export const metadata: Metadata = {
  title: 'AKURU · Family learning',
  description: 'AKURU is your family’s space to learn, practise and grow.',
  icons: { icon: [{ url: '/favicon-friendly-bot.png?v=2', type: 'image/png' }] },
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
