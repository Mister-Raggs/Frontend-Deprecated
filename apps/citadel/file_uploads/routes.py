# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import logging
from flask import render_template, make_response, request
from flask_login import login_required

from apps.citadel.file_uploads import blueprint
from apps.services import file_upload_handler


@blueprint.route(
    "/file_upload",
)
# @login_required
def show_file_upload():
    """
    show_file_upload _summary_

    Returns:
        _type_: _description_
    """
    return render_template("citadel/file_upload.html")


@blueprint.route("/receive_file_upload", methods=["POST"])
# @login_required
def receive_file_upload():
    """
    receive_file_upload _summary_

    Returns:
        _type_: _description_
    """
    # logging.info("Request form is: %s", request.form)
    # logging.info("Request files is: %s", request.files)

    return file_upload_handler.handle_file_uploads(request)

    # return render_template("citadel/file_upload.html")
