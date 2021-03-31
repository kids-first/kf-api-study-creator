from creator.events.models import Event
from creator.files.models import File
from creator.ingest_runs.models import IngestRun

from django.contrib.auth import get_user_model

User = get_user_model()


def test_ingest_run(db, clients, prep_file):
    """
    Test IngestRun model
    """
    client = clients.get("Administrators")

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
        assert str(ir) == str(ir.id)
        ir.versions.set(file_versions)
        ir.save()
        assert ir.input_hash
        assert ir.name
        assert str(ir)
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

    # Test Event creation
    user = User.objects.first()
    ir4 = setup_ir(file_versions, user)
    ir4.complete()
    ir4.save()

    ir5 = setup_ir(file_versions, user)
    ir5.cancel()
    ir5.save()

    ir6 = setup_ir(file_versions, user)
    ir6.fail()
    ir6.save()

    assert event_type_num("IR_STA") == 3
    assert event_type_num("IR_COM") == 1
    assert event_type_num("IR_CAN") == 1
    assert event_type_num("IR_FAI") == 1


def setup_ir(file_versions, user):
    ir = IngestRun()
    ir.creator = user
    ir.save()
    ir.versions.set(file_versions)
    ir.save()
    ir.start()
    ir.save()
    return ir


def event_type_num(ev_type):
    return Event.objects.filter(event_type=ev_type).count()
