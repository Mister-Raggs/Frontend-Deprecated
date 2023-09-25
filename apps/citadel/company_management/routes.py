# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import logging
from mongoengine.errors import ValidationError
from flask import make_response, render_template, request, redirect, url_for, flash
from flask_login import login_required

from apps.common import utils
from apps.models.company_model import AddressCountry
from apps.services import company_management_service
from apps.common.custom_exceptions import CitadelIDPWebException, CompanyNotFoundException
from apps.services import company_management_service
from apps.citadel.company_management import blueprint
from apps.citadel.company_management.forms import AddUpdateCompanyForm

##########################################################################################
# APIs from here - these have /api prefixes
##########################################################################################
@blueprint.route("/api/get_companies_data", methods=["POST"])
@login_required
def api_get_companies_data():
    # Detect the current page
    segment = utils.get_segment(request)

    # logging.info("Request form is: %s", request.form)

    draw = request.form["draw"]
    page_number = int(request.form["start"])
    length = int(request.form["length"])
    search_value = request.form["search[value]"]

    # TODO: validate the request params

    response = company_management_service.prepare_companies_list_data(draw, search_value, page_number, length)
    # logging.info("response is -> %s", response)
    return make_response(response, 200)


@blueprint.route("/api/company_toggle_activate_delete", methods=["POST"])
@login_required
def company_toggle_activate_delete():
    # Detect the current page
    segment = utils.get_segment(request)

    company_id = request.form["company_id"]
    action = request.form["action"]

    if utils.string_is_not_empty(company_id) and utils.string_is_not_empty(action):
        try:
            company_management_service.handle_company_toggle_activate_delete(company_id, action)
        except (CitadelIDPWebException, CompanyNotFoundException, ValidationError) as e:
            msg = f"Failed to toggle is_active for Company id {company_id}"
            logging.exception(msg)
            return make_response(msg, 404)
    else:
        return make_response("Missing company_id parameter.", 400)
    return make_response("Success", 200)


##########################################################################################
# Action routes from here
##########################################################################################
@blueprint.route(
    "/admin_list_all_companies",
)
@login_required
def admin_list_all_companies():
    # Detect the current page
    segment = utils.get_segment(request)

    # form for the update company control sidebar
    add_update_company_form = AddUpdateCompanyForm(request.form)

    return render_template(
        "citadel/admin_list_all_companies/admin_list_all_companies.html", segment=segment, form=add_update_company_form
    )


@blueprint.route("/admin_add_update_company", methods=["GET", "POST"])
@login_required
def admin_add_update_company():
    add_update_company_form = AddUpdateCompanyForm(request.form)

    # Detect the current page
    segment = utils.get_segment(request)

    row_id = request.args.get("row_id")
    # if this an update page load request
    if (row_id is not None) and ("add-update-company-submit" not in request.form):
        add_update_company_form = __create_add_update_company_form_for_update(row_id, add_update_company_form)

    # If the form submit button was pressed
    if "add-update-company-submit" in request.form:
        validation_msg = company_management_service.validate_add_update_company_data(add_update_company_form)
        if utils.string_is_not_empty(validation_msg):
            validation_msg = "Please correct the error and submit again: <br />" + validation_msg
            return render_template(
                "citadel/admin_add_update_company.html",
                msg=validation_msg,
                msg_type="error",
                form=add_update_company_form,
                segment=segment,
            )
        else:
            try:
                company_management_service.save_company_details(add_update_company_form)
                success_msg = f"Successfully saved company details for '{add_update_company_form.short_name.data}'"
                flash(success_msg, "success")
                if add_update_company_form.form_type.data == "update":
                    redirect_url = url_for(
                        "citadel_blueprint.company_management_blueprint.admin_add_update_company",
                        row_id=row_id,
                    )
                else:
                    redirect_url = url_for("citadel_blueprint.company_management_blueprint.admin_add_update_company")
                return redirect(redirect_url)
            except CitadelIDPWebException as c:
                logging.exception("Failed to save company details. Submitted form was %s", add_update_company_form)
                return render_template(
                    "citadel/admin_add_update_company.html",
                    msg=(
                        f"Failed to save company details for company '{add_update_company_form.full_name.data}' "
                        "due to an Internal Server Error. Please try again later."
                    ),
                    msg_type="error",
                    form=add_update_company_form,
                    segment=segment,
                )
    else:
        return render_template("citadel/admin_add_update_company.html", form=add_update_company_form, segment=segment)


def __create_add_update_company_form_for_update(row_id, add_update_company_form):
    company = company_management_service.get_company_details_by_row_id(row_id)

    add_update_company_form.form_type.data = "update"
    add_update_company_form.row_id.data = str(company.pk)

    # set the key for state based on country
    addressCountry = company.address.address_country
    states_dict = None
    if addressCountry == AddressCountry.US:
        states_dict = utils.us_states_dict
    else:
        states_dict = utils.ca_states_dict

    state_value_key = None

    for key, value in states_dict.items():
        if company.address.address_state == value:
            state_value_key = key
            break

    add_update_company_form.address_state_option_value_for_update.data = state_value_key

    add_update_company_form.full_name.data = company.full_name
    add_update_company_form.short_name.data = company.short_name
    add_update_company_form.address_street_name_line_1.data = company.address.street_name_line_1
    add_update_company_form.address_street_name_line_2.data = company.address.street_name_line_2
    add_update_company_form.address_country.data = company.address.address_country.name
    add_update_company_form.address_state.data = company.address.address_state
    add_update_company_form.address_city.data = company.address.address_city
    add_update_company_form.address_zip.data = company.address.address_zip
    return add_update_company_form
