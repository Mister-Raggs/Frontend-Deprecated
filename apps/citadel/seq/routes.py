# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import logging
from flask import render_template, make_response, request
from apps.citadel.seq import blueprint
from flask_login import login_required

from apps.services import seq_handler


@blueprint.route(
    "/seq",
)
# @login_required
def show_seq():
    """
    show_seq_summary_

    Returns:
        _type_: _description_
    """
    return render_template("citadel/seq.html")


@blueprint.route("/receive_seq", methods=["POST"])
# @login_required
def receive_seq():
    """
    receive_seq_summary_

    Returns:
        _type_: _description_
    """
    # logging.info("Request form is: %s", request.form)
    # logging.info("Request files is: %s", request.files)

    return seq_handler.handle_seq(request)

    # return render_template("citadel/seq.html")
