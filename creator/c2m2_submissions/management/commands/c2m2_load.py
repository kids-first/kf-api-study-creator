import os
import csv
import logging
import requests
from dataclasses import dataclass, field
from typing import (
    Any,
    TypeVar,
    Dict,
    Generic,
    Optional,
    Union,
    List,
    get_args,
)
from django.core.management.base import BaseCommand, CommandError

from django.conf import settings

logger = logging.getLogger(__name__)

ROOT_PROJECT_NS = "kidsfirst:"
ROOT_PROJECT_LOCAL_ID = "drc"
ROOT_PROJECT_ABBR = "KFDRC"
ROOT_PROJECT_NAME = (
    "The Gabriella Miller Kids First Pediatric Research Program"
)
ROOT_PROJECT_DESCRIPTION = """
A large-scale data resource to help researchers uncover new insights into the 
biology of childhood cancer and structural birth defects.
""".replace(
    "\n", ""
)
ROOT_PROJECT_URL = "https://kidsfirstdrc.org"

CONTACT_EMAIL = "support@kidsfirstdrc.org"
CONTACT_NAME = "Kids First Support"

# This is the prefix used for each sub-project in Kids First (Each study)
PROJECT_PREFIX = "Kids First: "

# This is a list of studies that are currently on the portal
# We will only add these studies to the submission by default
PUBLISHED_STUDIES = [
    "SD_DK0KRWK8",
    "SD_NMVV8A1Y",
    "SD_R0EPRSGS",
    "SD_7NQ9151J",
    "SD_YNSSAPHE",
    "SD_9PYZAHHE",
    "SD_DZ4GPQX6",
    "SD_W0V965XZ",
    "SD_ZXJFFMEF",
    "SD_M3DBXD12",
    "SD_8Y99QZJJ",
    "SD_46RR9ZR6",
    "SD_PREASA7S",
    "SD_B8X3C1MX",
    "SD_BHJXBDQK",
    "SD_1P41Z782",
    "SD_DYPMEHHF",
    "SD_RM8AFW0R",
    "SD_YGVA0E1C",
    "SD_6FPYJQBR",
    "SD_ZFGDG5YS",
    "SD_46SK55A3",
]

# A constant field whose value will be used directly when found in a mapping
Const = type("Const", (str,), {})
# A dataservice field which will be referred to when found in a mapping
DSField = type("DSField", (str,), {})

# Possible fields to use when mapping onto an Entity's properties
Mapping = Union[Const, DSField]


@dataclass
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

        init_query = f"study_id={study}&{params}" if study else "{params}"

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
            # Displays current status in fetching the files
            print(f"\r{len(results)}/{resp.json()['total']}", end="")

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
        for k, v in instance._mapping.items():
            if k not in props:
                raise KeyError(f"{k} is not a property of {cls}")

            # Handle different types of mapping values
            if type(v) is Const:
                props[k] = v
            elif type(v) is DSField:
                props[k] = data.get(v, None)

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


EntityType = TypeVar("EntityType")


@dataclass
class Table(Generic[EntityType]):
    out_dir: str = "data_dir"
    entities: list[EntityType] = field(default_factory=list)

    def write(self):
        """
        Process contents and write file
        """
        self.prepare_file()
        self.load_entities()
        self.write_entities()

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


@dataclass
class Project(Entity):
    _filename: str = "project.tsv"
    _endpoint: str = "studies"
    _mapping: Dict[str, Mapping] = field(
        default_factory=lambda: {
            "id_namespace": Const("kidsfirst"),
            "local_id": DSField("kf_id"),
            "abbreviation": DSField("kf_id"),
            "name": DSField("short_name"),
            "description": DSField("name"),
        }
    )

    id_namespace: str = "kidsfirst"
    local_id: str = "drc"
    persistent_id: Optional[str] = None
    creation_time: Optional[str] = None
    abbreviation: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def _fetch_entities(cls, study: Optional[str]) -> "Project":
        entities = []
        for study in PUBLISHED_STUDIES:
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


class Biosample(Entity):
    _filename: str = "biosample.tsv"

    id_namespace: Optional[str]
    local_id: Optional[str]
    project_id_namespace: Optional[str]
    project_local_id: Optional[str]
    persistent_id: Optional[str]
    creation_time: Optional[str]
    anatomy: Optional[str]


class BiosampleFromSubject(Entity):
    _filename: str = "biosample_from_subject.tsv"

    biosample_id_namespace: Optional[str]
    biosample_local_id: Optional[str]
    subject_id_namespace: Optional[str]
    subject_local_id: Optional[str]


