from typing import Dict, List, Optional

from environs import Env
from flask import Flask
from she_logging import logger

env = Env()


def init_config(
    *,
    app: Flask,
    use_sqlalchemy: bool = False,
    use_auth0: bool = False,
    use_customdb_auth0: bool = False,
    testing: bool = False,
    use_sqlite: bool = False,
    use_jwt: bool = True,
) -> None:
    app.testing = testing
    app.config.from_object(GeneralConfig(testing=testing))

    if use_jwt:
        logger.info("JWT mode ON")
        app.config.from_object(JwtConfig())
    else:
        logger.info("JWT mode OFF")

    if use_auth0:
        logger.info("Auth0 mode ON")
        app.config.from_object(Auth0Config(testing=testing))
    else:
        logger.info("Auth0 mode OFF")

    if use_customdb_auth0:
        logger.info("Auth0 custom db mode ON")
        app.config.from_object(Auth0CustomConfig())
    else:
        logger.info("Auth0 custom db mode OFF")

    if use_sqlalchemy:
        app.config.from_object(TestSqlDbConfig() if use_sqlite else RealSqlDbConfig())


class GeneralConfig:
    def __init__(self, testing: bool = False) -> None:
        self.ALLOW_DROP_DATA: bool = env.bool("ALLOW_DROP_DATA", default=False)
        self.DEBUG: bool = env.bool("DEBUG", default=False)
        self.ENVIRONMENT: str = env.str("ENVIRONMENT", default="PRODUCTION")
        self.LISTEN_ADDRESS: str = env.str("LISTEN_ADDRESS", default="0.0.0.0")
        self.LOG_REQUEST_ID_GENERATE_IF_NOT_FOUND: bool = env.bool(
            "LOG_REQUEST_ID_GENERATE_IF_NOT_FOUND", default=True
        )
        self.PORT: int = env.int("PORT", default=5000)
        self.PREFERRED_URL_SCHEME: str = env.str("PREFERRED_URL_SCHEME", default="http")
        self.UNITTESTING: bool = testing

        # Guard against turning on dev endpoints in production
        if (
            is_production_environment(environment=self.ENVIRONMENT)
            and self.ALLOW_DROP_DATA
        ):
            raise EnvironmentError(
                "ALLOW_DROP_DATA cannot be True if ENVIRONMENT is set to PRODUCTION."
            )


class JwtConfig:
    def __init__(self) -> None:
        self.HS_KEY: str = env.str("HS_KEY")
        self.IGNORE_JWT_VALIDATION: bool = env.bool(
            "IGNORE_JWT_VALIDATION", default=False
        )
        self.PROXY_URL: str = env.str("PROXY_URL")
        self.HS_ISSUER: str = self.PROXY_URL + "/"
        self.SYSTEM_AUTH_HOST: str = env.str("SYSTEM_AUTH_HOST", default="localhost")
        self.SYSTEM_AUTH_PORT: int = env.int("SYSTEM_AUTH_PORT", default=7000)
        self.SYSTEM_AUTH_URL_SCHEME: str = env.str(
            "SYSTEM_AUTH_URL_SCHEME", default="http"
        )
        self.VALID_JWT_ALGORITHMS: List[str] = [
            "HS256",
            "HS512",
            "HS384",
            "RS256",
            "RS384",
            "RS512",
            "ES256",
            "ES384",
            "ES512",
        ]
        # Require redis as we'll need it to validate JWTs.
        self.REDIS_INSTALLED = env.bool("REDIS_INSTALLED", True)
        if self.REDIS_INSTALLED:
            self.REDIS_HOST = env.str("REDIS_HOST")
            self.REDIS_PORT = env.str("REDIS_PORT")
            self.REDIS_PASSWORD = env.str("REDIS_PASSWORD")
            self.REDIS_TIMEOUT = env.int("REDIS_TIMEOUT", 2)  # Default to 2 seconds.

        # Guard against turning off JWT validation in production
        if (
            is_production_environment(environment=GeneralConfig().ENVIRONMENT)
            and self.IGNORE_JWT_VALIDATION
        ):
            raise EnvironmentError(
                "IGNORE_JWT_VALIDATION cannot be True if ENVIRONMENT is set to PRODUCTION."
            )


