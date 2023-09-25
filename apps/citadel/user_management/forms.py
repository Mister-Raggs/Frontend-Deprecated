import re
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, EmailField, PasswordField
from wtforms.validators import DataRequired, Email

from apps.common import utils


def validate_address_zip(form, field):
    zip = field.data
    # US zip code regex check
    m = re.search(r"^\d{5}(-{0,1}\d{4})?$", zip)
    if not m:
        # Canada zip code regex check
        m = re.search(r"^[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z][ -]?\d[ABCEGHJ-NPRSTV-Z]\d$", zip, flags=re.IGNORECASE)
        return True if m else False
    else:
        return True


class AddUpdateUserForm(FlaskForm):
    # hidden fields
    form_type = HiddenField("Form Type", id="form_type", name="form_type", default="add", validators=[DataRequired()])
    row_id = HiddenField("Row Id", id="row_id", name="row_id")

    salutation = SelectField(
        "Salutation",
        id="salutation",
        name="salutation",
        choices=list(utils.user_salutations_dict.items()),
        validators=[DataRequired()],
    )
    first_name = StringField("First Name", id="first_name", name="first_name", validators=[DataRequired()])
    middle_name = StringField("Middle Name", id="middle_name", name="middle_name")
    last_name = StringField("Last Name", id="last_name", name="last_name", validators=[DataRequired()])
    email = EmailField("Email", id="email", name="email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", id="password", name="password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", id="confirm_password", name="confirm_password", validators=[DataRequired()]
    )
    user_type = SelectField(
        "User Type",
        id="user_type",
        name="user_type",
        choices=list(utils.user_type_dict.items()),
        validators=[DataRequired()],
    )
    company = SelectField(
        "User Type",
        id="company",
        name="company",
        validators=[DataRequired()],
    )
    role = SelectField(
        "User Role",
        id="role",
        name="role",
        choices=list(utils.user_role_dict.items()),
        validators=[DataRequired()],
    )
