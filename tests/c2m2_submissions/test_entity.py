import pytest
from dataclasses import dataclass, field
from typing import Dict, Optional

from creator.c2m2_submissions.entities import Entity
from creator.c2m2_submissions.types import DSField, IntConst, StrConst, Mapping


def test_fetch_no_endpoint(mocker):
    @dataclass
    class MyEntity(Entity):
        id: Optional[str] = None

    mock_req = mocker.patch("creator.c2m2_submissions.entities.requests.get")

    MyEntity._fetch_entities()

    assert mock_req.call_count == 0


def test_fetch(mocker):
    @dataclass
    class MyEntity(Entity):
        id: Optional[str] = None
        _endpoint = "testing"

    mock_req = mocker.patch("creator.c2m2_submissions.entities.requests.get")

    MyEntity._fetch_entities()

    assert mock_req.call_count == 1
    assert mock_req.call_args_list[0].args == (
        "http://dataservice/testing?visible=True&limit=100",
    )


def test_serialize():
    @dataclass
    class MyEntity(Entity):
        id: Optional[str] = None
        name: Optional[str] = None
        _endpoint = "testing"

    entity = MyEntity(id=1, name="Test")
    assert MyEntity._serialize(entity) == [1, "Test"]


def test_deserialize_no_mapping():
    """
    If there is no mapping, we can't deserialize an Entity
    """

    @dataclass
    class MyEntity(Entity):
        id: Optional[str] = None

    with pytest.raises(ValueError):
        MyEntity._deserialize({"id": 1, "name": "Test"})


def test_deserialize_simple_mapping():
    """
    Test a simple mapping of constances
    """

    @dataclass
    class MyEntity(Entity):
        id: Optional[int] = None
        _mapping: Dict[str, Mapping] = field(
            default_factory=lambda: {"id": IntConst(1)}
        )

    entity = MyEntity._deserialize({"id": 1})
    assert entity.id == 1


def test_deserialize_dataservice_field():
    """
    Test the DSField type
    """

    @dataclass
    class MyEntity(Entity):
        id: Optional[str] = None
        _mapping: Dict[str, Mapping] = field(
            default_factory=lambda: {"id": DSField("obj_id")}
        )

    entity = MyEntity._deserialize({"obj_id": 1})
    assert entity.id == 1
