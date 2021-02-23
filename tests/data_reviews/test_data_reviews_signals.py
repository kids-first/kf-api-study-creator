from django.contrib.auth import get_user_model

from creator.data_reviews.factories import DataReview
from creator.data_reviews.models import State
from creator.studies.models import Study
from creator.files.models import File, Version

User = get_user_model()


def test_file_version_delete_signal(db, clients, prep_file):
    """
    Test correct event is fired when file versions are deleted
    """
    # Create two DataReviews with files
    for i in range(2):
        study_id, file_id, _ = prep_file(authed=True)
    f = File.objects.get(pk=file_id).versions.first()

    drs = []
    for i in range(3):
        dr = DataReview(
            creator=User.objects.first(),
            study=Study.objects.get(pk=study_id),
        )
        if i != 0:
            dr.versions.add(f)
            dr.save()
        drs.append(dr)

    # Delete file version
    f.delete()

    # Check events fired for the right data reviews
    for i, dr in enumerate(drs):
        if i == 0:
            event_count = 0
        else:
            event_count = 1
        assert (
            dr.events.filter(
                description__contains="was deleted from data review"
            ).count()
            == event_count
        )


def test_file_post_save_signal(db, clients, prep_file):
    """
    Test for expected data review state change and event firing when
    new file version is uploaded
    """
    # Create a study with files
    files = []
    for i in range(2):
        study_id, file_id, version_id = prep_file(authed=True)
        files.append(file_id)
    f0v0 = File.objects.get(pk=files[0]).versions.first()

    # Create some data reviews with one version
    drs = []
    states = [State.WAITING, State.IN_REVIEW, State.COMPLETED, State.CLOSED]
    for i in range(len(states)):
        dr = DataReview(
            state=states[i],
            creator=User.objects.first(),
            study=Study.objects.get(pk=study_id),
        )
        dr.versions.add(f0v0)
        dr.save()
        drs.append(dr)

    # Upload new version to a file not involved in data reviews
    f1v1 = Version(root_file=File.objects.get(pk=files[1]), size=100)
    f1v1.save()
    for dr in drs:
        assert dr.events.count() == 0

    # Upload new version to file involved in data reviews
    f0v1 = Version(root_file=File.objects.get(pk=files[0]), size=100)
    f0v1.save()
    for dr in drs:
        dr.refresh_from_db()

    # Non-terminal reviews should have events
    for i, dr in enumerate(drs[0:2]):
        for e in dr.events.filter(version=f0v1).all():
            assert f0v1.pk in e.description
            assert "which is part of open data review" in e.description
        if i == 0:
            assert dr.state == State.IN_REVIEW
            assert dr.events.count() == 2
        else:
            assert dr.events.count() == 1

    # Terminal reviews should have 0 events
    for dr in drs[2:]:
        assert dr.events.count() == 0

    # Save existing version - should be no new data review events
    f0v1.size = 200
    f0v1.save()
    for dr in drs:
        assert dr.events.count() <= 2
