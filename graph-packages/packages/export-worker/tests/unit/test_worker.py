"""Unit tests for K8s Export Worker (ADR-025).

Tests the stateless database polling architecture:
- Three-phase loop: Claim -> Submit -> Poll
- Starburst client_tags for resource group routing
- Database-persisted polling state
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from export_worker.clients.starburst import QueryPollResult, QuerySubmissionResult
from export_worker.models import ExportJob, ExportJobStatus, SnapshotJobsResult
from export_worker.worker import ExportWorker, configure_logging


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_logging_json_format(self) -> None:
        """Test that JSON format configures JSON processors."""
        with patch("export_worker.worker.structlog.configure") as mock_configure:
            configure_logging(log_format="json", log_level="INFO")

            mock_configure.assert_called_once()
            call_kwargs = mock_configure.call_args.kwargs
            processors = call_kwargs["processors"]

            # Check that JSONRenderer is in processors
            from structlog.processors import JSONRenderer
            assert any((isinstance(p, type) and p == JSONRenderer) or isinstance(p, JSONRenderer)
                      for p in processors)

    def test_configure_logging_console_format(self) -> None:
        """Test that console format configures console renderer."""
        with patch("export_worker.worker.structlog.configure") as mock_configure:
            configure_logging(log_format="console", log_level="DEBUG")

            mock_configure.assert_called_once()
            call_kwargs = mock_configure.call_args.kwargs
            processors = call_kwargs["processors"]

            # Check that ConsoleRenderer is in processors
            from structlog.dev import ConsoleRenderer
            assert any((isinstance(p, type) and p == ConsoleRenderer) or isinstance(p, ConsoleRenderer)
                      for p in processors)

    def test_configure_logging_sets_log_level(self) -> None:
        """Test that log level is correctly set."""
        import logging

        with patch("export_worker.worker.structlog.configure") as mock_configure, \
             patch("export_worker.worker.structlog.make_filtering_bound_logger") as mock_filter:

            configure_logging(log_format="json", log_level="WARNING")

            # Verify that make_filtering_bound_logger was called with WARNING level
            mock_filter.assert_called_once_with(logging.WARNING)

    def test_configure_logging_handles_invalid_level(self) -> None:
        """Test that invalid log level defaults to INFO."""
        import logging

        with patch("export_worker.worker.structlog.configure") as mock_configure, \
             patch("export_worker.worker.structlog.make_filtering_bound_logger") as mock_filter:

            configure_logging(log_format="json", log_level="INVALID")

            # Should default to INFO
            mock_filter.assert_called_once_with(logging.INFO)


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create mock settings for testing (ADR-025)."""
    settings = MagicMock()
    settings.poll_interval_seconds = 5
    settings.empty_poll_backoff_seconds = 10
    settings.claim_limit = 10
    settings.poll_limit = 10
    settings.log_format = "console"
    settings.log_level = "DEBUG"

    # Starburst config
    settings.starburst.url = "http://starburst.test"
    settings.starburst.user = "test"
    settings.starburst.password.get_secret_value.return_value = "password"
    settings.starburst.catalog = "analytics"
    settings.starburst.schema_name = "public"
    settings.starburst.request_timeout_seconds = 30
    settings.starburst.client_tags = "graph-olap-export"
    settings.starburst.source = "graph-olap-export-worker"

    # Control plane config
    settings.control_plane.url = "http://control-plane.test"
    settings.control_plane.timeout_seconds = 30
    settings.control_plane.max_retries = 3
    settings.control_plane.internal_api_key = None

    # GCS config
    settings.gcs.project = "test-project"

    return settings


class TestExportWorkerInit:
    """Tests for ExportWorker initialization."""

    def test_init_sets_worker_id_from_hostname(self, mock_settings: MagicMock) -> None:
        """Test that worker_id is set from HOSTNAME env var."""
        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient"), \
             patch("export_worker.worker.GCSClient"), \
             patch.dict("os.environ", {"HOSTNAME": "export-worker-abc123"}):
            worker = ExportWorker(mock_settings)
            assert worker._worker_id == "export-worker-abc123"

    def test_init_creates_shutdown_event(self, mock_settings: MagicMock) -> None:
        """Test that shutdown event is created."""
        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient"), \
             patch("export_worker.worker.GCSClient"):
            worker = ExportWorker(mock_settings)
            assert isinstance(worker._shutdown_event, asyncio.Event)
            assert not worker._shutdown_event.is_set()