class BiosampleFromSubject(Entity):
    _filename: str = "biosample_in_collecion.tsv"

    biosample_id_namespace: Optional[str]
    biosample_local_id: Optional[str]
    subject_id_namespace: Optional[str]
    subject_local_id: Optional[str]


class Collection(Entity):
    _filename: str = "collection.tsv"

    biosample_id_namespace: Optional[str]
    biosample_local_id: Optional[str]
    subject_id_namespace: Optional[str]
    subject_local_id: Optional[str]


class CollectionDefinedByProject(Entity):
    _filename: str = "collection_defined_by_project.tsv"


class CollectionInCollection(Entity):
    _filename: str = "collection_in_collection.tsv"


@dataclass
class File(Entity):
    _filename: str = "file.tsv"
    _endpoint: str = "genomic-files"
    _mapping: Dict[str, Mapping] = field(
        default_factory=lambda: {
            "id_namespace": Const(ROOT_PROJECT_NS),
            "local_id": DSField("kf_id"),
            "project_id_namespace": Const(ROOT_PROJECT_NS),
            "project_local_id": DSField("study_id"),
            "size_in_bytes": DSField("size"),
            "uncompressed_size_in_bytes": DSField("size"),
            "filename": DSField("file_name"),
            "file_format": DSField("file_format"),
            "data_type": DSField("data_type"),
        }
    )
    id_namespace: str = "kidsfirst"
    local_id: str = "drc"
    project_id_namespace: str = "kidsfirst"
    project_local_id: Optional[str] = None
    persistent_id: Optional[str] = None
    creation_time: Optional[str] = None
    size_in_bytes: Optional[int] = 0
    uncompressed_size_in_bytes: Optional[int] = 0
    sha256: Optional[str] = ""
    md5: Optional[str] = ""
    filename: Optional[str] = ""
    file_format: Optional[str] = ""
    data_type: Optional[str] = ""
    assay_type: Optional[str] = ""
    mime_type: Optional[str] = ""


class FileDescribesBiosample(Entity):
    _filename: str = "file_describes_biosample.tsv"


class FileDescribesSubject(Entity):
    _filename: str = "file_describes_subject.tsv"


class FileInCollection(Entity):
    _filename: str = "file_in_collection.tsv"


class IdNamespace(Entity):
    _filename: str = "id_namespace.tsv"


class PrimaryDCCContact(Entity):
    _filename: str = "primary_dcc_contact.tsv"


class ProjectInProject(Entity):
    _filename: str = "project_in_project.tsv"


class Subject(Entity):
    _filename: str = "subject.tsv"


class SubjectInCollection(Entity):
    _filename: str = "subject_in_collection.tsv"


class SubjectRoleTaxonomy(Entity):
    _filename: str = "subject_role_taxonomy.tsv"


class Command(BaseCommand):
    help = "Create C2M2 Level 0 Manifest from Dataservice"

    def add_arguments(self, parser):
        parser.add_argument(
            "--studies",
            type=str,
            default=PUBLISHED_STUDIES,
            nargs="*",
            help="kf_ids of studies to include in the submission file",
        )
        parser.add_argument(
            "--out-dir",
            type=str,
            default="c2m2_submission",
            help="The directory to place the submission files in",
        )

    def handle(self, *args, **options):
        logger.info(
            f"Will build a submission file for {len(options.get('studies'))} "
            "studies."
        )
        self.out_dir = options.get("out_dir")
        self.setup_directory()

        self.tables = [
            Table[entity](out_dir=self.out_dir)
            for entity in [
                Biosample,
                BiosampleFromSubject,
                BiosampleFromSubject,
                Collection,
                CollectionDefinedByProject,
                CollectionInCollection,
                File,
                FileDescribesBiosample,
                FileDescribesSubject,
                FileInCollection,
                IdNamespace,
                PrimaryDCCContact,
                Project,
                ProjectInProject,
                Subject,
                SubjectInCollection,
                SubjectRoleTaxonomy,
            ]
        ]

        logger.info("Preparing files")
        for table in self.tables:
            table.prepare_file()

        for study in PUBLISHED_STUDIES[:2]:
            logger.info(f"Compiling study '{study}'")
            for table in self.tables:
                table.load_entities(study)
                table.write_entities()

    def setup_directory(self):
        logger.info(f"Making directory for submission at '{self.out_dir}'")
        try:
            os.mkdir(self.out_dir)
        except FileExistsError:
            logger.warn(
                f"Output directory '{self.out_dir}' already exists."
                "May overwrite any previous contents"
            )
            pass
