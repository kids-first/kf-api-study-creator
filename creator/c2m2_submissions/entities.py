import os
import csv
import logging
import requests
from typing import Any, Dict, Generic, Optional, List, TypeVar, get_args
from dataclasses import dataclass, field
from django.conf import settings

from .types import (
    StrConst,
    IntConst,
    DataType,
    FileFormat,
    Mapping,
    FileNameField,
    DSField,
    DSRelation,
)
from .globals import (
    ROOT_PROJECT_NS,
    ROOT_PROJECT_DESCRIPTION,
    ROOT_PROJECT_NAME,
    ROOT_PROJECT_ABBR,
    ROOT_PROJECT_LOCAL_ID,
)
from .edam_mapper import EDAMMapper

logger = logging.getLogger(__name__)

EntityType = TypeVar("EntityType")


def filename_mapper(name: Optional[str]):
    if name is None:
        return

    return name.split("/")[-1]


@dataclass
class Table(Generic[EntityType]):
    out_dir: str = "data_dir"
    entities: list[EntityType] = field(default_factory=list)

    def prepare_file(self):
        """
        Prepare the Table by writing the header out.
        Will replace any contents previously existing for the file.
        """
        T = get_args(self.__orig_class__)[0]
        # Any non-private properties will be written out
        header = [k for k in T.__annotations__.keys() if not k.startswith("_")]
        with open(
            os.path.join(self.out_dir, T._filename), "w", newline="\n"
        ) as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(header)

    def load_entities(self, study: Optional[str] = None) -> None:
        """
        Load and transform entities into desired target format
        """
        T = get_args(self.__orig_class__)[0]
        self.entities = T._fetch_entities(study)

    def write_entities(self) -> None:
        """
        Write entities out to file
        """
        T = get_args(self.__orig_class__)[0]
        with open(
            os.path.join(self.out_dir, T._filename), "a", newline="\n"
        ) as f:
            writer = csv.writer(f, delimiter="\t")
            for e in self.entities:
                writer.writerow(T._serialize(e))


mapper = EDAMMapper()


class Entity:
    _mapping: Dict[str, Mapping] = field(default_factory=dict)
    _endpoint: Optional[str] = None

    @classmethod
    def _fetch_entities(cls, study: Optional[str] = None) -> List["Entity"]:
        """
        Fetch entities from Dataservice and deserialize them
        """
        # Skip this entity if the endpoint is not given
        if cls._endpoint is None:
            return []

        url = f"{settings.DATASERVICE_URL}/{cls._endpoint}"
        params = f"visible=True&limit=100"

        init_query = f"study_id={study}&{params}" if study else f"{params}"

        results = []
        entities = []
        resp = requests.get(f"{url}?{init_query}")
        logger.info(
            f"{resp.json()['total']} entities to fetch for {cls.__name__}"
        )
        results.extend(resp.json()["results"])

        while "next" in resp.json()["_links"]:
            next_link = resp.json()["_links"]["next"]
            resp = requests.get(
                f"{settings.DATASERVICE_URL}/{next_link}&{params}"
            )
            results.extend(resp.json()["results"])
            print(
                f"\r{len(results)} downloaded of {resp.json()['total']}",
                end="",
            )

        logger.info(f"Fetched {len(results)} files for study {study}")

        for res in results:
            # Inject the study id so we can use it when we serialize
            if study:
                res["study_id"] = study
            entities.append(cls._deserialize(res))

        return entities

    @classmethod
    def _deserialize(cls, data) -> "Entity":
        """
        Deserialize a data object to an Entity by applying the Entity's
        mapping.
        """
        # Formulate a default value set where everything is None
        props = {
            k: None
            for k in cls.__annotations__.keys()
            if not k.startswith("_")
        }

        instance = cls()
        if not isinstance(instance._mapping, dict):
            raise ValueError(
                f"A mapping must be defined for {cls} before deserializing"
            )
        for k, v in instance._mapping.items():
            if k not in props:
                raise KeyError(f"{k} is not a property of {cls}")

            # TODO: This could be better represented as a dict?
            #       mappers = {EDAM: edam_mapper}
            # Handle different types of mapping values
            if type(v) in [StrConst, IntConst]:
                props[k] = v
            elif type(v) is DSField:
                props[k] = data.get(v, None)
            elif type(v) is DSRelation:
                # Try to get the desired relation from _links
                link = data.get("_links", {}).get(v, None)
                if link is None:
                    return
                # Extract the kf_id from the link
                link = link.split("/")[-1]
                props[k] = link
            elif type(v) is FileFormat:
                props[k] = mapper.map_file_format(data.get(v, None))
            elif type(v) is FileNameField:
                props[k] = filename_mapper(data.get(v, None))
            elif type(v) is DataType:
                props[k] = mapper.map_data_type(data.get(v, None))

        # Actually set properties on the instance
        for k, v in props.items():
            setattr(instance, k, v)

        return instance

    @classmethod
    def _serialize(cls, instance: "Entity") -> List[Any]:
        """
        Returns a list of the values of the Entity's properties ordered
        according to how they are defined in the Entity's class.
        """
        props = [
            getattr(instance, k)
            for k in instance.__annotations__.keys()
            if not k.startswith("_")
        ]
        return props


