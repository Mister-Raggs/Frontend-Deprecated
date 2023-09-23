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
from apps.models.input_blob_model import InputBlob
from apps.services import document_management_service
from apps.common.custom_exceptions import DocumentNotFoundException, CitadelIDPWebException
from mongoengine.errors import ValidationError


##########################################################################################
# APIs from here - these have /api prefixes
##########################################################################################


@blueprint.route("/api/get_list_document_data", methods=["POST"])
@login_required
def api_get_document_data():
    # Detect the current page
    segment = utils.get_segment(request)
    # logging.info("Request form is: %s", request.form)
    draw = request.form["draw"]
    page_number = int(request.form["start"])
    length = int(request.form["length"])
    search_value = request.form["search[value]"]
    # TODO: validate the request params
    response = document_management_service.prepare_document_list_data(draw, search_value, page_number, length)
    # logging.info("response is -> %s", response)
    return make_response(response, 200)


@blueprint.route("/api/document_toggle_activate_delete", methods=["POST", "GET"])
@login_required
def toggle_document_status():
    document_id = request.form["document_id"]
    action = request.form["action"]
    if utils.string_is_not_empty(document_id) and utils.string_is_not_empty(action):
        try:
            document_management_service.handle_document_toggle_activate_delete(document_id, action)
        except (CitadelIDPWebException, DocumentNotFoundException, ValidationError) as e:
            msg = f"Failed to toggle is active for document id {document_id}"
            logging.exception(msg)
            return make_response(msg, 404)
    else:
        return make_response("Missing document_id parameter.", 400)
    return make_response("Success, 200")


@blueprint.route("/api/get_list_underlying_data", methods=["POST"])
@login_required
def api_get_list_underlying_data():
    # Detect the current page
    segment = utils.get_segment(request)
    # logging.info("Request form is: %s", request.form)
    draw = request.form["draw"]
    page_number = int(request.form["start"])
    length = int(request.form["length"])
    search_value = request.form["search[value]"]
    # TODO: validate the request params
    response = document_management_service.prepare_list_underlying_data(draw, search_value, page_number, length)
    # logging.info("response is -> %s", response)
    return make_response(response, 200)





@blueprint.route("/api/document_preview", methods=["GET"])
@login_required
def api_handle_preview_document_action():
    try:
        document_id = request.args.get("document_id")

        if not document_id:
            return make_response("Missing document_id parameter.", 400)

        preview_image_base64 = document_management_service.handle_document_preview(document_id)
        if preview_image_base64:
            return preview_image_base64
        else:
            return make_response("Preview image not available.", 404)
    except Exception as e:
        msg = f"Error generating document preview: {str(e)}"
        logging.exception(msg)
        return make_response(msg, 500)



##########################################################################################
# Action routes from here
##########################################################################################


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


@blueprint.route(
    "/list_all_documents",
)
@login_required
def show_list_all_documents():
    segment = utils.get_segment(request)
    """
    show_list_all_documents _summary_
    Returns:
        _type_: _description_
    """
    return render_template("citadel/list_all_documents.html", segment=segment)


@blueprint.route(
    "/underlying_documents",
)
@login_required
def show_list_underlying_documents():
    segment = utils.get_segment(request)
    """
    show_underlying_documents _summary_
    Returns:
        _type_: _description_
    """
    return render_template("citadel/underlying_documents.html", segment=segment)
