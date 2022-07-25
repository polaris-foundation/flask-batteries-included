# Flask Batteries Included

An installable package for API microservices. It provides Flask plus the basic extras Polaris needs for every API microservice.

Flask Batteries Included contains the following functionality:
* Common configuration
* Database setup (PostgreSQL)
* Monitoring API endpoints, and metrics
* Endpoint security and JWT parsing
* API error handling
* Schema validation
* Utility methods

To use Flask Batteries Included, call `augment_app`, passing in the Flask app as a parameter.

```python
def create_app() -> Flask:
    app: Flask = Flask(__name__)
    
    # Augment app to initialise Flask Batteries Included.
    app: Flask = fbi_augment_app(app=app)

    # Initialise config, which will check required env vars are present.
    init_config(app)

    # Add an API blueprint of your choice.
    app.register_blueprint(some_blueprint)
    return app
```

## Maintainers
The Polaris platform was created by Sensyne Health Ltd., and has now been made open-source. As a result, some of the
instructions, setup and configuration will no longer be relevant to third party contributors. For example, some of
the libraries used may not be publicly available, or docker images may not be accessible externally. In addition, 
CICD pipelines may no longer function.

For now, Sensyne Health Ltd. and its employees are the maintainers of this repository.

## Common configuration
Depending on the flags you pass into the `fbi_augment_app` call, initialising the config will check for the presence
of certain sets of environment variables (defaulting where appropriate). Each set of environment variables is grouped
into classes in [flask_batteries_included/config.py](flask_batteries_included/config.py)

## Database setup (PostgreSQL)
Use the `init_db(app)` function in [flask_batteries_included/sqldb.py](flask_batteries_included/sqldb.py) to initialise
a SQL database. This also provides utility functions, and a base `Identifer` model for the `SQLAlchemy` ORM.

## Monitoring API endpoints, and metrics
Augmenting an app with Flask Batteries included will register a blueprint for monitoring endpoints, which can be found 
in [flask_batteries_included/blueprint_monitoring/\_\_init__.py](flask_batteries_included/blueprint_monitoring/__init__.py).
The `/running` endpoint is useful for Kubernetes readiness and liveness checks, as well as healthchecks within docker
environments.

There is additional logic in [flask_batteries_included/helpers/metrics.py](flask_batteries_included/helpers/metrics.py)
that add performance metrics and logging in a Flask post-request hook. This allows you to see information about requests
and responses in the form of logging and response headers.

## Endpoint security and JWT parsing
The [flask_batteries_included/helpers/security](flask_batteries_included/helpers/security) module contains helpers for
performing endpoint protection using JSON Web Tokens (JWTs). This is a bespoke module which allows Polaris services to 
add JWT validation as well as authorisation based on a particular JWT's scope, using the `protected_route` decorator:

```python
@api_blueprint.route("/dhos/v1/patient/<patient_id>/installation", methods=["POST"])
@protected_route(
    and_(
        scopes_present(required_scopes="write:gdm_telemetry"),
        match_keys(patient_id="patient_id"),
    )
)
def create_patient_installation(patient_id: str) -> Response:
    ...
```

The JWT validation logic is complex as it involves slightly different validation steps depending on the source of the 
JWT. For example, if the JWT was issued by a third-party authentication provider such as Auth0 or Azure AD B2C, we
check the JWT's `audience` to see who claims to have issued it, then check the JWT signature against a public key to 
ensure it was signed by the provider.

In other cases, for example JWTs issued by Polaris itself, we instead validate the token using a symmetric key, which
must be provided as an environment variable to the application using this library.

## API error handling
This library extends the default Flask error handling to allow more specific HTTP error codes and messages to be 
returned when certain exceptions are raised. This error handling can be found in
[flask_batteries_included/helpers/error_handler.py](flask_batteries_included/helpers/error_handler.py). For example,
raising a `PermissionError` will result in an HTTP 403 error response.

## Schema validation
While it is recommended to use dedicated libraries for schema validation (such as `marshmallow` or `pydantic`), there
are some utilities for performing schema validation within Flask Batteries Included here: 
[flask_batteries_included/helpers/schema.py](flask_batteries_included/helpers/schema.py).