# Following are many definitions for all the entities in the C2M2 model


@dataclass
class Project(Entity):
    id_namespace: Optional[str] = None
    local_id: Optional[str] = None
    persistent_id: Optional[str] = None
    creation_time: Optional[str] = None
    abbreviation: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

    _filename: str = "project.tsv"
    _endpoint: str = "studies"
    _mapping: Dict[str, Mapping] = field(
        default_factory=lambda: {
            "id_namespace": StrConst(ROOT_PROJECT_NS),
            "local_id": DSField("kf_id"),
            "abbreviation": DSField("kf_id"),
            "name": DSField("short_name"),
            "description": DSField("name"),
        }
    )

    @classmethod
    def _fetch_entities(cls, study: Optional[str]) -> List["Project"]:
        """
        If no study is passed, create the high-level project for Kids First.
        If a study is passed, retrieve its info from the DataService
        """
        entities = []
        # Make the high-level project which is not captured in the Dataservice
        if study is None:
            entities.append(
                Project(
                    id_namespace=ROOT_PROJECT_NS,
                    local_id=ROOT_PROJECT_LOCAL_ID,
                    abbreviation=ROOT_PROJECT_ABBR,
                    name=ROOT_PROJECT_NAME,
                    description=ROOT_PROJECT_DESCRIPTION,
                )
            )
        else:
            try:
                resp = requests.get(
                    f"{settings.DATASERVICE_URL}/studies/{study}"
                )
            except Exception as err:
                logger.error(
                    f"Problem getting study {study} from Dataservice: {err}"
                )
                raise
            entities.append(cls._deserialize(resp.json()["results"]))

        return entities


class Anatomy(Entity):
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

    _filename: str = "anatomy.tsv"


class AssayType(Entity):
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

    _filename: str = "assay_type.tsv"


@dataclass
class Biosample(Entity):
    id_namespace: Optional[str] = None
    local_id: Optional[str] = None
    project_id_namespace: Optional[str] = None
    project_local_id: Optional[str] = None
    persistent_id: Optional[str] = None
    creation_time: Optional[str] = None
    anatomy: Optional[str] = None

    _filename: str = "biosample.tsv"
    _endpoint: str = "biospecimens"
    _mapping: Dict[str, Mapping] = field(
        default_factory=lambda: {
            "id_namespace": StrConst(ROOT_PROJECT_NS),
            "local_id": DSField("kf_id"),
            "project_id_namespace": StrConst(ROOT_PROJECT_NS),
            "project_local_id": DSField("study_id"),
            "creation_time": DSField("created_at"),
        }
    )


