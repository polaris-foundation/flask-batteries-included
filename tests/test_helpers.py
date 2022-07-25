import re

from flask_batteries_included.helpers import generate_uuid


def test_generate_uuid() -> None:
    assert (
        re.match(
            "^[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}$",
            generate_uuid(),
        )
        is not None
    )
