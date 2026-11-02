'use client';

import { Fragment, useState, type ReactNode } from 'react';
import Image from 'next/image';
import { Bot, BookOpen, ChevronDown } from 'lucide-react';

const fallbackAvatar = '/akuru-bots/akuru-bot-say.png';

export function TutorChatAvatar({
  src,
  name,
  size = 40,
}: {
  src?: string;
  name: string;
  size?: number;
}) {
  const [failedSource, setFailedSource] = useState<string | null>(null);
  const candidate = src || fallbackAvatar;
  const imageSource = failedSource === candidate ? fallbackAvatar : candidate;
  const [fallbackFailed, setFallbackFailed] = useState(false);
  return (
    <span className="tutor-chat-avatar" style={{ width: size, height: size }}>
      {fallbackFailed && failedSource === candidate ? (
        <span>
          <Bot size={size * 0.55} aria-hidden="true" />
          <span className="sr-only">{name} avatar</span>
        </span>
      ) : (
        <Image
          unoptimized
          width={size}
          height={size}
          src={`${imageSource}${imageSource.includes('?') ? '&' : '?'}v=20261020-uncropped`}
          alt={`${name} avatar`}
          onError={() => {
            if (imageSource === fallbackAvatar) setFallbackFailed(true);
            setFailedSource(candidate);
          }}
        />
      )}
    </span>
  );
}

function inlineText(text: string): ReactNode {
  // Deliberately small, text-only formatting: never interpret HTML or model links.
  return text
    .split(/(\*\*[^*\n]+\*\*|`[^`\n]+`)/g)
    .map((part, index) =>
      part.startsWith('**') && part.endsWith('**') ? (
        <strong key={index}>{part.slice(2, -2)}</strong>
      ) : part.startsWith('`') && part.endsWith('`') ? (
        <code key={index}>{part.slice(1, -1)}</code>
      ) : (
        <Fragment key={index}>{part}</Fragment>
      ),
    );
}

export function TutorMessageContent({
  content,
  formatted = true,
}: {
  content: string;
  formatted?: boolean;
}) {
  if (!formatted)
    return (
      <div className="tutor-message-copy">
        <p>{content}</p>
      </div>
    );
  const groups: {
    kind: 'paragraph' | 'ordered' | 'unordered';
    lines: string[];
    start?: number;
  }[] = [];
  for (const line of content.replace(/\r\n?/g, '\n').split('\n')) {
    if (!line.trim()) {
      groups.push({ kind: 'paragraph', lines: [] });
      continue;
    }
    const ordered = line.match(/^\s*(\d+)[.)]\s+(.+)$/);
    const unordered = line.match(/^\s*[-*•]\s+(.+)$/);
    const kind = ordered ? 'ordered' : unordered ? 'unordered' : 'paragraph';
    const value =
      ordered?.[2] || unordered?.[1] || line.replace(/^#{1,4}\s+/, '');
    const last = groups.at(-1);
    if (last?.kind === kind && last.lines.length) last.lines.push(value);
    else
      groups.push({
        kind,
        lines: [value],
        start: ordered ? Number(ordered[1]) : undefined,
      });
  }
  return (
    <div className="tutor-message-copy">
      {groups
        .filter((group) => group.lines.length)
        .map((group, index) =>
          group.kind === 'ordered' ? (
            <ol key={index} start={group.start}>
              {group.lines.map((line, i) => (
                <li key={i}>{inlineText(line)}</li>
              ))}
            </ol>
          ) : group.kind === 'unordered' ? (
            <ul key={index}>
              {group.lines.map((line, i) => (
                <li key={i}>{inlineText(line)}</li>
              ))}
            </ul>
          ) : (
            <p key={index}>{inlineText(group.lines.join('\n'))}</p>
          ),
        )}
    </div>
  );
}

export function TutorTextbookEvidence({
  sourceCount,
  visualCount,
  children,
}: {
  sourceCount: number;
  visualCount: number;
  children: ReactNode;
}) {
  if (!sourceCount && !visualCount) return null;
  return (
    <details className="tutor-textbook-evidence">
      <summary>
        <BookOpen size={17} aria-hidden="true" />
        <span>
          <strong>Textbook references</strong>
          <small>
            {sourceCount} {sourceCount === 1 ? 'source' : 'sources'}
            {visualCount
              ? ` · ${visualCount} visual ${visualCount === 1 ? 'aid' : 'aids'}`
              : ''}
          </small>
        </span>
        <ChevronDown
          size={17}
          className="tutor-evidence-chevron"
          aria-hidden="true"
        />
      </summary>
      <div className="agent-evidence stack">{children}</div>
    </details>
  );
}