class TestExportWorkerShutdown:
    """Tests for ExportWorker shutdown handling."""

    def test_request_shutdown_sets_event(self, mock_settings: MagicMock) -> None:
        """Test that request_shutdown sets the shutdown event."""
        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient"), \
             patch("export_worker.worker.GCSClient"):
            worker = ExportWorker(mock_settings)
            assert not worker.is_shutting_down

            worker.request_shutdown()

            assert worker.is_shutting_down


class TestExportWorkerClaimPhase:
    """Tests for the claim phase."""

    @pytest.mark.asyncio
    async def test_claim_phase_returns_claimed_jobs(
        self,
        mock_settings: MagicMock,
        sample_export_jobs: list[ExportJob],
    ) -> None:
        """Test that claim phase returns claimed jobs."""
        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.claim_export_jobs.return_value = sample_export_jobs

            worker = ExportWorker(mock_settings)
            claimed = await worker._claim_phase()

            assert len(claimed) == 2
            mock_cp.claim_export_jobs.assert_called_once_with(
                worker_id=worker._worker_id,
                limit=mock_settings.claim_limit,
            )

    @pytest.mark.asyncio
    async def test_claim_phase_returns_empty_on_error(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test that claim phase returns empty list on error."""
        from export_worker.exceptions import ControlPlaneError

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.claim_export_jobs.side_effect = ControlPlaneError("Connection failed")

            worker = ExportWorker(mock_settings)
            claimed = await worker._claim_phase()

            assert claimed == []


class TestExportWorkerSubmitPhase:
    """Tests for the submit phase."""

    @pytest.mark.asyncio
    async def test_submit_phase_submits_jobs(
        self,
        mock_settings: MagicMock,
        sample_export_jobs: list[ExportJob],
    ) -> None:
        """Test that submit phase submits jobs to Starburst."""
        with patch("export_worker.worker.StarburstClient") as mock_starburst_cls, \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_starburst = mock_starburst_cls.from_config.return_value
            mock_starburst.submit_unload_async = AsyncMock(
                return_value=QuerySubmissionResult(
                    query_id="query-123",
                    next_uri="http://starburst/v1/query/123/1",
                )
            )
            mock_cp = mock_cp_cls.from_config.return_value

            worker = ExportWorker(mock_settings)
            await worker._submit_phase(sample_export_jobs)

            assert mock_starburst.submit_unload_async.call_count == 2
            assert mock_cp.update_export_job.call_count == 2

    @pytest.mark.asyncio
    async def test_submit_phase_marks_failed_on_starburst_error(
        self,
        mock_settings: MagicMock,
        sample_export_jobs: list[ExportJob],
    ) -> None:
        """Test that submit phase marks job as failed on Starburst error."""
        from export_worker.exceptions import StarburstError

        with patch("export_worker.worker.StarburstClient") as mock_starburst_cls, \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_starburst = mock_starburst_cls.from_config.return_value
            mock_starburst.submit_unload_async = AsyncMock(
                side_effect=StarburstError("Connection refused")
            )
            mock_cp = mock_cp_cls.from_config.return_value

            worker = ExportWorker(mock_settings)
            await worker._submit_phase([sample_export_jobs[0]])

            # Should update job to failed
            mock_cp.update_export_job.assert_called_once()
            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert call_kwargs["status"] == ExportJobStatus.FAILED
            assert "Connection refused" in call_kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_submit_phase_stops_on_shutdown(
        self,
        mock_settings: MagicMock,
        sample_export_jobs: list[ExportJob],
    ) -> None:
        """Test that submit phase stops when shutdown is requested."""
        with patch("export_worker.worker.StarburstClient") as mock_starburst_cls, \
             patch("export_worker.worker.ControlPlaneClient"), \
             patch("export_worker.worker.GCSClient"):
            mock_starburst = mock_starburst_cls.from_config.return_value

            worker = ExportWorker(mock_settings)
            worker.request_shutdown()

            await worker._submit_phase(sample_export_jobs)

            # Should not submit any jobs
            mock_starburst.submit_unload_async.assert_not_called()


class TestExportWorkerPollPhase:
    """Tests for the poll phase."""

    @pytest.mark.asyncio
    async def test_poll_phase_polls_starburst(
        self,
        mock_settings: MagicMock,
        sample_submitted_export_job: ExportJob,
    ) -> None:
        """Test that poll phase polls Starburst for job status."""
        with patch("export_worker.worker.StarburstClient") as mock_starburst_cls, \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient") as mock_gcs_cls:
            mock_starburst = mock_starburst_cls.from_config.return_value
            mock_starburst.poll_query_async = AsyncMock(
                return_value=QueryPollResult(
                    state="FINISHED",
                    next_uri=None,
                    error_message=None,
                )
            )
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_pollable_export_jobs.return_value = [sample_submitted_export_job]
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True,
                any_failed=False,
                node_counts={"Customer": 1000},
                edge_counts={},
                total_size=1024,
            )
            mock_gcs = mock_gcs_cls.from_config.return_value
            mock_gcs.count_parquet_rows.return_value = (1000, 1024)

            worker = ExportWorker(mock_settings)
            polled = await worker._poll_phase()

            assert len(polled) == 1
            mock_starburst.poll_query_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_poll_phase_schedules_next_poll_when_running(
        self,
        mock_settings: MagicMock,
        sample_submitted_export_job: ExportJob,
    ) -> None:
        """Test that poll phase schedules next poll when query still running."""
        with patch("export_worker.worker.StarburstClient") as mock_starburst_cls, \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_starburst = mock_starburst_cls.from_config.return_value
            mock_starburst.poll_query_async = AsyncMock(
                return_value=QueryPollResult(
                    state="RUNNING",
                    next_uri="http://starburst/v1/query/123/2",
                    error_message=None,
                )
            )
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_pollable_export_jobs.return_value = [sample_submitted_export_job]

            worker = ExportWorker(mock_settings)
            await worker._poll_phase()

            # Should update job with new next_poll_at
            mock_cp.update_export_job.assert_called_once()
            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert "next_poll_at" in call_kwargs
            assert call_kwargs["poll_count"] == 2

    @pytest.mark.asyncio
    async def test_poll_phase_marks_failed_on_query_failure(
        self,
        mock_settings: MagicMock,
        sample_submitted_export_job: ExportJob,
    ) -> None:
        """Test that poll phase marks job as failed when query fails."""
        with patch("export_worker.worker.StarburstClient") as mock_starburst_cls, \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_starburst = mock_starburst_cls.from_config.return_value
            mock_starburst.poll_query_async = AsyncMock(
                return_value=QueryPollResult(
                    state="FAILED",
                    next_uri=None,
                    error_message="Query execution failed",
                )
            )
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_pollable_export_jobs.return_value = [sample_submitted_export_job]

            worker = ExportWorker(mock_settings)
            await worker._poll_phase()

            mock_cp.update_export_job.assert_called_once()
            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert call_kwargs["status"] == ExportJobStatus.FAILED
            assert "Query execution failed" in call_kwargs["error_message"]


# =============================================================================
# SNAPSHOT TESTS DISABLED
# These tests are commented out as snapshot functionality has been disabled.
# =============================================================================
# class TestExportWorkerSnapshotFinalization:
#     """Tests for snapshot finalization."""
#
#     @pytest.mark.asyncio
#     async def test_finalize_snapshot_success(
#         self,
#         mock_settings: MagicMock,
#     ) -> None:
#         """Test snapshot finalization when all jobs succeed."""
#         with patch("export_worker.worker.StarburstClient"), \
#              patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
#              patch("export_worker.worker.GCSClient"):
#             mock_cp = mock_cp_cls.from_config.return_value
#             mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
#                 all_complete=True,
#                 any_failed=False,
#                 node_counts={"Customer": 1000},
#                 edge_counts={"PURCHASED": 500},
#                 total_size=2048,
#             )
#
#             worker = ExportWorker(mock_settings)
#
#             import structlog
#             log = structlog.get_logger()
#
#             await worker._check_snapshot_complete(123, log)
#
#             mock_cp.finalize_snapshot.assert_called_once()
#             call_kwargs = mock_cp.finalize_snapshot.call_args.kwargs
#             assert call_kwargs["success"] is True
#             assert call_kwargs["node_counts"] == {"Customer": 1000}
#             assert call_kwargs["edge_counts"] == {"PURCHASED": 500}
#             assert call_kwargs["size_bytes"] == 2048
#
#     @pytest.mark.asyncio
#     async def test_finalize_snapshot_failure(
#         self,
#         mock_settings: MagicMock,
#     ) -> None:
#         """Test snapshot finalization when some jobs fail."""
#         with patch("export_worker.worker.StarburstClient"), \
#              patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
#              patch("export_worker.worker.GCSClient"):
#             mock_cp = mock_cp_cls.from_config.return_value
#             mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
#                 all_complete=True,
#                 any_failed=True,
#                 first_error="Query execution failed",
#                 node_counts={},
#                 edge_counts={},
#                 total_size=0,
#             )
#
#             worker = ExportWorker(mock_settings)
#
#             import structlog
#             log = structlog.get_logger()
#
#             await worker._check_snapshot_complete(123, log)
#
#             mock_cp.finalize_snapshot.assert_called_once()
#             call_kwargs = mock_cp.finalize_snapshot.call_args.kwargs
#             assert call_kwargs["success"] is False
#             assert "Query execution failed" in call_kwargs["error_message"]
#
#     @pytest.mark.asyncio
#     async def test_finalize_snapshot_not_complete(
#         self,
#         mock_settings: MagicMock,
#     ) -> None:
#         """Test that finalization is skipped when jobs still running."""
#         with patch("export_worker.worker.StarburstClient"), \
#              patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
#              patch("export_worker.worker.GCSClient"):
#             mock_cp = mock_cp_cls.from_config.return_value
#             mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
#                 all_complete=False,
#                 any_failed=False,
#                 node_counts={},
#                 edge_counts={},
#                 total_size=0,
#             )
#
#             worker = ExportWorker(mock_settings)
#
#             import structlog
#             log = structlog.get_logger()
#
#             await worker._check_snapshot_complete(123, log)
#
#             # Should not finalize
#             mock_cp.finalize_snapshot.assert_not_called()


class TestExportWorkerSnapshotFinalization:
    """Tests for snapshot finalization."""

    @pytest.mark.asyncio
    async def test_check_snapshot_complete_success(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test snapshot finalization when all jobs succeed."""
        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True,
                any_failed=False,
                node_counts={"Customer": 1000},
                edge_counts={"PURCHASED": 500},
                total_size=2048,
            )

            worker = ExportWorker(mock_settings)

            import structlog
            log = structlog.get_logger()

            await worker._check_snapshot_complete(123, log)

            mock_cp.finalize_snapshot.assert_called_once()
            call_kwargs = mock_cp.finalize_snapshot.call_args.kwargs
            assert call_kwargs["success"] is True
            assert call_kwargs["node_counts"] == {"Customer": 1000}

    @pytest.mark.asyncio
    async def test_check_snapshot_complete_failure(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test snapshot finalization when some jobs fail."""
        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True,
                any_failed=True,
                first_error="Query execution failed",
                node_counts={},
                edge_counts={},
                total_size=0,
            )

            worker = ExportWorker(mock_settings)

            import structlog
            log = structlog.get_logger()

            await worker._check_snapshot_complete(123, log)

            mock_cp.finalize_snapshot.assert_called_once()
            call_kwargs = mock_cp.finalize_snapshot.call_args.kwargs
            assert call_kwargs["success"] is False
            assert "Query execution failed" in call_kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_check_snapshot_complete_not_done(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test that finalization is skipped when jobs still running."""
        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=False,
                any_failed=False,
            )

            worker = ExportWorker(mock_settings)

            import structlog
            log = structlog.get_logger()

            await worker._check_snapshot_complete(123, log)

            mock_cp.finalize_snapshot.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_snapshot_complete_on_cp_error(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test that CP errors are caught during snapshot check."""
        from export_worker.exceptions import ControlPlaneError

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.side_effect = ControlPlaneError("Connection lost")

            worker = ExportWorker(mock_settings)

            import structlog
            log = structlog.get_logger()

            # Should not raise
            await worker._check_snapshot_complete(123, log)


class TestExportWorkerMarkJobFailed:
    """Tests for _mark_job_failed."""

    @pytest.mark.asyncio
    async def test_mark_job_failed_updates_job_and_checks_snapshot(
        self,
        mock_settings: MagicMock,
        sample_export_jobs: list[ExportJob],
    ) -> None:
        """Test that marking a job as failed updates CP and checks snapshot."""
        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True,
                any_failed=True,
                first_error="Test error",
            )

            worker = ExportWorker(mock_settings)
            await worker._mark_job_failed(sample_export_jobs[0], "Test error")

            # Should update job status
            mock_cp.update_export_job.assert_called_once()
            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert call_kwargs["status"] == ExportJobStatus.FAILED
            assert call_kwargs["error_message"] == "Test error"

            # Should check snapshot completion
            mock_cp.get_snapshot_jobs_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_job_failed_handles_cp_error(
        self,
        mock_settings: MagicMock,
        sample_export_jobs: list[ExportJob],
    ) -> None:
        """Test that CP errors during mark_job_failed are caught."""
        from export_worker.exceptions import ControlPlaneError

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.update_export_job.side_effect = ControlPlaneError("Connection lost")

            worker = ExportWorker(mock_settings)
            # Should not raise
            await worker._mark_job_failed(sample_export_jobs[0], "Test error")


class TestExportWorkerHandleJobComplete:
    """Tests for _handle_job_complete."""

    @pytest.mark.asyncio
    async def test_handle_job_complete_counts_rows(
        self,
        mock_settings: MagicMock,
        sample_submitted_export_job: ExportJob,
    ) -> None:
        """Test that completed job counts rows and updates status."""
        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient") as mock_gcs_cls:
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True,
                any_failed=False,
                node_counts={"Customer": 500},
                edge_counts={},
                total_size=1024,
            )
            mock_gcs = mock_gcs_cls.from_config.return_value
            mock_gcs.count_parquet_rows.return_value = (500, 1024)

            worker = ExportWorker(mock_settings)

            import structlog
            log = structlog.get_logger()

            await worker._handle_job_complete(sample_submitted_export_job, log)

            mock_gcs.count_parquet_rows.assert_called_once()
            mock_cp.update_export_job.assert_called_once()
            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert call_kwargs["status"] == ExportJobStatus.COMPLETED
            assert call_kwargs["row_count"] == 500

    @pytest.mark.asyncio
    async def test_handle_job_complete_error_marks_failed(
        self,
        mock_settings: MagicMock,
        sample_submitted_export_job: ExportJob,
    ) -> None:
        """Test that errors during completion handling mark job as failed."""
        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient") as mock_gcs_cls:
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True, any_failed=True, first_error="count error",
            )
            mock_gcs = mock_gcs_cls.from_config.return_value
            mock_gcs.count_parquet_rows.side_effect = Exception("GCS unavailable")

            worker = ExportWorker(mock_settings)

            import structlog
            log = structlog.get_logger()

            await worker._handle_job_complete(sample_submitted_export_job, log)

            # Should mark job as failed
            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert call_kwargs["status"] == ExportJobStatus.FAILED


class TestExportWorkerPollJobErrors:
    """Tests for _poll_job error paths."""

    @pytest.mark.asyncio
    async def test_poll_job_missing_next_uri(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test that missing next_uri marks job as failed."""
        job = ExportJob(
            id=1, snapshot_id=123, job_type="node", entity_name="Customer",
            status=ExportJobStatus.SUBMITTED, gcs_path="gs://b/p/",
            next_uri=None, poll_count=1,
        )

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True, any_failed=True, first_error="Missing next_uri",
            )

            worker = ExportWorker(mock_settings)
            await worker._poll_job(job)

            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert call_kwargs["status"] == ExportJobStatus.FAILED
            assert "next_uri" in call_kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_poll_job_starburst_error_reschedules(
        self,
        mock_settings: MagicMock,
        sample_submitted_export_job: ExportJob,
    ) -> None:
        """Test that Starburst error reschedules the poll instead of failing."""
        from export_worker.exceptions import StarburstError

        with patch("export_worker.worker.StarburstClient") as mock_sb_cls, \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_sb = mock_sb_cls.from_config.return_value
            mock_sb.poll_query_async = AsyncMock(
                side_effect=StarburstError("Connection timeout")
            )
            mock_cp = mock_cp_cls.from_config.return_value

            worker = ExportWorker(mock_settings)
            await worker._poll_job(sample_submitted_export_job)

            # Should reschedule, not fail
            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert "next_poll_at" in call_kwargs
            assert "status" not in call_kwargs

    @pytest.mark.asyncio
    async def test_poll_job_starburst_error_reschedule_fails(
        self,
        mock_settings: MagicMock,
        sample_submitted_export_job: ExportJob,
    ) -> None:
        """Test that failure to reschedule after Starburst error is caught."""
        from export_worker.exceptions import ControlPlaneError, StarburstError

        with patch("export_worker.worker.StarburstClient") as mock_sb_cls, \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_sb = mock_sb_cls.from_config.return_value
            mock_sb.poll_query_async = AsyncMock(
                side_effect=StarburstError("Connection timeout")
            )
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.update_export_job.side_effect = ControlPlaneError("CP down")

            worker = ExportWorker(mock_settings)
            # Should not raise
            await worker._poll_job(sample_submitted_export_job)

    @pytest.mark.asyncio
    async def test_poll_job_unload_not_registered_triggers_direct_export(
        self,
        mock_settings: MagicMock,
        sample_submitted_export_job: ExportJob,
    ) -> None:
        """Test that 'not registered' error triggers direct export fallback."""
        with patch("export_worker.worker.StarburstClient") as mock_sb_cls, \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_sb = mock_sb_cls.from_config.return_value
            mock_sb.poll_query_async = AsyncMock(
                return_value=QueryPollResult(
                    state="FAILED",
                    next_uri=None,
                    error_message="Function not registered: system.unload",
                )
            )
            mock_sb.execute_and_export_async = AsyncMock(return_value=(100, 512))
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True, any_failed=False,
                node_counts={"Customer": 100}, total_size=512,
            )

            worker = ExportWorker(mock_settings)
            await worker._poll_job(sample_submitted_export_job)

            # Should have called direct export
            mock_sb.execute_and_export_async.assert_called_once()


