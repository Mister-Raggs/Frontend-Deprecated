import logging
import os
import random
from typing import List
import mongoengine as me

from apps.common import utils
from apps.models.company_model import AddressCountry, CompanyAddress, CompanyModel, ContactNumber, ContactNumberType
from apps.models.user_model import UserModel, UserRole, UserSalutationTypes

logging.basicConfig(level=logging.INFO)
me.connect(host="mongodb://127.0.0.1:27017/citadel-idp-db-test-1", alias="citadel_frontend_app")

companies_to_generate = 500


def load_dummy_companies_data():
    for i in range(1, companies_to_generate):
        company: CompanyModel = CompanyModel.objects(full_name="Full Name " + str(i)).first()
        if company is None:
            company_address = CompanyAddress(
                street_name_line_1="6952 CAMPOS AVE " + str(i),
                street_name_line_2="address line 2 - " + str(i),
                address_city="257 - " + str(i) + " Fireweed Ln",
                address_country=AddressCountry.US,
                address_state=utils.us_states_dict["AK"],
                address_zip="99901",
            )
            company = CompanyModel(
                full_name="Company Full Name " + str(i),
                short_name="Company Short " + str(i),
                address=company_address,
                contact_numbers=[
                    ContactNumber(number="+1-416-666-6666", type=ContactNumberType.MOBILE_1),
                    ContactNumber(number="+1-416-777-7777", type=ContactNumberType.MOBILE_2),
                ],
                is_active=True,
                is_deleted=False,
            )
            company.save()
            company.reload()
            logging.info("Successfully created dummy company with full_name %s", company.full_name)


def load_dummy_users_data():
    script_path = os.path.dirname(__file__)

    company_row_ids_list = []
    # get all companies and order by full name asc
    for company in CompanyModel.objects().order_by("+full_name"):
        company_row_ids_list.append(str(company.pk))

    first_names_list = read_file_to_list(f"{script_path}/dummy_users_data/dummy_first_names.txt")
    last_names_list = read_file_to_list(f"{script_path}/dummy_users_data/dummy_last_names.txt")
    emails_list = read_file_to_list(f"{script_path}/dummy_users_data/dummy_emails.txt")
    company_row_ids_list_size = len(company_row_ids_list)

    for i, first_name in enumerate(first_names_list):
        user_model = UserModel(
            salutation=list(UserSalutationTypes)[random.randint(0, 3)],
            first_name=first_name,
            last_name=last_names_list[i],
            email=emails_list[i],
            password="password#1234",
            company=CompanyModel.objects(
                id=company_row_ids_list[random.randint(0, (company_row_ids_list_size - 1))]
            ).first(),
        )

        role: UserRole = None
        if user_model.company.short_name == "AARK Global":
            role = UserRole.ADMIN
        else:
            role = list(UserRole)[random.randint(2, 3)]

        user_model.roles = [role]

        user_model.save()

        logging.info(
            "Successfully created dummy user with name %s %s %s",
            user_model.salutation.value,
            user_model.first_name,
            user_model.last_name,
        )


def read_file_to_list(file_path) -> List[str]:
    data = []
    with open(file_path, "r", encoding="UTF-8") as file:
        for line in file:
            data.append(line.rstrip())
    return data


if __name__ == "__main__":
    load_dummy_companies_data()
    load_dummy_users_data()
