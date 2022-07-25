from flask import Flask
from she_logging import logger
from werkzeug.middleware.proxy_fix import ProxyFix

from .blueprint_debug import debug_blueprint
from .blueprint_monitoring import init_monitoring
from .config import init_config, is_not_production_environment
from .helpers.error_handler import init_error_handler
from .helpers.etags import init_etags
from .helpers.json import CustomJSONEncoder
from .helpers.metrics import init_metrics
from .helpers.request_id import init_request_id


def create_app(
    testing: bool = False,
    use_auth0: bool = False,
    use_customdb_auth0: bool = False,
    use_pgsql: bool = False,
    use_sqlite: bool = False,
    import_name: str = None,
) -> Flask:

    app: Flask = Flask(import_name or __name__)
    return augment_app(
        app=app,
        testing=testing,
        use_auth0=use_auth0,
        use_customdb_auth0=use_customdb_auth0,
        use_pgsql=use_pgsql,
        use_sqlite=use_sqlite,
    )


def augment_app(
    app: Flask,
    testing: bool = False,
    use_auth0: bool = False,
    use_customdb_auth0: bool = False,
    use_pgsql: bool = False,
    use_sqlite: bool = False,
    use_jwt: bool = True,
) -> Flask:
    # TODO default use_jwt to False in next major version, and enforce kwargs with *
    use_sqlalchemy = use_pgsql or use_sqlite
    init_config(
        app=app,
        use_sqlalchemy=use_sqlalchemy,
        use_auth0=use_auth0,
        use_customdb_auth0=use_customdb_auth0,
        testing=testing,
        use_sqlite=use_sqlite,
        use_jwt=use_jwt,
    )

    # Register custom error handlers
    init_error_handler(app=app, use_sqlalchemy=use_sqlalchemy)

    app.json_encoder = CustomJSONEncoder

    # Add in support for ETags
    init_etags(app)

    # Add in monitoring endpoints and metrics if not testing
    if not testing:
        init_monitoring(app)
        init_metrics(app)

    # Add in debug endpoints if in a lower environment
    if is_not_production_environment():
        app.register_blueprint(debug_blueprint)

    # Add in X-Request-ID handling
    init_request_id(app)

    # Make sure the reverse proxy headers are used to help flask resolve urls.
    # noinspection PyTypeHints
    app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)  # type:ignore

    # Done!
    logger.info("App now includes batteries!")

    return app
