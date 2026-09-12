'use client';

import { useEffect, useRef, useState } from 'react';
import NextImage from 'next/image';
import { usePathname } from 'next/navigation';

const loadingScenes = [
  {
    image: '/akuru-loading/akuru-loading-reader.png',
    message: 'Opening the next chapter…',
    alt: 'AKURU BOT reading',
  },
  {
    image: '/akuru-loading/akuru-loading-runner.png',
    message: 'On the way…',
    alt: 'AKURU BOT running',
  },
  {
    image: '/akuru-loading/akuru-loading-idea.png',
    message: 'Getting things ready…',
    alt: 'AKURU BOT holding a bright idea',
  },
  {
    image: '/akuru-loading/akuru-loading-laptop.png',
    message: 'Preparing your learning space…',
    alt: 'AKURU BOT working on a laptop',
  },
  {
    image: '/akuru-loading/akuru-loading-question.png',
    message: 'Finding the right place…',
    alt: 'AKURU BOT thinking',
  },
] as const;

export function RouteLoadingOverlay() {
  const pathname = usePathname();
  const [visible, setVisible] = useState(false);
  const [sceneIndex, setSceneIndex] = useState(0);
  const previousScene = useRef(0);
  const timeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    for (const scene of loadingScenes) {
      const image = new Image();
      image.src = scene.image;
    }
  }, []);

  useEffect(() => {
    if (!visible) return;
    timeout.current = setTimeout(() => setVisible(false), 450);
    return () => {
      if (timeout.current) clearTimeout(timeout.current);
    };
  }, [pathname]);

  useEffect(() => {
    const show = (minimumDuration = 650) => {
      if (timeout.current) clearTimeout(timeout.current);
      const offset = 1 + Math.floor(Math.random() * (loadingScenes.length - 1));
      const next = (previousScene.current + offset) % loadingScenes.length;
      previousScene.current = next;
      setSceneIndex(next);
      setVisible(true);
      timeout.current = setTimeout(() => setVisible(false), minimumDuration);
    };

    const onClick = (event: MouseEvent) => {
      if (
        event.defaultPrevented ||
        event.button !== 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.shiftKey ||
        event.altKey
      )
        return;
      const link = (event.target as Element | null)?.closest<HTMLAnchorElement>(
        'a[href]',
      );
      if (!link || link.target === '_blank' || link.hasAttribute('download'))
        return;
      const destination = new URL(link.href, window.location.href);
      if (
        destination.origin !== window.location.origin ||
        destination.pathname === window.location.pathname
      )
        return;
      show(1200);
    };
    const onHashChange = () => {
      if (window.location.pathname === '/') show();
    };

    document.addEventListener('click', onClick, true);
    window.addEventListener('hashchange', onHashChange);
    return () => {
      document.removeEventListener('click', onClick, true);
      window.removeEventListener('hashchange', onHashChange);
      if (timeout.current) clearTimeout(timeout.current);
    };
  }, []);

  const scene = loadingScenes[sceneIndex];
  return (
    <div className="route-loader" data-visible={visible} aria-hidden={!visible}>
      <div className="route-loader-card" role="status" aria-live="polite">
        <NextImage src={scene.image} alt={scene.alt} width={210} height={210} />
        <div className="route-loader-dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <strong>{scene.message}</strong>
        <small>A little progress, every day.</small>
      </div>
    </div>
  );
}
