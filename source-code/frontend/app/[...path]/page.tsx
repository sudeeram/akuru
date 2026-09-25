import { notFound } from 'next/navigation';
import AkuruApplication from '../page';
import { isApplicationPath } from '@/lib/routes';

export default async function RoutedApplication({ params }: { params: Promise<{ path: string[] }> }) {
  const segments = (await params).path;
  const pathname = `/${segments.map(encodeURIComponent).join('/')}`;
  if (!isApplicationPath(pathname)) notFound();
  return <AkuruApplication />;
}