class Auth0Config:
    """
    Note that while this section uses "Auth0" throughout, it is in fact extensible to any third party auth
    provider who follows the pattern of issuing signed tokens with a publicly available JWKS for verification
    (such as Azure AD B2C).
    """

    _DEFAULT_AUTH0_DOMAIN = "https://draysonhealth.eu.auth0.com/"
    _DEFAULT_AUTH0_JWKS_URL = "https://draysonhealth.eu.auth0.com/.well-known/jwks.json"
    _DEFAULT_AUTH0_METADATA = "https://gdm.sensynehealth.com/metadata"

    def __init__(self, testing: bool = False) -> None:
        self.AUTH0_AUDIENCE: str = env.str("AUTH0_AUDIENCE")
        self.AUTH0_DOMAIN: str = env.str(
            "AUTH0_DOMAIN", default=self._DEFAULT_AUTH0_DOMAIN
        )
        self.AUTH0_JWKS_URL: str = env.str(
            "AUTH0_JWKS_URL", default=self._DEFAULT_AUTH0_JWKS_URL
        )
        self.AUTH0_METADATA: str = env.str(
            "AUTH0_METADATA", default=self._DEFAULT_AUTH0_METADATA
        )
        # Support our old way of doing things where we infer the scope key from the metadata key.
        auth0_scope_key: Optional[str] = env.str("AUTH0_SCOPE_KEY", None)
        if auth0_scope_key is None:
            if "/" in self.AUTH0_METADATA:
                i_slash = self.AUTH0_METADATA.rfind("/")
                auth0_scope_key = self.AUTH0_METADATA[0:i_slash] + "/scope"
            else:
                auth0_scope_key = "scope"
        self.AUTH0_SCOPE_KEY: str = auth0_scope_key

        if testing:
            self.AUTH0_JWKS_TESTING: str = (
                '{"keys":[{"alg":"RS256","kty":"RSA","use":"sig","x5c":["MIIDDzCCAfegAwIBAgIJOP'
                "kBjuq/HjHCMA0GCSqGSIb3DQEBCwUAMCUxIzAhBgNVBAMTGmRyYXlzb25oZWFsdGguZXUuYXV0aDAu"
                "Y29tMB4XDTE4MDIwODEyNTg0OVoXDTMxMTAxODEyNTg0OVowJTEjMCEGA1UEAxMaZHJheXNvbmhlYW"
                "x0aC5ldS5hdXRoMC5jb20wggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC0J8xif39iOPW6"
                "+lrxSkCBJHhTbSmQaWYzbl0pYA/x7syzZHjoqP46FurTlBz/+b4zgUl9NHO6pRcWKOey9ZspfiBPLe"
                "s3Y/9gIpS6TMvXvl/XvoimCJU07wjESm7/bKVIqGo5XNkwxznMnEmIKCgc5GMjSe/GzkEZxe8oAj6s"
                "FlQv7R1Ugp6LPTQThrdxPtDyC3++0/cg/BpGYM4udgzCpyLNUF3ZsnNGo6hKVmgKp0kkSalualcYqi"
                "fFyQ2yd3sV77/UqWlIMYT0t4D9m3fMn8fvD3RVD8YJ7ScVqgXDEC+37JvR5sooVc99gIGKFDPWoYhY"
                "ORLo784dpGwbeLlJAgMBAAGjQjBAMA8GA1UdEwEB/wQFMAMBAf8wHQYDVR0OBBYEFBbjgqbHy2cDzC"
                "3TZyr4nfse8xhbMA4GA1UdDwEB/wQEAwIChDANBgkqhkiG9w0BAQsFAAOCAQEANTHvJ6DgjWnxfjsJ"
                "EO6Vs+DHQpbMgKX11igtzYAI6bNueLSeFZ5FAlCo1uiS5Fz7voUr0dCMTtqK3EUOWMVZjqxUenUBhD"
                "eF6N1OhaaIV2SqRYvozPSiyg3Q0YGdbKd0+5DIxVfODXsUtU7DAaicIi4+1uITrRu40/MMt51+9G7r"
                "8m6alYM4NA3W7Yd0K4y1BbNOxHHTEfYXl47v4qY/KqU+HcxVVuLixYkGj5M7DW8SbLW8+Mgg6bH+LD"
                "5wJloFpM9mKPO4dXkc7ck4O+tqUXcs2Y7Q7JwtLuZSMcAUSTz7yuDs9A+mo175EsQjL1AKJ3FYpMkr"
                'GqM2KHXbdjniqg=="],"n":"tCfMYn9_Yjj1uvpa8UpAgSR4U20pkGlmM25dKWAP8e7Ms2R46Kj-Oh'
                "bq05Qc__m-M4FJfTRzuqUXFijnsvWbKX4gTy3rN2P_YCKUukzL175f176IpgiVNO8IxEpu_2ylSKhq"
                "OVzZMMc5zJxJiCgoHORjI0nvxs5BGcXvKAI-rBZUL-0dVIKeiz00E4a3cT7Q8gt_vtP3IPwaRmDOLn"
                "YMwqcizVBd2bJzRqOoSlZoCqdJJEmpbmpXGKonxckNsnd7Fe-_1KlpSDGE9LeA_Zt3zJ_H7w90VQ_G"
                'Ce0nFaoFwxAvt-yb0ebKKFXPfYCBihQz1qGIWDkS6O_OHaRsG3i5SQ","e":"AQAB","kid":"NDc1'
                'MjgyOEEwQzI2Q0M2QjZBQTJCRTA2NjdDM0ZCN0ZDOUM1MENBQQ","x5t":"NDc1MjgyOEEwQzI2Q0M'
                '2QjZBQTJCRTA2NjdDM0ZCN0ZDOUM1MENBQQ"}]}'
            )

        logger.info("AUTH0_AUDIENCE set to %s", self.AUTH0_AUDIENCE)
        logger.info("AUTH0_DOMAIN set to %s", self.AUTH0_DOMAIN)
        logger.info("AUTH0_METADATA set to %s", self.AUTH0_METADATA)
        logger.info("AUTH0_SCOPE_KEY set to %s", self.AUTH0_SCOPE_KEY)


