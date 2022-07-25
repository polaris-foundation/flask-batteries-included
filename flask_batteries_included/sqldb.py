from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Tuple

from environs import Env
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask_batteries_included.blueprint_monitoring import healthcheck
from flask_batteries_included.helpers import generate_uuid
from flask_batteries_included.helpers.schema import post
from flask_batteries_included.helpers.security.jwt import current_jwt_user

TESTING_DB_URL = "sqlite://"

env: Env = Env()
db: SQLAlchemy = SQLAlchemy()


def init_db(app: Flask, testing: bool = False) -> None:
    db.init_app(app=app)

    # Perform database migrations.
    from flask_migrate import Migrate

    Migrate(app, db)
    if testing is False:
        # Only add db healthchecks if not testing
        healthcheck.add_check(database_connectivity_test)
        healthcheck.add_check(database_version_test)


def database_connectivity_test() -> Tuple[bool, str]:
    """Healthcheck for database connectivity"""
    try:
        db.engine.execute("SELECT 1 AS running;")
    except Exception as e:
        return False, "Database not available. Reason: " + str(e)
    return True, "Database ok"


def database_version_test() -> Tuple[bool, str]:
    """Healthcheck for database content"""
    try:
        result = db.engine.execute("SELECT version_num FROM alembic_version;")
        for r in result:
            return True, "Database version: " + r[0]
    except Exception as e:
        return False, "Database version not available. Reason: " + str(e)
    return True, "Database version: unknown"


class ModelIdentifier:
    """
    This class is designed to be used by classes extending `flask_sqlalchemy.Model`. It provides
    common identifier fields for models and includes onupdate hooks that automatically update the
    `modified` and `modified_by` fields.
    """

    uuid = db.Column(db.String(length=36), primary_key=True, default=generate_uuid)
    created = db.Column(
        db.DateTime, unique=False, nullable=False, default=datetime.utcnow
    )
    created_by_ = db.Column(
        db.String, unique=False, nullable=False, default=current_jwt_user
    )

    modified = db.Column(
        db.DateTime,
        unique=False,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    modified_by_ = db.Column(
        db.String,
        unique=False,
        nullable=False,
        default=current_jwt_user,
        onupdate=current_jwt_user,
    )

    @property
    def created_by(self) -> str:
        """
        Can be overridden in subclass
        :return: uuid of creator
        """
        return self.created_by_

    @property
    def modified_by(self) -> str:
        """
        Can be overridden in subclass
        :return: uuid of last modifier
        """
        return self.modified_by_

    def pack_identifier(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "created": self.created.replace(tzinfo=timezone.utc)
            if self.created
            else None,
            "created_by": self.created_by,
            "modified": self.modified.replace(tzinfo=timezone.utc)
            if self.modified
            else None,
            "modified_by": self.modified_by,
        }

    @staticmethod
    def schema() -> Dict:
        raise NotImplementedError()


def validate_model(json_in: Dict, model: db.Model, modifier: Callable = None) -> Any:
    inputs = post(json_in=json_in, **model.schema())
    if modifier is not None:
        modifier(inputs)

    if "created_by" in inputs:
        inputs["created_by_"] = inputs.pop("created_by")

    if "modified_by" in inputs:
        inputs["modified_by_"] = inputs.pop("modified_by")

    return model(**inputs)


def validate_models(
    json_in: Dict, model: db.Model, modifier: Callable = None
) -> List[Any]:
    return [validate_model(datum, model, modifier=modifier) for datum in json_in]
