import logging
import signal
import time
from pathlib import Path
from types import FrameType

from worker.config import get_worker_settings

logger = logging.getLogger("convo-glasses-worker")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

HEALTH_FILE = Path("/tmp/worker_healthy")


class JobWorker:
    def __init__(self) -> None:
        self.settings = get_worker_settings()
        self.running = True

    def signal_handler(self, signum: int, frame: FrameType | None) -> None:
        logger.info("Received signal %d, initiating graceful shutdown...", signum)
        self.running = False
        if HEALTH_FILE.exists():
            HEALTH_FILE.unlink(missing_ok=True)

    def update_health(self) -> None:
        try:
            HEALTH_FILE.write_text(str(int(time.time())))
        except OSError as err:
            logger.warning("Failed to update health file: %s", err)

    def process_one_batch(self) -> int:
        """Poll and process messages from SQS. Returns count of processed messages."""
        # Milestone M0 scaffold: ready for M2 resume parsing jobs
        self.update_health()
        return 0

    def run(self) -> None:
        logger.info("Starting Convo Glasses Worker (env=%s)", self.settings.ENVIRONMENT)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.update_health()
        while self.running:
            self.process_one_batch()
            time.sleep(1)

        logger.info("Worker stopped successfully.")


def main() -> None:
    worker = JobWorker()
    worker.run()


if __name__ == "__main__":
    main()