@dataclass
class BiosampleFromSubject(Entity):
    biosample_id_namespace: Optional[str] = None
    biosample_local_id: Optional[str] = None
    subject_id_namespace: Optional[str] = None
    subject_local_id: Optional[str] = None

    _filename: str = "biosample_from_subject.tsv"

    _endpoint: str = "biospecimens"
    _mapping: Dict[str, Mapping] = field(
        default_factory=lambda: {
            "biosample_id_namespace": StrConst(ROOT_PROJECT_NS),
            "biosample_local_id": DSField("kf_id"),
            "subject_id_namespace": StrConst(ROOT_PROJECT_NS),
            "subject_local_id": DSRelation("participant"),
        }
    )


class BiosampleInCollection(Entity):
    biosample_id_namespace: Optional[str] = None
    biosample_local_id: Optional[str] = None
    collection_id_namespace: Optional[str] = None
    collection_local_id: Optional[str] = None

    _filename: str = "biosample_in_collection.tsv"


class Collection(Entity):
    id_namespace: Optional[str] = None
    local_id: Optional[str] = None
    persistent_id: Optional[str] = None
    creation_time: Optional[str] = None
    abbreviation: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

    _filename: str = "collection.tsv"


class CollectionDefinedByProject(Entity):
    collection_id_namespace: Optional[str] = None
    collection_local_id: Optional[str] = None
    project_id_namespace: Optional[str] = None
    project_local_id: Optional[str] = None

    _filename: str = "collection_defined_by_project.tsv"


class CollectionInCollection(Entity):
    superset_collection_id_namespace: Optional[str] = None
    superset_collection_local_id: Optional[str] = None
    subset_collection_id_namespace: Optional[str] = None
    subset_collection_local_id: Optional[str] = None

    _filename: str = "collection_in_collection.tsv"


@dataclass
class File(Entity):
    id_namespace: Optional[str] = None
    local_id: Optional[str] = None
    project_id_namespace: Optional[str] = None
    project_local_id: Optional[str] = None
    persistent_id: Optional[str] = None
    creation_time: Optional[str] = None
    size_in_bytes: Optional[int] = None
    uncompressed_size_in_bytes: Optional[int] = None
    sha256: Optional[str] = None
    md5: Optional[str] = None
    filename: Optional[str] = None
    file_format: Optional[str] = None
    data_type: Optional[str] = None
    assay_type: Optional[str] = None
    mime_type: Optional[str] = None

    _filename: str = "file.tsv"
    _endpoint: str = "genomic-files"
    _mapping: Dict[str, Mapping] = field(
        default_factory=lambda: {
            "id_namespace": StrConst(ROOT_PROJECT_NS),
            "local_id": DSField("kf_id"),
            "project_id_namespace": StrConst(ROOT_PROJECT_NS),
            "project_local_id": DSField("study_id"),
            "size_in_bytes": DSField("size"),
            "uncompressed_size_in_bytes": DSField("size"),
            "filename": FileNameField("file_name"),
            "file_format": FileFormat("file_format"),
            "data_type": DataType("data_type"),
        }
    )


@dataclass
class FileDescribesBiosample(Entity):
    file_id_namespace: Optional[str] = None
    file_local_id: Optional[str] = None
    biosample_id_namespace: Optional[str] = None
    biosample_local_id: Optional[str] = None

    _filename: str = "file_describes_biosample.tsv"

    _endpoint: str = "biospecimen-genomic-files"
    _mapping: Dict[str, Mapping] = field(
        default_factory=lambda: {
            "file_id_namespace": StrConst(ROOT_PROJECT_NS),
            "file_local_id": DSRelation("genomic_file"),
            "biosample_id_namespace": StrConst(ROOT_PROJECT_NS),
            "biosample_local_id": DSRelation("biospecimen"),
        }
    )


