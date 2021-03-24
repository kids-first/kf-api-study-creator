import types
from typing import Any, Generic, Union, TypeVar

# A constant field whose value will be used directly when found in a mapping
IntConst = type("IntConst", (int,), {})
StrConst = type("StrConst", (str,), {})

# A dataservice field which will be referred to when found in a mapping
DSField = type("DSField", (str,), {})
DSRelation = type("DSRelation", (str,), {})
FileFormat = type("DataType", (str,), {})
DataType = type("FileFormat", (str,), {})
FileNameField = type("FileName", (str,), {})
# Possible fields to use when mapping onto an Entity's properties
Mapping = Union[IntConst, StrConst, DSField, FileFormat, DataType]
