type LearningContext = {
  sessionRef: string;
  status: string;
  activeTopic: { topicRef: string };
};

/** Profile switches retain learning context; new sessions/topics do not. */
export function tutorLearningContextChanged(
  previous: LearningContext | null,
  next: LearningContext,
): boolean {
  return (
    next.status !== 'active' ||
    previous?.sessionRef !== next.sessionRef ||
    previous.activeTopic.topicRef !== next.activeTopic.topicRef
  );
}
