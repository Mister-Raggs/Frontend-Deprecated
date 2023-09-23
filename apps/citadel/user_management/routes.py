# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import logging
from flask import make_response, render_template, request, redirect, url_for, flash
from mongoengine.errors import ValidationError
from flask_login import login_required

from apps.common import utils
from apps.common.custom_exceptions import CitadelIDPWebException, UserSaveException, CompanyNotFoundException
from apps.services import user_management_service
from apps.models.company_model import CompanyModel
from apps.citadel.user_management import blueprint
from apps.citadel.user_management.forms import AddUpdateUserForm


##########################################################################################
# APIs from here - these have /api prefixes
##########################################################################################
@blueprint.route("/api/get_users_data", methods=["POST"])
@login_required
def api_get_users_data():
    # Detect the current page
    segment = utils.get_segment(request)

    draw = request.form["draw"]
    page_number = int(request.form["start"])
    length = int(request.form["length"])
    search_value = request.form["search[value]"]

    # TODO: validate the request params

    response = user_management_service.prepare_users_list_data(draw, search_value, page_number, length)
    # logging.info("response is -> %s", response)
    return make_response(response, 200)


@blueprint.route("/api/user_toggle_activate_delete", methods=["POST"])
@login_required
def company_toggle_activate_delete():
    # Detect the current page
    segment = utils.get_segment(request)

    row_id = request.form["row_id"]
    action = request.form["action"]

    if utils.string_is_not_empty(row_id) and utils.string_is_not_empty(action):
        try:
            user_management_service.handle_user_toggle_activate_delete(row_id, action)
        except (CitadelIDPWebException, UserSaveException, ValidationError) as e:
            msg = f"Failed to toggle is_active for User id {row_id}"
            logging.exception(msg)
            return make_response(msg, 404)
    else:
        return make_response("Missing row_id parameter.", 400)
    return make_response("Success", 200)


##########################################################################################
# Action routes from here
##########################################################################################
@blueprint.route(
    "/admin_list_all_users",
)
@login_required
def admin_list_all_users():
    # Detect the current page
    segment = utils.get_segment(request)

    return render_template("citadel/admin_list_all_users.html", segment=segment)


@blueprint.route("/admin_add_update_user", methods=["GET", "POST"])
@login_required
def admin_add_update_user():
    # initialize form
    form: AddUpdateUserForm = AddUpdateUserForm(request.form)
    companies = [(str(company.id), company.full_name) for company in CompanyModel.objects()]
    companies.insert(0, ("-1", "Choose User Company"))
    form.company.choices = companies

    # Detect the current page
    segment = utils.get_segment(request)

    row_id = request.args.get("row_id")
    # if this an update page load request
    if (row_id is not None) and ("add-update-user-submit" not in request.form):
        form = __create_add_update_user_form_for_update(row_id, form)

    # If the form submit button was pressed
    if "add-update-user-submit" in request.form:
        validation_msg = user_management_service.validate_add_update_user_data(form)
        if utils.string_is_not_empty(validation_msg):
            validation_msg = "Please correct the error and submit again: <br />" + validation_msg
            return render_template(
                "citadel/admin_add_update_user.html",
                msg=validation_msg,
                msg_type="error",
                form=form,
                segment=segment,
            )
        else:
            try:
                user_management_service.save_user_details(form)
                success_msg = f"Successfully saved user details for '{form.first_name.data} {form.last_name.data}'"
                flash(success_msg, "success")
                if form.form_type.data == "update":
                    redirect_url = url_for(
                        "citadel_blueprint.user_management_blueprint.admin_add_update_user",
                        row_id=row_id,
                    )
                else:
                    redirect_url = url_for("citadel_blueprint.user_management_blueprint.admin_add_update_user")
                return redirect(redirect_url)
            except CompanyNotFoundException as c:
                logging.exception(
                    "Failed to save user details. Company with row id '%s' was not found", form.company.data
                )
                return render_template(
                    "citadel/admin_add_update_user.html",
                    msg=(
                        f"Failed to save user details for '{form.first_name.data} {form.last_name.data}'. "
                        "Company with id '{form.company.data}' was not found."
                    ),
                    msg_type="error",
                    form=form,
                    segment=segment,
                )
            except UserSaveException as c:
                logging.exception("Failed to save user details. Submitted form was %s", form)
                return render_template(
                    "citadel/admin_add_update_user.html",
                    msg=(
                        f"Failed to save user details for '{form.first_name.data} {form.last_name.data}' "
                        "due to an Internal Server Error. Please try again later."
                    ),
                    msg_type="error",
                    form=form,
                    segment=segment,
                )

    return render_template("citadel/admin_add_update_user.html", form=form, segment=segment)


def __create_add_update_user_form_for_update(row_id, form: AddUpdateUserForm):
    user = user_management_service.get_user_details_by_row_id(row_id)

    form.form_type.data = "update"
    form.row_id.data = str(user.pk)

    form.salutation.data = user.salutation.value
    form.first_name.data = user.first_name
    form.middle_name.data = user.middle_name
    form.last_name.data = user.last_name
    form.email.data = user.email
    # TODO: find way to remove showing password from update flow. Add another simple form to just update password.
    form.password.data = user.password
    form.confirm_password.data = user.password
    form.company.data = str(user.company.pk)
    form.user_type.data = user.user_type.value
    form.role.data = user.roles[0]

    return form
