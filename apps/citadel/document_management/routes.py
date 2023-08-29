# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from http import HTTPStatus
import logging
from flask import render_template, make_response, request
from apps.citadel.document_management import blueprint
from flask_login import login_required
from apps.common import constants, utils
from apps.services import document_management_service


@blueprint.route(
    "/document_upload",
)
@login_required
def document_upload_page():
    """
    document_upload_page _summary_

    Returns:
        _type_: _description_
    """
    # Detect the current page
    segment = utils.get_segment(request)

    return render_template(
        "citadel/document_upload.html",
        segment=segment,
        max_file_size_allowed_bytes=constants.MAX_FILE_SIZE_ALLOWED_BYTES,
        chunk_size_bytes=constants.CHUNK_SIZE_BYTES,
        max_parallel_file_uploads_allowed=constants.MAX_PARALLEL_FILE_UPLOADS_ALLOWED,
        max_allowed_file_uploads_on_one_page=constants.MAX_ALLOWED_FILE_UPLOADS_ON_ONE_PAGE,
    )


@blueprint.route("/receive_document_upload", methods=["POST"])
@login_required
def receive_document_upload():
    """
    receive_document_upload _summary_

    Returns:
        _type_: _description_
    """
    # logging.info("Request form is: %s", request.form)
    # logging.info("Request files is: %s", request.files)

    # validate file size first
    if "dztotalfilesize" in request.form:
        total_file_size_in_bytes = request.form["dztotalfilesize"]
        if int(total_file_size_in_bytes) > constants.MAX_FILE_SIZE_ALLOWED_BYTES:
            return make_response(
                f"Maximum allowed file size is {constants.MAX_FILE_SIZE_ALLOWED_BYTES} bytes, but the size of this file is {total_file_size_in_bytes} bytes.",
                HTTPStatus.BAD_REQUEST,
            )
        else:
            return document_management_service.handle_document_upload(request)
    else:
        # TODO: return a 404 response for now but we need to change this to proper response
        return render_template("home/page-404.html"), HTTPStatus.NOT_FOUND
