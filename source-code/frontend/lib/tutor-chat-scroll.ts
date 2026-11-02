/** Scroll the bounded transcript separately from the page to avoid competing
 * smooth-scroll animations in nested containers. */
export function scrollTutorTurnIntoView(
  turn: HTMLElement,
  reducedMotion: boolean,
) {
  const list = turn.closest<HTMLElement>('.tutor-turn-list');
  if (list) {
    const top = Math.max(
      0,
      list.scrollTop +
        turn.getBoundingClientRect().top -
        list.getBoundingClientRect().top -
        16,
    );
    list.scrollTo({ top, behavior: 'instant' });
    list.scrollIntoView({
      block: 'nearest',
      behavior: reducedMotion ? 'instant' : 'smooth',
    });
  } else {
    turn.scrollIntoView({
      block: 'start',
      behavior: reducedMotion ? 'instant' : 'smooth',
    });
  }
}