class Auth0CustomConfig:
    def __init__(self) -> None:
        self.AUTH0_CUSTOM_DOMAIN: str = env.str("AUTH0_CUSTOM_DOMAIN")
        self.AUTH0_HS_KEY: str = env.str("AUTH0_HS_KEY")


class BaseSqlDbConfig:
    """Base class for SQL database config"""

    def __init__(self) -> None:
        self.SQLALCHEMY_TRACK_MODIFICATIONS: bool = env.bool(
            "SQLALCHEMY_TRACK_MODIFICATIONS", default=False
        )


class TestSqlDbConfig(BaseSqlDbConfig):
    """SQL database config for an in-memory SQLite database"""

    def __init__(self) -> None:
        super().__init__()
        self.SQLALCHEMY_DATABASE_URI: str = "sqlite://"


class RealSqlDbConfig(BaseSqlDbConfig):
    """SQL database config for a real-world database server"""

    def __init__(self) -> None:
        super().__init__()

        self.SQLALCHEMY_DATABASE_URI: str = "postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}".format(
            db_user=env.str("DATABASE_USER"),
            db_pass=env.str("DATABASE_PASSWORD"),
            db_host=env.str("DATABASE_HOST"),
            db_port=env.int("DATABASE_PORT"),
            db_name=env.str("DATABASE_NAME"),
        )

        self.SQLALCHEMY_ENGINE_OPTIONS: Dict = {
            "max_overflow": env.int("SQLALCHEMY_MAX_OVERFLOW", default=0),
            "pool_size": env.int("SQLALCHEMY_POOL_SIZE", default=2),
            "pool_timeout": env.int("SQLALCHEMY_POOL_TIMEOUT", default=30),
            "pool_recycle": env.int("SQLALCHEMY_POOL_RECYCLE", default=600),
            "pool_pre_ping": env.bool("SQLALCHEMY_POOL_PRE_PING", default=True),
            "executemany_mode": env.str(
                "SQLALCHEMY_EXECUTEMANY_MODE", default="values"
            ),
        }


def is_production_environment(environment: str = None) -> bool:
    if environment is None:
        environment = env.str("ENVIRONMENT", default="PRODUCTION")

    return environment not in ("DEMO", "DEVELOPMENT", "STAGING", "TRAINING", "TEST")


def is_not_production_environment(environment: str = None) -> bool:
    return not is_production_environment(environment=environment)
