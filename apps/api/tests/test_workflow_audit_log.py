import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vesta_api.domain.workflow_audit_models import NewWorkflowAuditEvent  # noqa: E402
from vesta_api.repositories.workflow_audit_log import (  # noqa: E402
    InMemoryWorkflowAuditLogRepository,
)


class WorkflowAuditLogRepositoryTest(unittest.TestCase):
    def test_groups_events_into_a_complete_workflow(self) -> None:
        repository = InMemoryWorkflowAuditLogRepository()
        for stage in ("input", "system", "output"):
            repository.record(
                NewWorkflowAuditEvent(
                    workflow_id="workflow-1",
                    stage=stage,
                    event_type=f"{stage}_event",
                    summary=f"{stage} summary",
                    payload={"stage": stage},
                )
            )

        workflows = repository.list_workflows(limit=10, offset=0)
        events = repository.list_events("workflow-1")

        self.assertEqual(1, len(workflows))
        self.assertEqual("input summary", workflows[0].input_preview)
        self.assertEqual(3, workflows[0].event_count)
        self.assertTrue(workflows[0].has_input)
        self.assertTrue(workflows[0].has_system)
        self.assertTrue(workflows[0].has_output)
        self.assertEqual(("input", "system", "output"), tuple(e.stage for e in events))
        self.assertEqual({"stage": "system"}, events[1].payload)
        self.assertFalse(hasattr(events[0], "expires_at"))

    def test_filters_events_by_workflow(self) -> None:
        repository = InMemoryWorkflowAuditLogRepository()
        for workflow_id in ("workflow-1", "workflow-2"):
            repository.record(
                NewWorkflowAuditEvent(
                    workflow_id=workflow_id,
                    stage="input",
                    event_type="free_text_submitted",
                    summary=workflow_id,
                    payload={},
                )
            )

        self.assertEqual(1, len(repository.list_events("workflow-2")))
        self.assertEqual("workflow-2", repository.list_events("workflow-2")[0].summary)


if __name__ == "__main__":
    unittest.main()
