from creator.files.models import File, Version
from creator.events.models import Event
from creator.studies.factories import StudyFactory
from django.contrib.auth import get_user_model

User = get_user_model()

UPDATE_VERSION = """
mutation (
    $kfId:String!,
    $state: VersionState!,
    $description: String,
) {
    updateVersion(
        kfId: $kfId,
        description: $description
        state: $state
    ) {
        version { id kfId state description size }
    }
}
"""


def test_new_version_event(admin_client, db, upload_file, upload_version):
    """
    Test that new versions create events
    """
    study_id = StudyFactory.create_batch(1)[0].kf_id
    resp = upload_file(study_id, "manifest.txt", admin_client)
    file_id = resp.json()["data"]["createFile"]["file"]["kfId"]
    file = File.objects.get(kf_id=file_id)
    user = User.objects.first()

    resp = upload_version(file.kf_id, "manifest.txt", admin_client)
    version = Version.objects.get(
        kf_id=resp.json()["data"]["createVersion"]["version"]["kfId"]
    )

    assert Event.objects.count() == 3
    assert Event.objects.filter(event_type="FV_CRE").count() == 2

    fv_cre = Event.objects.filter(event_type="FV_CRE").latest("created_at")
    assert fv_cre.user == user
    assert fv_cre.file == file
    assert fv_cre.version == version


def test_update_version_event(admin_client, db, upload_file, upload_version):
    """
    Test that updating versions create events
    """
    study_id = StudyFactory.create_batch(1)[0].kf_id
    resp = upload_file(study_id, "manifest.txt", admin_client)
    file_id = resp.json()["data"]["createFile"]["file"]["kfId"]
    file = File.objects.get(kf_id=file_id)
    version = file.versions.first()
    user = User.objects.first()

    variables = {"kfId": version.kf_id, "state": "PRC"}
    resp = admin_client.post(
        "/graphql",
        content_type="application/json",
        data={"query": UPDATE_VERSION, "variables": variables},
    )

    assert Event.objects.count() == 3
    assert Event.objects.filter(event_type="FV_UPD").count() == 1

    fv_upd = Event.objects.filter(event_type="FV_UPD").first()
    assert fv_upd.user == user
    assert fv_upd.file == file
    assert fv_upd.version == version
