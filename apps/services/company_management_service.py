import os, logging
from flask import make_response, jsonify
from bson import json_util
from flask.wrappers import Request, Response
from werkzeug.utils import secure_filename
from mongoengine.queryset.visitor import Q

from apps.citadel.company_management.forms import AddUpdateCompanyForm
from apps.models.company_model import CompanyModel, CompanyAddress, AddressCountry, check_company_exists_by_full_name
from apps.common import utils
from apps.common.custom_exceptions import CitadelDBException, CitadelIDPWebException, CompanyNotFoundException
from apps.blob_management.company_folder_creator import create_company_folder_structure


def get_company_details_by_row_id(row_id) -> CompanyModel:
    company = CompanyModel.objects(id=row_id).first()
    return company


def handle_company_toggle_activate_delete(company_id, action):
    company: CompanyModel = CompanyModel.objects(pk=company_id).first()
    old_value = False
    new_value = False
    if company:
        if action.lower() == "is_active":
            old_value = company.is_active
            if old_value:
                company.is_active = False
                new_value = False
            else:
                company.is_active = True
                new_value = True
        elif action.lower() == "is_deleted":
            old_value = company.is_deleted
            if old_value:
                company.is_deleted = False
                new_value = False
            else:
                company.is_deleted = True
                new_value = True
        else:
            raise CitadelIDPWebException(f"Invalid toggle action '{action}' requested.")
        company.save()
        logging.info("Successfully toggled '%s' from %s to %s", action, old_value, new_value)
    else:
        msg = f"toggle activate operation failed. No Company found with id {company_id}"
        raise CompanyNotFoundException(msg)


def prepare_companies_list_data(draw, search_value, start_index, page_length):
    """
    prepare_companies_list_data _summary_

    Args:
        draw (_type_): _description_
        search_value (_type_): _description_
        page_start (int): zero based page number. i.e. page 0 means its page 1
        page_length (int): number of records to fetch per page.
    """

    end_index = start_index + page_length
    companies_data = None
    records_total = CompanyModel.objects().count()
    records_filtered = records_total
    if utils.string_is_not_empty(search_value):
        companies_data = CompanyModel.objects(
            Q(full_name__icontains=search_value) | Q(short_name__icontains=search_value)
        )[start_index:end_index]

        # get the count of records also
        records_filtered = CompanyModel.objects(
            Q(full_name__icontains=search_value) | Q(short_name__icontains=search_value)
        ).count()
    else:
        companies_data = CompanyModel.objects[start_index:end_index]

    # logging.info(companies_data)

    response_data = []
    for company in companies_data:
        address_state_city_country_zip = (
            f"{company.address.address_city}, {company.address.address_state}, "
            f"{company.address.address_country.name} - {company.address.address_zip}"
        )
        response_data.append(
            {
                "DT_RowId": str(company.pk),
                "full_name": company.full_name,
                "short_name": company.short_name,
                "address_state_city_country_zip": address_state_city_country_zip,
                "is_active": "Yes" if (company.is_active) else "No",
                "is_deleted": "Yes" if (company.is_deleted) else "No",
            }
        )

    response = {
        "draw": draw,
        "recordsFiltered": records_filtered,
        "recordsTotal": records_total,
        "data": response_data,
    }

    # logging.info("response -> %s", response)
    return jsonify(response)


def save_company_details(form: AddUpdateCompanyForm) -> str:
    # TODO: validate zip code and state and country combo

    # prepare the states dict to use based on country
    states_dict = None
    if form.address_country.data == AddressCountry.US.name:
        address_country = AddressCountry.US
        states_dict = utils.us_states_dict
    else:
        address_country = AddressCountry.CA
        states_dict = utils.ca_states_dict

    # check for update or add new
    company_model = None
    if form.form_type.data == "update" and utils.string_is_not_empty(form.row_id.data):
        company_model = CompanyModel.objects(id=form.row_id.data).first()

    if company_model:
        # update it
        company_address = company_model.address
        company_address.street_name_line_1 = form.address_street_name_line_1.data
        company_address.street_name_line_2 = form.address_street_name_line_2.data
        company_address.address_city = form.address_city.data
        company_address.address_country = address_country
        company_address.address_state = states_dict[form.address_state.data]
        company_address.address_zip = form.address_zip.data

        company_model.full_name = form.full_name.data
        company_model.short_name = form.short_name.data
        company_model.address = company_address
    else:
        # make new
        company_address = CompanyAddress(
            street_name_line_1=form.address_street_name_line_1.data,
            street_name_line_2=form.address_street_name_line_2.data,
            address_city=form.address_city.data,
            address_country=address_country,
            address_state=states_dict[form.address_state.data],
            address_zip=form.address_zip.data,
        )

        # TODO: handle is_active and is_deleted also
        company_model = CompanyModel(
            full_name=form.full_name.data,
            short_name=form.short_name.data,
            address=company_address,
            # contact_numbers = me.ListField(me.EmbeddedDocumentField(ContactNumber), required=True)
        )

    try:
        company_model.save()
        company_model.reload()

        if form.form_type.data == "add" and not utils.string_is_not_empty(form.row_id.data):
            # Create company blob folder structure for new companies
            create_company_folder_structure(str(company_model.pk))
    except:
        raise CitadelDBException(f"Failed to save CompanyModel for company '{form.full_name.data}'.")

    # TODO: create company blog folder structure for incoming documents and for form recognizer result jsons


# TODO: add other form data validations here
def validate_add_update_company_data(form: AddUpdateCompanyForm) -> str:
    if check_company_exists_by_full_name(form.full_name.data, form.row_id.data):
        return "Company with same full name already exists"
    elif not utils.string_is_not_empty(form.short_name.data):
        return "Company short name is mandatory but seems empty."
    elif not utils.string_is_not_empty(form.address_street_name_line_1.data):
        return "Company Street Address 1 is mandatory but seems empty."
    elif not utils.string_is_not_empty(form.address_city.data):
        return "Company Address City is mandatory but seems empty."
    elif not utils.string_is_not_empty(form.address_country.data):
        return "Company Country is mandatory but seems empty."
    elif not utils.string_is_not_empty(form.address_state.data):
        return "Company Address State is mandatory but seems empty."
    elif not utils.string_is_not_empty(form.address_zip.data):
        return "Company Address Zip is mandatory but seems empty."
