
from creator.ingest_runs.models import State
from creator.ingest_runs.common.model import hash_versions


def cancel_duplicate_ingest_processes(
    version_kfids, ingest_process_cls, cancel_task
):
    """
    Cancel ingest processes (e.g. ingest run, validation run) that are
    already running for the same set of file versions
    """
    duplicates = ingest_process_cls.objects.filter(
        state__in=[State.NOT_STARTED, State.RUNNING],
        input_hash=hash_versions(version_kfids),
    ).all()

    canceled_any = False
    for dup in duplicates:
        dup.queue.enqueue(cancel_task, args=(dup.id,))
        canceled_any = True

    return canceled_any
