from datetime import datetime

import pytest
from flask import g

from flask_batteries_included.sqldb import ModelIdentifier, db


class Entity(ModelIdentifier, db.Model):
    dummy = db.Column(db.String(), nullable=False, unique=False)


@pytest.mark.usefixtures("app")
def test_identifier() -> None:
    """
    Tests that when a database entity is updated, the modified and modified_by fields are set automatically.
    """
    g.jwt_claims = {"clinician_id": "first_user_uuid"}
    test_entity = Entity(dummy="first_value")
    db.session.add(test_entity)
    db.session.commit()

    assert test_entity.uuid is not None
    assert isinstance(test_entity.uuid, str)
    assert len(test_entity.uuid) == 36

    assert test_entity.created_by == "first_user_uuid"
    assert test_entity.modified_by == "first_user_uuid"
    assert test_entity.dummy == "first_value"

    middle_time = datetime.utcnow()
    g.jwt_claims = {"clinician_id": "second_user_uuid"}
    test_entity.dummy = "second_value"
    db.session.commit()

    assert test_entity.created_by == "first_user_uuid"
    assert test_entity.modified_by == "second_user_uuid"
    assert test_entity.dummy == "second_value"
    assert test_entity.created < middle_time
    assert test_entity.modified > middle_time
