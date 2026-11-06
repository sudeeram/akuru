import type { Metadata } from 'next';
import { RouteLoadingOverlay } from '@/components/route-loading-overlay';
import './globals.css';
import './ui-adoption.css';
import './landing.css';
export const metadata: Metadata = {
  title: 'AKURU · Small steps. Lasting understanding.',
  description:
    'Build understanding and confidence with AKURU: AI tutoring, reviewed flashcards, digital textbooks and connected support for students and families.',
  icons: {
    icon: [{ url: '/favicon-friendly-bot.png?v=2', type: 'image/png' }],
  },
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
