import logging
import signal
import time

from app.queue import QueueUnavailable, get_document_queue
from app.services.document_processing import process_job, recover_queued_jobs


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("akuru.document-worker")
running = True


def stop(_signum, _frame) -> None:
    global running
    running = False


def main() -> None:
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    queue = get_document_queue()
    while running:
        try:
            recovered = recover_queued_jobs(queue)
            if recovered:
                logger.info("Recovered %s queued document job(s)", recovered)
            break
        except QueueUnavailable as exc:
            logger.warning("Waiting for Redis: %s", exc)
            time.sleep(5)
    while running:
        try:
            job_id = queue.dequeue(timeout_seconds=5)
            if job_id:
                logger.info("Document job %s finished with state %s", job_id, process_job(job_id))
        except QueueUnavailable as exc:
            logger.warning("Redis unavailable: %s", exc)
            time.sleep(5)
        except Exception:
            logger.exception("Document worker recovered from an unexpected job failure")


if __name__ == "__main__":
    main()
