import asyncio
import json
import logging
import signal
import time
from pathlib import Path
from types import FrameType
from typing import Any

import boto3
from botocore.config import Config

from worker.config import get_worker_settings
from worker.processor import process_document_job

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
        self._sqs: Any = None

    @property
    def sqs(self) -> Any:
        if self._sqs is None:
            endpoint = self.settings.SQS_ENDPOINT_URL if self.settings.SQS_ENDPOINT_URL else None
            self._sqs = boto3.client(
                "sqs",
                endpoint_url=endpoint,
                aws_access_key_id=self.settings.S3_ACCESS_KEY_ID,
                aws_secret_access_key=self.settings.S3_SECRET_ACCESS_KEY,
                region_name=self.settings.SQS_REGION,
                config=Config(signature_version="s3v4"),
            )
        return self._sqs

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
        self.update_health()
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.settings.SQS_QUEUE_URL,
                MaxNumberOfMessages=self.settings.MAX_MESSAGES_PER_POLL,
                WaitTimeSeconds=min(self.settings.POLL_WAIT_TIME_SECONDS, 5),
            )
            messages = response.get("Messages", [])
            if not messages:
                return 0

            count = 0
            for msg in messages:
                receipt_handle = msg.get("ReceiptHandle")
                body = msg.get("Body", "{}")
                try:
                    payload = json.loads(body)
                    job_type = payload.get("job_type")
                    if job_type == "parse_resume":
                        asyncio.run(process_document_job(payload))

                    # Delete message after successful processing
                    if receipt_handle:
                        self.sqs.delete_message(
                            QueueUrl=self.settings.SQS_QUEUE_URL,
                            ReceiptHandle=receipt_handle,
                        )
                    count += 1
                except Exception as err:
                    logger.error("Error processing message %s: %s", msg.get("MessageId"), err)

            return count
        except Exception as err:
            logger.debug("SQS polling check (idle or connecting): %s", err)
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
