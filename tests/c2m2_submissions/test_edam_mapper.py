from creator.c2m2_submissions.edam_mapper import EDAMMapper


def test_map_file_format():
    """
    Test that file formats are mapped to EDAM ids correctly.
    """
    mapper = EDAMMapper()
    assert mapper.map_file_format("BAM") == "format:2572"


def test_map_file_format_with_data_type():
    """
    Test that file format mapper returns none if given a data type
    """
    mapper = EDAMMapper()
    assert mapper.map_file_format("DNA sequence") is None


def test_map_data_type():
    """
    Test that data types are mapped to EDAM ids correctly.
    """
    mapper = EDAMMapper()
    assert mapper.map_data_type("DNA sequence") == "data:3494"


def test_map_data_type_with_file_format():
    """
    Test that a file format passed to the data type mapper will give back
    none instead of a file format
    """
    mapper = EDAMMapper()
    assert mapper.map_data_type("BAM") is None
