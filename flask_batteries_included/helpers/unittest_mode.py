from flask import Flask


def init_unittest_mode(app: Flask) -> None:

    app.testing = True