class TestExportWorkerSubmitJobDirectExport:
    """Tests for direct export fallback."""

    @pytest.mark.asyncio
    async def test_submit_job_direct_export_success(
        self,
        mock_settings: MagicMock,
        sample_export_jobs: list[ExportJob],
    ) -> None:
        """Test successful direct export."""
        with patch("export_worker.worker.StarburstClient") as mock_sb_cls, \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_sb = mock_sb_cls.from_config.return_value
            mock_sb.execute_and_export_async = AsyncMock(return_value=(200, 1024))
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True, any_failed=False,
                node_counts={"Customer": 200}, total_size=1024,
            )

            worker = ExportWorker(mock_settings)

            import structlog
            log = structlog.get_logger()

            await worker._submit_job_direct_export(sample_export_jobs[0], log)

            mock_sb.execute_and_export_async.assert_called_once()
            # Should update job as completed
            call_args = mock_cp.update_export_job.call_args
            assert call_args.kwargs["status"] == ExportJobStatus.COMPLETED
            assert call_args.kwargs["row_count"] == 200

    @pytest.mark.asyncio
    async def test_submit_job_direct_export_starburst_error(
        self,
        mock_settings: MagicMock,
        sample_export_jobs: list[ExportJob],
    ) -> None:
        """Test direct export handles Starburst error."""
        from export_worker.exceptions import StarburstError

        with patch("export_worker.worker.StarburstClient") as mock_sb_cls, \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_sb = mock_sb_cls.from_config.return_value
            mock_sb.execute_and_export_async = AsyncMock(
                side_effect=StarburstError("Query failed")
            )
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True, any_failed=True, first_error="Query failed",
            )

            worker = ExportWorker(mock_settings)

            import structlog
            log = structlog.get_logger()

            await worker._submit_job_direct_export(sample_export_jobs[0], log)

            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert call_kwargs["status"] == ExportJobStatus.FAILED

    @pytest.mark.asyncio
    async def test_submit_job_direct_export_unexpected_error(
        self,
        mock_settings: MagicMock,
        sample_export_jobs: list[ExportJob],
    ) -> None:
        """Test direct export handles unexpected error."""
        with patch("export_worker.worker.StarburstClient") as mock_sb_cls, \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_sb = mock_sb_cls.from_config.return_value
            mock_sb.execute_and_export_async = AsyncMock(
                side_effect=RuntimeError("Unexpected")
            )
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True, any_failed=True, first_error="Unexpected",
            )

            worker = ExportWorker(mock_settings)

            import structlog
            log = structlog.get_logger()

            await worker._submit_job_direct_export(sample_export_jobs[0], log)

            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert call_kwargs["status"] == ExportJobStatus.FAILED


