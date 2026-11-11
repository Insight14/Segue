import json
from unittest.mock import MagicMock, patch

from worker.config import get_worker_settings
from worker.main import JobWorker, main


def test_worker_settings() -> None:
    settings = get_worker_settings()
    assert settings.ENVIRONMENT in ["local", "test", "production"]
    assert settings.SQS_QUEUE_URL != ""


def test_worker_batch_empty() -> None:
    worker = JobWorker()
    worker._sqs = MagicMock()
    worker._sqs.receive_message.return_value = {"Messages": []}

    count = worker.process_one_batch()
    assert count == 0


def test_worker_batch_processes_sqs_message() -> None:
    worker = JobWorker()
    mock_sqs = MagicMock()
    mock_sqs.receive_message.return_value = {
        "Messages": [
            {
                "MessageId": "msg-123",
                "ReceiptHandle": "receipt-123",
                "Body": json.dumps(
                    {
                        "job_type": "parse_resume",
                        "document_id": "00000000-0000-0000-0000-000000000001",
                        "user_id": "00000000-0000-0000-0000-000000000002",
                        "s3_key": "some/path.pdf",
                    }
                ),
            }
        ]
    }
    worker._sqs = mock_sqs

    with patch("worker.main.process_document_job", return_value=True) as mock_proc:
        count = worker.process_one_batch()
        assert count == 1
        mock_proc.assert_called_once()
        mock_sqs.delete_message.assert_called_once_with(
            QueueUrl=worker.settings.SQS_QUEUE_URL,
            ReceiptHandle="receipt-123",
        )


def test_worker_shutdown_signal() -> None:
    worker = JobWorker()
    assert worker.running is True
    worker.signal_handler(15, None)
    assert worker.running is False


def test_worker_run_and_stop() -> None:
    worker = JobWorker()

    def stop_worker() -> int:
        worker.running = False
        return 0

    worker.process_one_batch = stop_worker  # type: ignore[method-assign]
    with patch("time.sleep", return_value=None):
        worker.run()
    assert worker.running is False


def test_worker_main_entry() -> None:
    with patch.object(JobWorker, "run", return_value=None) as mock_run:
        main()
        mock_run.assert_called_once()
