import json
import os

from flask import Blueprint, jsonify, render_template, request
from pylti1p3.contrib.flask import (
    FlaskOIDCLogin,
    FlaskMessageLaunch,
    FlaskRequest,
)

bp = Blueprint("lti", __name__)


def _get_deps():
    """Get shared dependencies from Flask app config."""
    from flask import current_app

    return (
        current_app.config["TOOL_CONF"],
        current_app.config["LTI_CACHE"],
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    tool_conf, cache = _get_deps()
    flask_request = FlaskRequest()
    launch_url = os.environ["FUNCTION_URL"] + "/launch"

    oidc_login = FlaskOIDCLogin(flask_request, tool_conf, launch_data_storage=cache)
    return oidc_login.enable_check_cookies().redirect(launch_url)


@bp.route("/launch", methods=["POST"])
def launch():
    tool_conf, cache = _get_deps()
    flask_request = FlaskRequest()

    message_launch = FlaskMessageLaunch(
        flask_request, tool_conf, launch_data_storage=cache
    )
    launch_data = message_launch.get_launch_data()

    name = launch_data.get(
        "name",
        launch_data.get(
            "https://purl.imsglobal.org/spec/lti/claim/ext",
            {},
        )
        .get("user_username", "Unknown User"),
    )

    claims = sorted(launch_data.items(), key=lambda x: x[0])

    return render_template("launch.html", name=name, claims=claims)


@bp.route("/jwks", methods=["GET"])
def jwks():
    tool_conf, _ = _get_deps()
    return jsonify(tool_conf.get_jwks())


@bp.route("/config.xml", methods=["GET"])
def config_xml():
    function_url = os.environ["FUNCTION_URL"]
    return render_template(
        "config.xml",
        launch_url=function_url + "/launch",
        login_url=function_url + "/login",
        jwks_url=function_url + "/jwks",
    ), 200, {"Content-Type": "application/xml"}
