# 3.1.2
- Moved hosting to public pypi

# 3.1.1
- Fixed typing in before_request() and after_request() hooks
- Fixed use of removed helper class in apispec dependency
- Fixed openapi spec generation tests
- Removed sonarcloud

# 3.1.0

- Add dev-only endpoint for echoing request headers

# 3.0.1

- Fix for etag handling (you can't add an etag on a direct passthrough reponse such as an asset)

# 3.0.0

- Now requires Flask 2.x and Apispec 5.x as minimum version

# 2.7.0

- Added an env var for explicitly setting the key to be used when pulling scope/permissions from a JWT
- Added support for an exception AuthMissingException which results in a 401 response

# 2.6.5

- Trimmed logging of long request/response bodies

# 2.6.4

- JwtParser now parses all jwt claims (not only pre-selected) making them accessible via `g.jwt_claims -> claim`

# 2.6.3

- Removed `version` field from `/version` endpoint.

# 2.6.2

- Alter can_edit_spo2_scale to can_edit_ews

# 2.6.1

- Remove no-store from cache headers

# 2.6.0

- Added etag support

# 2.5.5

- Fixed a bug causing a 500 error for unmatched requests

# 2.5.4

- Added logging for request headers

# 2.5.3

- ModelIdentifier UUID is now generated automatically by default

# 2.5.2

- Remove requirement for JWT config

# 2.5.1

- Fix spelling

# 2.5.0

- Allow database configuration to choose between postgres or sqlite
- Added flask decorator 'deprecated_route'

# 2.4.0

- Remove Neo4J dependency

# 2.3.13

- Allow batch inserts to be generated in SQL Alchemy by defaulting executemany_mode to values

# 2.3.12

- Changed post request hook not to log request/response bodies if direct_passthrough is set

# 2.3.11

- Fixed a bug where extra fields were added to generated OpenAPI specifications

# 2.3.10

- Fixed neomodel Identifier hooks to properly update modified/modified_by when a node is saved.

# 2.3.9

- Suppressed erroneous logging warning for requests without JWT
- Added request content to logging of errored HTTP requests

# 2.3.8

- Added more SQLAlchemy config, which can be overridden using env vars
- Reduced verbosity in endpoint permissions logging

# 2.3.7

- Revert decorator verification as it doesn't work with connexion

# 2.3.6

- Verify flask endpoint decorators to ensure flask routing decorator is applied last
- If scopes are given as a list (instead of string) f-b-i now gives a clean PermissionError

# 2.3.5

- Fixed a bug where device IDs were not parsed correctly from device JWTs
- Fixed bytestring conversion in logging of HTTP errors

# 2.3.4

- Make selected required fields optional in Identifier schema for platform level consistency

# 2.3.3

- Switch from dhoslib to she-logging

# 2.3.2

- Fix API endpoint warning introduced in 2.3.1 to only report endpoints for specified blueprints

# 2.3.1

- Reduce logging verbosity
- Add warning when API endpoint isn't included in API spec

# 2.3.0

- Required Python version is now 3.8
- Fix bug that meant monitoring endpoints were being logged
- Turning off JWT validation during a unit test no longer turns it off for subsequent tests.
- Reduced JWT logging: don't log scopes/claims at all unless the validation fails.
- PermissionError now suppresses the traceback: it's an invalid call, not an error in our code so we don't need to traceback.

# 2.2.2

- Add response content logging on HTTP errors

# 2.2.1

- Add summary for monitoring endpoints OpenAPI spec

# 2.2.0

- Added functions to aid endpoint security
- Updated dependencies
- Add handling for marshmallow schema errors and NotImplementedError
- Fix bug causing JWT claims KeyError when JWT is invalid
- Add identifier schema for apispec generation
- Fix bug where modified_by was not set correctly when a pgsql DB entity was updated

# 2.1.1 

- JWT sub and iss fields exposed in g.claims_map

# 2.1.0

- Support for openapi bearerAuth in connexion
- Helpers for apispec to generate openapi.yaml from code
- Added middleware to help flask resolve URLs behind a reverse proxy

# 2.0.7

- Remove NewRelic
- Remove unused logging module (should have been removed with 2.0.0)

# 2.0.6

- Update dependencies

# 2.0.5

- Fix neo4j database connection bug

# 2.0.4

- Fix database migration bug  

# 2.0.3

- Upgrade to poetry 1.0

# 2.0.2

- Added default Postgres pool settings to cope with non-graceful disconnects

# 2.0.1

- Fixed problems with initialising config for Auth0 options
- Added typesafe datetime parsing functions

# 2.0.0

- neo4j and postgres-related code is now optional to install

# 1.3.9

- Added default Postgres pool settings to cope with non-graceful disconnects

# 1.3.8

- Add default no caching headers to all requests

# 1.3.7

- Switched static code analysis to SonarCloud

# 1.3.6

- Switched build from `pip` to `poetry`

# 1.3.5

- Replace `CUSTOM_PYPI_URL` with `PIP_EXTRA_INDEX_URL`

# 1.3.4

- Addition of List requestArg

# 1.3.3

- Pin Flask to 1.0.\* to avoid breaking changes, because apparently they don't know what semver is

# 1.3.2

- Catch and log neo4j and postgres connection issues
- Added makefile

# 1.3.1

- Removed spammy logging

# 1.3.0

- Change to dhoslib logging
- Reviewed logging messages

# 1.2.5

- Request ID handling.

# 1.2.4

- suppress logging kube probe requests of /running

# 1.2.3

- Use shared logging library
- Structured logging of requests

# 1.2.2

- Metrics endpoint now aggregates stats per-endpoint, instead of per-unique URL

# 1.2.1

- Changed current JWT user check to add warning and return "unknown"

# 1.2.0

- Addition of device_id to current JWT user checks
- Pinning of dependencies to major versions

# 1.1.26

- Removal of clinician database lookup for expanded identifier (moved to Dhos-services)

# 1.1.25

- Updates CICD build/deploy process
