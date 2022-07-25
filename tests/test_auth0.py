import json
from typing import Dict, Optional

from jose import jwt

from flask_batteries_included.helpers.security.jwk import retrieve_relevant_jwk

JWT = (
    "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6Ik5EYzFNamd5T0VFd1F6STJRME0yUWpaQl"
    "FUSkNSVEEyTmpkRE0wWkNOMFpET1VNMU1FTkJRUSJ9.eyJodHRwczovL2dkbS5kcmF5c29uaGVhbHR"
    "oLmNvbS9tZXRhZGF0YSI6eyJjbGluaWNpYW5faWQiOiJhYTk5IiwibG9jYXRpb25zIjpbeyJuYW1lI"
    "joiTWFuY2hlc3RlciBIb3NwaXRhbCIsImlkIjoiTDIifSx7Im5hbWUiOiJFYXN0bGVpZ2ggSG9zcGl"
    "0YWwiLCJpZCI6IkwxIn1dfSwiaXNzIjoiaHR0cHM6Ly9kcmF5c29uaGVhbHRoLmV1LmF1dGgwLmNvb"
    "S8iLCJzdWIiOiJhdXRoMHw1YWRkZWNjODdmNDdmZDYxNDFmMzFkNDIiLCJhdWQiOlsiaHR0cHM6Ly9"
    "kaG9zLWRldi5kcmF5c29uaGVhbHRoLmNvbS8iLCJodHRwczovL2RyYXlzb25oZWFsdGguZXUuYXV0a"
    "DAuY29tL3VzZXJpbmZvIl0sImlhdCI6MTUyNDQ5Njg0NiwiZXhwIjoxNTI0NTA0MDQ2LCJhenAiOiJ"
    "heUh4QnE2WjJ3czB4RGJKUjRoWU1QZGpGV2ZtUTgwNCIsInNjb3BlIjoib3BlbmlkIn0.Hy-EHB2Va"
    "udciIZhY_4EsvAP9BQpWbYnCyknCTMVZq6C2dq6i6q7ZKX-e5KOuARWnrBpTqX7Gp42R_uEwlkjf9Q"
    "x0kGdSo_L7KfAgUgU2Bq7RGiaf7cttCDI-zmvEo9Vn7uTY0eqeQAjpRtqy66XeQK-gJeOpXNwq5n42"
    "eRiNcX4j1LBn3TsM2Z7kyvzLjlWpICJUeeLbMPCU0vSjWqvCBW158aNL0u6ZNxH_QHL82Fx6DXkYiG"
    "wWDjYLn9c0Fm0vRMBhle6sK7ErxcmmCJia1NUeUp0lm1rqHbpYinglVHCUYg6qJc3Xem2YyZzam43p"
    "4q1sXAwEuInizfFQ3mV0A"
)

JWKS_RAW = (
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


AUTH0_DOMAIN = "https://draysonhealth.eu.auth0.com/"

AUTH0_AUDIENCE = "https://dhos-dev.draysonhealth.com/"

AUTH0_METADATA = "https://gdm.draysonhealth.com/metadata"

VALID_JWT_ALGORITHMS = [
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

AUTH0_EXPIRED_ACCESS_TOKEN = (
    "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6Ik5EYzFNamd5T0VFd1F6STJRME0yUWpaQl"
    "FUSkNSVEEyTmpkRE0wWkNOMFpET1VNMU1FTkJRUSJ9.eyJodHRwczovL2dkbS5kcmF5c29uaGVhbHR"
    "oLmNvbS9tZXRhZGF0YSI6eyJjbGluaWNpYW5faWQiOiJhYTk5IiwibG9jYXRpb25zIjpbeyJuYW1lI"
    "joiTWFuY2hlc3RlciBIb3NwaXRhbCIsImlkIjoiTDIifSx7Im5hbWUiOiJFYXN0bGVpZ2ggSG9zcGl"
    "0YWwiLCJpZCI6IkwxIn1dfSwiaXNzIjoiaHR0cHM6Ly9kcmF5c29uaGVhbHRoLmV1LmF1dGgwLmNvb"
    "S8iLCJzdWIiOiJhdXRoMHw1YWRkZWNjODdmNDdmZDYxNDFmMzFkNDIiLCJhdWQiOlsiaHR0cHM6Ly9"
    "kaG9zLWRldi5kcmF5c29uaGVhbHRoLmNvbS8iLCJodHRwczovL2RyYXlzb25oZWFsdGguZXUuYXV0a"
    "DAuY29tL3VzZXJpbmZvIl0sImlhdCI6MTUyNDQ5Njg0NiwiZXhwIjoxNTI0NTA0MDQ2LCJhenAiOiJ"
    "heUh4QnE2WjJ3czB4RGJKUjRoWU1QZGpGV2ZtUTgwNCIsInNjb3BlIjoib3BlbmlkIn0.Hy-EHB2Va"
    "udciIZhY_4EsvAP9BQpWbYnCyknCTMVZq6C2dq6i6q7ZKX-e5KOuARWnrBpTqX7Gp42R_uEwlkjf9Q"
    "x0kGdSo_L7KfAgUgU2Bq7RGiaf7cttCDI-zmvEo9Vn7uTY0eqeQAjpRtqy66XeQK-gJeOpXNwq5n42"
    "eRiNcX4j1LBn3TsM2Z7kyvzLjlWpICJUeeLbMPCU0vSjWqvCBW158aNL0u6ZNxH_QHL82Fx6DXkYiG"
    "wWDjYLn9c0Fm0vRMBhle6sK7ErxcmmCJia1NUeUp0lm1rqHbpYinglVHCUYg6qJc3Xem2YyZzam43p"
    "4q1sXAwEuInizfFQ3mV0A"
)


def test_auth0_retrieve_jwk_success() -> None:

    jwks = json.loads(JWKS_RAW)

    relevant_jwk: Optional[Dict] = retrieve_relevant_jwk(
        jwks, jwt.get_unverified_header(JWT)
    )
    assert relevant_jwk is not None

    for key, expected_value in {
        "kty": "RSA",
        "kid": "NDc1MjgyOEEwQzI2Q0M2QjZBQTJCRTA2NjdDM0ZCN0ZDOUM1MENBQQ",
        "use": "sig",
        "n": "tCfMYn9_Yjj1uvpa8UpAgSR4U20pkGlmM25dKWAP8e7Ms2R46Kj-Oh"
        "bq05Qc__m-M4FJfTRzuqUXFijnsvWbKX4gTy3rN2P_YCKUukzL175f176IpgiVNO8IxEpu_2ylSKhq"
        "OVzZMMc5zJxJiCgoHORjI0nvxs5BGcXvKAI-rBZUL-0dVIKeiz00E4a3cT7Q8gt_vtP3IPwaRmDOLn"
        "YMwqcizVBd2bJzRqOoSlZoCqdJJEmpbmpXGKonxckNsnd7Fe-_1KlpSDGE9LeA_Zt3zJ_H7w90VQ_G"
        "Ce0nFaoFwxAvt-yb0ebKKFXPfYCBihQz1qGIWDkS6O_OHaRsG3i5SQ",
        "e": "AQAB",
    }.items():

        assert key in relevant_jwk
        assert relevant_jwk[key] == expected_value


def test_auth0_retrieve_jwk_wrong_kid() -> None:

    jwks = json.loads(JWKS_RAW)
    jwks["keys"][0]["kid"] = "12345"

    assert retrieve_relevant_jwk(jwks, jwt.get_unverified_header(JWT)) is None
