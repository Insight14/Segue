from unittest.mock import patch

from worker.config import get_worker_settings
from worker.main import JobWorker, main


def test_worker_settings() -> None:
    settings = get_worker_settings()
    assert settings.ENVIRONMENT in ["local", "test", "production"]
    assert settings.SQS_QUEUE_URL != ""


def test_worker_batch() -> None:
    worker = JobWorker()
    count = worker.process_one_batch()
    assert count == 0


def test_worker_shutdown_signal() -> None:
    worker = JobWorker()
    assert worker.running is True
    worker.signal_handler(15, None)
    assert worker.running is False


def test_worker_run_and_stop() -> None:
    worker = JobWorker()

    # Trigger one loop then exit
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
