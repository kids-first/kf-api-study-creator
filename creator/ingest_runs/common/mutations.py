from creator.ingest_runs.models import CANCEL_SOURCES
from creator.ingest_runs.common.model import hash_versions


def cancel_duplicate_ingest_processes(
    version_kfids, ingest_process_cls, cancel_task
):
    """
    Cancel ingest processes (e.g. ingest run, validation run) that are
    already running for the same set of file versions
    """
    duplicates = ingest_process_cls.objects.filter(
        state__in=CANCEL_SOURCES,
        input_hash=hash_versions(version_kfids),
    ).all()

    canceled_any = False
    for dup in duplicates:
        # Transition to canceling state
        dup.start_cancel()
        dup.save()
        # Queue up cancel task
        dup.queue.enqueue(cancel_task, args=(dup.id,))
        canceled_any = True

    return canceled_any