class TestExportWorkerSubmitJobViaConnector:
    """Tests for dynamic connector export."""

    @pytest.mark.asyncio
    async def test_submit_via_connector_success(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test successful connector export."""
        job = ExportJob(
            id=1, snapshot_id=123, job_type="node", entity_name="Customer",
            status=ExportJobStatus.PENDING, gcs_path="gs://b/p/",
            data_source_id=42, sql="SELECT * FROM t",
        )

        mock_connector = AsyncMock()
        mock_connector.execute_and_export_parquet = AsyncMock(return_value=(300, 2048))
        mock_connector.close = AsyncMock()

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"), \
             patch("export_worker.worker.create_connector", return_value=mock_connector):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_data_source.return_value = {
                "source_type": "bigquery",
                "config": {},
                "credentials": {},
            }
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True, any_failed=False,
                node_counts={"Customer": 300}, total_size=2048,
            )

            worker = ExportWorker(mock_settings)

            import structlog
            log = structlog.get_logger()

            await worker._submit_job_via_connector(job, log)

            mock_connector.execute_and_export_parquet.assert_called_once()
            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert call_kwargs["status"] == ExportJobStatus.COMPLETED
            assert call_kwargs["row_count"] == 300

    @pytest.mark.asyncio
    async def test_submit_via_connector_missing_sql(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test connector export fails when SQL is missing."""
        job = ExportJob(
            id=1, snapshot_id=123, job_type="node", entity_name="Customer",
            status=ExportJobStatus.PENDING, gcs_path="gs://b/p/",
            data_source_id=42, sql=None,
        )

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True, any_failed=True,
            )

            worker = ExportWorker(mock_settings)

            import structlog
            log = structlog.get_logger()

            await worker._submit_job_via_connector(job, log)

            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert call_kwargs["status"] == ExportJobStatus.FAILED

    @pytest.mark.asyncio
    async def test_submit_via_connector_error(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test connector export handles errors."""
        job = ExportJob(
            id=1, snapshot_id=123, job_type="node", entity_name="Customer",
            status=ExportJobStatus.PENDING, gcs_path="gs://b/p/",
            data_source_id=42, sql="SELECT * FROM t",
        )

        mock_connector = AsyncMock()
        mock_connector.execute_and_export_parquet = AsyncMock(
            side_effect=RuntimeError("BigQuery timeout")
        )
        mock_connector.close = AsyncMock()

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"), \
             patch("export_worker.worker.create_connector", return_value=mock_connector):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_data_source.return_value = {
                "source_type": "bigquery", "config": {}, "credentials": {},
            }
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True, any_failed=True, first_error="BigQuery timeout",
            )

            worker = ExportWorker(mock_settings)

            import structlog
            log = structlog.get_logger()

            await worker._submit_job_via_connector(job, log)

            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert call_kwargs["status"] == ExportJobStatus.FAILED


class TestExportWorkerSubmitJobMissingFields:
    """Tests for submit job with missing required fields."""

    @pytest.mark.asyncio
    async def test_submit_job_missing_sql(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test that job with missing SQL is marked as failed."""
        job = ExportJob(
            id=1, snapshot_id=123, job_type="node", entity_name="Customer",
            status=ExportJobStatus.PENDING, gcs_path="gs://b/p/",
            sql=None, column_names=["id"], starburst_catalog="analytics",
        )

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True, any_failed=True,
            )

            worker = ExportWorker(mock_settings)
            await worker._submit_job(job)

            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert call_kwargs["status"] == ExportJobStatus.FAILED

    @pytest.mark.asyncio
    async def test_submit_job_unload_not_registered_fallback(
        self,
        mock_settings: MagicMock,
        sample_export_jobs: list[ExportJob],
    ) -> None:
        """Test that 'not registered' error triggers direct export."""
        from export_worker.exceptions import StarburstError

        with patch("export_worker.worker.StarburstClient") as mock_sb_cls, \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_sb = mock_sb_cls.from_config.return_value
            mock_sb.submit_unload_async = AsyncMock(
                side_effect=StarburstError("Function not registered")
            )
            mock_sb.execute_and_export_async = AsyncMock(return_value=(100, 512))
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True, any_failed=False,
                node_counts={"Customer": 100}, total_size=512,
            )

            worker = ExportWorker(mock_settings)
            await worker._submit_job(sample_export_jobs[0])

            mock_sb.execute_and_export_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_job_unexpected_error(
        self,
        mock_settings: MagicMock,
        sample_export_jobs: list[ExportJob],
    ) -> None:
        """Test that unexpected errors mark job as failed."""
        with patch("export_worker.worker.StarburstClient") as mock_sb_cls, \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_sb = mock_sb_cls.from_config.return_value
            mock_sb.submit_unload_async = AsyncMock(
                side_effect=RuntimeError("Unexpected")
            )
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True, any_failed=True,
            )

            worker = ExportWorker(mock_settings)
            await worker._submit_job(sample_export_jobs[0])

            call_kwargs = mock_cp.update_export_job.call_args.kwargs
            assert call_kwargs["status"] == ExportJobStatus.FAILED

    @pytest.mark.asyncio
    async def test_submit_job_routes_to_connector(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test that job with data_source_id routes to connector."""
        job = ExportJob(
            id=1, snapshot_id=123, job_type="node", entity_name="Customer",
            status=ExportJobStatus.PENDING, gcs_path="gs://b/p/",
            data_source_id=42, sql="SELECT * FROM t",
        )

        mock_connector = AsyncMock()
        mock_connector.execute_and_export_parquet = AsyncMock(return_value=(50, 256))
        mock_connector.close = AsyncMock()

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"), \
             patch("export_worker.worker.create_connector", return_value=mock_connector):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_data_source.return_value = {
                "source_type": "bigquery", "config": {}, "credentials": {},
            }
            mock_cp.get_snapshot_jobs_result.return_value = SnapshotJobsResult(
                all_complete=True, any_failed=False,
            )

            worker = ExportWorker(mock_settings)
            await worker._submit_job(job)

            mock_connector.execute_and_export_parquet.assert_called_once()


class TestExportWorkerConnectorCache:
    """Tests for connector caching and cleanup."""

    @pytest.mark.asyncio
    async def test_get_connector_returns_none_without_data_source(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test _get_connector returns None when no data_source_id."""
        job = ExportJob(
            id=1, snapshot_id=123, job_type="node", entity_name="Customer",
            status=ExportJobStatus.PENDING, gcs_path="gs://b/p/",
            data_source_id=None,
        )

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient"), \
             patch("export_worker.worker.GCSClient"):
            worker = ExportWorker(mock_settings)
            result = await worker._get_connector(job)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_connector_caches(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test _get_connector caches connectors by data_source_id."""
        job = ExportJob(
            id=1, snapshot_id=123, job_type="node", entity_name="Customer",
            status=ExportJobStatus.PENDING, gcs_path="gs://b/p/",
            data_source_id=42, sql="SELECT * FROM t",
        )

        mock_connector = AsyncMock()

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"), \
             patch("export_worker.worker.create_connector", return_value=mock_connector) as mock_create:
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_data_source.return_value = {
                "source_type": "bigquery", "config": {}, "credentials": {},
            }

            worker = ExportWorker(mock_settings)

            # First call creates connector
            c1 = await worker._get_connector(job)
            assert c1 is mock_connector
            assert mock_create.call_count == 1

            # Second call returns cached
            c2 = await worker._get_connector(job)
            assert c2 is mock_connector
            assert mock_create.call_count == 1

    @pytest.mark.asyncio
    async def test_cleanup_connectors_closes_all(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test _cleanup_connectors closes all cached connectors."""
        mock_connector = AsyncMock()
        mock_connector.close = AsyncMock()

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient"), \
             patch("export_worker.worker.GCSClient"):
            worker = ExportWorker(mock_settings)
            worker._connector_cache[42] = mock_connector

            await worker._cleanup_connectors()

            mock_connector.close.assert_called_once()
            assert len(worker._connector_cache) == 0

    @pytest.mark.asyncio
    async def test_cleanup_connectors_handles_close_error(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test _cleanup_connectors handles errors during close."""
        mock_connector = AsyncMock()
        mock_connector.close = AsyncMock(side_effect=RuntimeError("Close failed"))

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient"), \
             patch("export_worker.worker.GCSClient"):
            worker = ExportWorker(mock_settings)
            worker._connector_cache[42] = mock_connector

            # Should not raise
            await worker._cleanup_connectors()
            assert len(worker._connector_cache) == 0


class TestExportWorkerWaitOrShutdown:
    """Tests for _wait_or_shutdown."""

    @pytest.mark.asyncio
    async def test_wait_or_shutdown_returns_on_timeout(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test _wait_or_shutdown returns after timeout."""
        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient"), \
             patch("export_worker.worker.GCSClient"):
            worker = ExportWorker(mock_settings)
            # Should return quickly with a very short timeout
            await worker._wait_or_shutdown(0.01)

    @pytest.mark.asyncio
    async def test_wait_or_shutdown_returns_on_signal(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test _wait_or_shutdown returns immediately on shutdown."""
        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient"), \
             patch("export_worker.worker.GCSClient"):
            worker = ExportWorker(mock_settings)
            worker.request_shutdown()
            # Should return immediately
            await worker._wait_or_shutdown(10)


class TestExportWorkerPollPhaseErrors:
    """Tests for poll phase error handling."""

    @pytest.mark.asyncio
    async def test_poll_phase_handles_cp_error(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test poll phase returns empty on CP error."""
        from export_worker.exceptions import ControlPlaneError

        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.get_pollable_export_jobs.side_effect = ControlPlaneError("Down")

            worker = ExportWorker(mock_settings)
            result = await worker._poll_phase()

            assert result == []


class TestExportWorkerMainLoop:
    """Tests for the main worker loop."""

    @pytest.mark.asyncio
    async def test_main_loop_runs_three_phases(
        self,
        mock_settings: MagicMock,
    ) -> None:
        """Test that main loop runs all three phases."""
        with patch("export_worker.worker.StarburstClient"), \
             patch("export_worker.worker.ControlPlaneClient") as mock_cp_cls, \
             patch("export_worker.worker.GCSClient"):
            mock_cp = mock_cp_cls.from_config.return_value
            mock_cp.claim_export_jobs.return_value = []
            mock_cp.get_pollable_export_jobs.return_value = []

            worker = ExportWorker(mock_settings)

            # Run for one iteration then shutdown
            async def run_and_stop():
                await asyncio.sleep(0.1)
                worker.request_shutdown()

            shutdown_task = asyncio.create_task(run_and_stop())
            await worker.run()
            await shutdown_task  # Ensure task completes

            # Both claim and poll should be called
            mock_cp.claim_export_jobs.assert_called()
            mock_cp.get_pollable_export_jobs.assert_called()
