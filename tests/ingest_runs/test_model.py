from creator.files.models import File
from creator.ingest_runs.models import IngestRun

from django.contrib.auth import get_user_model

User = get_user_model()


def test_ingest_run(db, clients, prep_file):
    """
    Test IngestRun model
    """
    # Create some data
    for i in range(2):
        prep_file(authed=True)
    file_versions = [f.versions.first() for f in File.objects.all()]

    # Create two valid ingest runs for the same batch of file versions
    for i in range(2):
        ir = IngestRun()
        ir.save()
        assert not ir.input_hash
        assert not ir.name
        assert not ir.study
        assert str(ir) == str(ir.pk)
        ir.versions.set(file_versions)
        ir.save()
        assert ir.input_hash
        assert ir.name
        assert ir.study == file_versions[0].root_file.study
        assert str(ir) == ir.name
        for v in file_versions:
            assert v.kf_id in ir.name
    ingest_runs = [(ir.input_hash, ir.name) for ir in IngestRun.objects.all()]
    assert ingest_runs[0] == ingest_runs[1]

    # Create third ingest run with diff set of file versions
    ir3 = IngestRun()
    ir3.save()
    ir3.versions.add(file_versions[0])
    ir3.save()
    for ir in ingest_runs:
        assert ir3.input_hash, ir3.name != ir