class FileDescribesSubject(Entity):
    file_id_namespace: Optional[str] = None
    file_local_id: Optional[str] = None
    subject_id_namespace: Optional[str] = None
    subject_local_id: Optional[str] = None

    _filename: str = "file_describes_subject.tsv"


class FileInCollection(Entity):
    file_id_namespace: Optional[str] = None
    file_local_id: Optional[str] = None
    collection_id_namespace: Optional[str] = None
    collection_local_id: Optional[str] = None

    _filename: str = "file_in_collection.tsv"


@dataclass
class IdNamespace(Entity):
    id: Optional[str] = None
    abbreviation: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

    _filename: str = "id_namespace.tsv"

    @classmethod
    def _fetch_entities(cls, study: Optional[str]) -> List["IdNamespace"]:
        """
        Write out a single record for the kidsfirst namespace
        """
        ns = cls(
            id=ROOT_PROJECT_NS,
            abbreviation="KFDRC_NS",
            name=ROOT_PROJECT_NAME,
            description=ROOT_PROJECT_DESCRIPTION,
        )

        return [ns]


class NCBITaxonomy(Entity):
    id: Optional[str] = None
    clade: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

    _filename: str = "ncbi_taxonomy.tsv"


class PrimaryDCCContact(Entity):
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    project_id_namespace: Optional[str] = None
    project_local_id: Optional[str] = None
    dcc_abbreviation: Optional[str] = None
    dcc_name: Optional[str] = None
    dcc_description: Optional[str] = None
    dcc_url: Optional[str] = None

    _filename: str = "primary_dcc_contact.tsv"


@dataclass
class ProjectInProject(Entity):
    parent_project_id_namespace: Optional[str] = None
    parent_project_local_id: Optional[str] = None
    child_project_id_namespace: Optional[str] = None
    child_project_local_id: Optional[str] = None

    _filename: str = "project_in_project.tsv"

    @classmethod
    def _fetch_entities(cls, study: Optional[str]) -> List["Project"]:
        """
        Relate each study back to the top-level Kids First project.
        If no study is given, we cannot make any relations.
        """
        if study is None:
            return []

        entities = []

        entities.append(
            ProjectInProject(
                parent_project_id_namespace=ROOT_PROJECT_NS,
                parent_project_local_id=ROOT_PROJECT_LOCAL_ID,
                child_project_id_namespace=ROOT_PROJECT_NS,
                child_project_local_id=study,
            )
        )
        return entities


@dataclass
class Subject(Entity):
    id_namespace: Optional[str] = None
    local_id: Optional[str] = None
    project_id_namespace: Optional[str] = None
    project_local_id: Optional[str] = None
    persistent_id: Optional[str] = None
    creation_time: Optional[str] = None
    granularity: Optional[str] = None

    _filename: str = "subject.tsv"
    _endpoint: str = "participants"
    _mapping: Dict[str, Mapping] = field(
        default_factory=lambda: {
            "id_namespace": StrConst(ROOT_PROJECT_NS),
            "local_id": DSField("kf_id"),
            "project_id_namespace": StrConst(ROOT_PROJECT_NS),
            "project_local_id": DSField("study_id"),
            "creation_time": DSField("created_at"),
            "granularity": StrConst("cfde_subject_granularity:0"),
        }
    )


class SubjectInCollection(Entity):
    subject_id_namespace: Optional[str] = None
    subject_local_id: Optional[str] = None
    collection_id_namespace: Optional[str] = None
    collection_local_id: Optional[str] = None

    _filename: str = "subject_in_collection.tsv"


class SubjectRoleTaxonomy(Entity):
    subject_id_namespace: Optional[str] = None
    subject_local_id: Optional[str] = None
    role_id: Optional[str] = None
    taxonomy_id: Optional[str] = None

    _filename: str = "subject_role_taxonomy.tsv"
