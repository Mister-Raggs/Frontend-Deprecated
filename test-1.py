from apps.models.user_model import UserModel, UserSalutationTypes
import mongoengine as me
from mongoengine.queryset.visitor import Q
from apps.models.company_model import CompanyModel, ContactNumber, ContactNumberType, CompanyAddress, AddressCountry
from apps.common import utils
import logging

me.connect(host="mongodb://127.0.0.1:27017/citadel-idp-db-test-1", alias="citadel_frontend_app")
# user = UserModel(
#     email="test@test.com",
#     password="pass",
#     user_type=UserType.AARK_GLOBAL,
#     is_active=True,
#     is_deleted=False,
#     roles=[UserRole.ADMIN],
# )

# user.save()

print(UserSalutationTypes.Mr.value)
model = CompanyModel
pk = "64d15c9fe9d9ba374672d19b"

# print(model._get_db())
# print("-------")
# print(model._get_collection())
# print("-------")
# print(model._get_collection_name())
# print("-------")
data = model.objects()
for company in CompanyModel.objects():
    print(company.full_name + ", " + str(company.id))

# data = model.objects().only("full_name")[10:20]
# print(data)
# data = model.objects().only("full_name")[20:30]
# print(data)


# for i in range(1, 100):
#     company: CompanyModel = CompanyModel.objects(full_name="Full Name " + str(i)).first()
#     if company is None:
#         company_address = CompanyAddress(
#             street_name_line_1="6952 CAMPOS AVE " + str(i),
#             street_name_line_2="address line 2 - " + str(i),
#             address_city="JBER - " + str(i),
#             address_country=AddressCountry.US,
#             address_state=utils.us_states_dict["AK"],
#             address_zip="99506-3427",
#         )
#         company = CompanyModel(
#             full_name="Full Name " + str(i),
#             short_name="Short " + str(i),
#             address=company_address,
#             contact_numbers=[
#                 ContactNumber(number="+1-416-666-6666", type=ContactNumberType.MOBILE_1),
#                 ContactNumber(number="+1-416-777-7777", type=ContactNumberType.MOBILE_2),
#             ],
#             is_active=True,
#             is_deleted=False,
#         )
#         company.save()
#         company.reload()
#         logging.info("Successfully created default company with full_name %s", company.full_name)
