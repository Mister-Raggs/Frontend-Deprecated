import logging
from flask import jsonify
from mongoengine.queryset.visitor import Q

from apps.citadel.user_management.forms import AddUpdateUserForm
from apps.models.company_model import CompanyModel
from apps.models.user_model import UserModel, UserType, UserRole, check_user_exists_by_email
from apps.common import utils
from apps.common.custom_exceptions import (
    CitadelIDPWebException,
    UserNotFoundException,
    UserSaveException,
)


def get_user_details_by_row_id(row_id) -> UserModel:
    user = UserModel.objects(id=row_id).first()
    return user


def handle_user_toggle_activate_delete(row_id, action):
    user: UserModel = UserModel.objects(pk=row_id).first()
    old_value = False
    new_value = False
    if user:
        if action.lower() == "is_active":
            old_value = user.is_active
            if old_value:
                user.is_active = False
                new_value = False
            else:
                user.is_active = True
                new_value = True
        elif action.lower() == "is_deleted":
            old_value = user.is_deleted
            if old_value:
                user.is_deleted = False
                new_value = False
            else:
                user.is_deleted = True
                new_value = True
        else:
            raise CitadelIDPWebException(f"Invalid toggle action '{action}' requested.")

        user.save()
        logging.info("Successfully toggled '%s' from %s to %s", action, old_value, new_value)
    else:
        msg = f"Toggle activate operation failed. No User found with id {row_id}"
        raise UserNotFoundException(msg)


def prepare_users_list_data(draw, search_value, start_index, page_length):
    """
    prepare_users_list_data _summary_

    Args:
        draw (_type_): _description_
        search_value (_type_): _description_
        page_start (int): zero based page number. i.e. page 0 means its page 1
        page_length (int): number of records to fetch per page.
    """

    end_index = start_index + page_length
    users_data = None
    records_total = UserModel.objects().count()
    records_filtered = records_total
    if utils.string_is_not_empty(search_value):
        query = (
            Q(first_name__icontains=search_value)
            | Q(middle_name__icontains=search_value)
            | Q(last_name__icontains=search_value)
            | Q(email__istartswith=search_value)
        )
        users_data = UserModel.objects(query)[start_index:end_index]

        # get the count of records also
        records_filtered = UserModel.objects(query).count()
    else:
        users_data = UserModel.objects[start_index:end_index]

    # logging.info(companies_data)

    response_data = []
    user: UserModel
    for user in users_data:
        user_full_name = f"{user.salutation.value} {user.first_name}"
        if utils.string_is_not_empty(user.middle_name):
            user_full_name += f" {user.middle_name}"
        user_full_name += f" {user.last_name}"

        response_data.append(
            {
                "DT_RowId": str(user.pk),
                "full_name": user_full_name,
                "email": user.email,
                "type_and_role": f"{user.user_type.value.title()}, {user.roles[0].value.title()}",
                "company_name": user.company.full_name,
                "is_active": "Yes" if (user.is_active) else "No",
                "is_deleted": "Yes" if (user.is_deleted) else "No",
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


def save_user_details(form: AddUpdateUserForm) -> str:
    # first check if the user's company is valid and exists or not
    # TODO: we might not need to do this for update form. SO needs a bit of
    # refactoring to avoid DB calls unnecessarily
    company = CompanyModel.objects(id=form.company.data).first()
    if not company:
        raise UserNotFoundException(
            f"User form had company id as {form.company.data} but there is no company by that id",
        )

    # check for update or add new
    user_model: UserModel = None
    if form.form_type.data == "update" and utils.string_is_not_empty(form.row_id.data):
        user_model = UserModel.objects(id=form.row_id.data).first()

    if user_model:
        # update it
        user_model.salutation = form.salutation.data
        user_model.first_name = form.first_name.data
        user_model.middle_name = form.middle_name.data
        user_model.last_name = form.last_name.data
        user_model.email = form.email.data

        # update user's password field only if the form has both pass and confirm pass...
        # i.e the user's password is to be changed too
        if utils.string_is_not_empty(form.password.data) and utils.string_is_not_empty(form.confirm_password.data):
            user_model.password = form.password.data

        __update_user_type_and_role_in_model(form, user_model)

        user_model.company = company

    else:
        # make new
        # TODO: handle is_active and is_deleted also
        # TODO: sha256 hash the password before saving.
        user_model = UserModel(
            salutation=form.salutation.data,
            first_name=form.first_name.data,
            middle_name=form.middle_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data,
            company=company,
        )
        __update_user_type_and_role_in_model(form, user_model)
    try:
        user_model.save()
    except:
        raise UserSaveException(f"Failed to save UserModel for User '{form.first_name.data} {form.last_name.data}'.")


# TODO: add other form data validations here
def validate_add_update_user_data(form: AddUpdateUserForm) -> str:
    if check_user_exists_by_email(form.email.data, form.row_id.data):
        return "Another user with the same email address already exists."
    elif not utils.string_is_not_empty(form.salutation.data):
        return "User salutation is mandatory but seems empty."
    elif not utils.string_is_not_empty(form.first_name.data):
        return "User first name is mandatory but seems empty."
    elif not utils.string_is_not_empty(form.last_name.data):
        return "User last name is mandatory but seems empty."
    elif not utils.string_is_not_empty(form.email.data):
        return "Email is mandatory but seems empty."
    elif (not utils.string_is_not_empty(form.user_type.data)) and (form.user_type.data != "-1"):
        return "User type is mandatory but seems empty."
    elif (not utils.string_is_not_empty(form.company.data)) and (form.company.data != "-1"):
        return "User company is mandatory but seems empty."
    elif (not utils.string_is_not_empty(form.role.data)) and (form.role.data != "-1"):
        return "User role is mandatory but seems empty."

    # pass and confirm pass checks for update and add user forms
    if form.form_type.data == "update":
        # both pass and confirm pass need to be either empty or (not empty and match)
        if (
            utils.string_is_not_empty(form.password.data) or utils.string_is_not_empty(form.confirm_password.data)
        ) and (form.password.data != form.confirm_password.data):
            return "Password and Confirm Password dont match."
    elif form.form_type.data == "add":
        if not utils.string_is_not_empty(form.password.data):
            return "Password is mandatory but seems empty."
        elif not utils.string_is_not_empty(form.confirm_password.data):
            return "Confirm Password is mandatory but seems empty."
        elif form.password.data != form.confirm_password.data:
            return "Password and Confirm Password dont match."
    else:
        return "Invalid form type. Only accepted form types are add or update."


def __update_user_type_and_role_in_model(form: AddUpdateUserForm, user_model: UserModel):
    if form.user_type.data == UserType.AARK_GLOBAL.name:
        user_model.user_type = UserType.AARK_GLOBAL
    else:
        user_model.user_type = UserType.CLIENT

    user_model.roles.clear()
    match form.role.data:
        case UserRole.ADMIN.name:
            user_model.roles.append(UserRole.ADMIN)
        case UserRole.NORMAL.name:
            user_model.roles.append(UserRole.NORMAL)
        case UserRole.CLIENT_ADMIN.name:
            user_model.roles.append(UserRole.CLIENT_ADMIN)
        case _:
            user_model.roles.append(UserRole.CLIENT_NORMAL)

    return user_model
