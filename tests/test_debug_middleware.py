import importlib
import creator.schema


def test_debug_middleware_enabled(db, client, settings):
    """
    Test that the debug query is added to the schema when DEBUG is on.
    """
    settings.DEBUG = True

    importlib.reload(creator.schema)

    assert hasattr(creator.schema.Query, "debug")


def test_debug_middleware_disabled(db, client, settings):
    """
    Test that the debug query is not resolved when DEBUG is off
    """
    settings.DEBUG = False

    importlib.reload(creator.schema)

    assert not hasattr(creator.schema.Query, "debug")
