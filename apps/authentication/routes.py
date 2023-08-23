# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import logging

from flask import render_template, redirect, request, url_for, session
from flask_login import current_user, login_user, logout_user
from apps import login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.common import constants
from apps.authentication.util import verify_pass
from apps.models.user_model import UserModel, get_user_by_email, verify_user_password


@blueprint.route("/")
def route_default():
    return redirect(url_for("authentication_blueprint.login"))


# Login & Registration
@blueprint.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm(request.form)
    if "login" in request.form:
        # read form data
        email = request.form["email"]
        password = request.form["password"]

        # Locate user
        user = get_user_by_email(email)

        msg = ""
        if user:
            if user.is_active:
                if not user.is_deleted:
                    if user.company.is_active:
                        if not user.company.is_deleted:
                            # all is good from activation and deletion perspective...check passwords now
                            if verify_user_password(password, user.password):
                                login_user(user)
                                populate_login_session(user)
                                logging.info("Successfully logged in user email: %s", session.get("user_email"))
                                return redirect(url_for("authentication_blueprint.route_default"))
                            else:
                                msg = "Wrong email or password."
                                logging.error("User '%s' email and password don't match.", email)
                        else:
                            msg = "User's company is deactivated."
                            logging.error(
                                "User '%s' belongs to company '%s' which is soft deleted.",
                                email,
                                user.company.short_name,
                            )
                    else:
                        msg = "User's company is deactivated."
                        logging.error(
                            "User '%s' belongs to company '%s' which is inactive.", email, user.company.short_name
                        )
                else:
                    msg = "User account is deactivated."
                    logging.error("User '%s' is soft deleted.", email)
            else:
                msg = "User account is deactivated."
                logging.error("User '%s' is inactive.", email)
        else:
            msg = "Wrong email or password."
            logging.error("User not found with email '%s'", email)

        # log all scenarios cases for auditing purposes but always send a
        # single general msg back to browser
        return render_template("accounts/login.html", msg=msg, form=login_form)

    if not current_user.is_authenticated:
        return render_template("accounts/login.html", form=login_form)
    return redirect(url_for("home_blueprint.index"))


# @blueprint.route("/register", methods=["GET", "POST"])
# def register():
#     create_account_form = CreateAccountForm(request.form)
#     if "register" in request.form:
#         email = request.form["email"]

#         # Check usename exists
#         user = UserModel.objects(email=email).first()
#         if user:
#             return render_template(
#                 "accounts/register.html", msg="User by this email already registered", success=False, form=create_account_form
#             )

#         # else we can create the user
#         user = Users(**request.form)
#         db.session.add(user)
#         db.session.commit()

#         # Delete user from session
#         logout_user()

#         return render_template(
#             "accounts/register.html", msg="User created successfully.", success=True, form=create_account_form
#         )

#     else:
#         return render_template("accounts/register.html", form=create_account_form)


@blueprint.route("/logout")
def logout():
    logout_user()
    logging.info("Successfully logged out user email: %s", session.get("user_email"))
    session.clear()
    return redirect(url_for("authentication_blueprint.login"))


# Errors
@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template("home/page-403.html"), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template("home/page-403.html"), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template("home/page-404.html"), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template("home/page-500.html"), 500


def populate_login_session(user_model: UserModel):
    session[constants.SESSION_USER_ROW_ID_KEY] = str(user_model.pk)
    session[constants.SESSION_FIRST_NAME_KEY] = user_model.first_name
    session[constants.SESSION_USER_MIDDLE_NAME_KEY] = user_model.middle_name
    session[constants.SESSION_USER_LAST_NAME_KEY] = user_model.last_name
    session[constants.SESSION_USER_EMAIL_KEY] = user_model.email
    session[constants.SESSION_USER_ROLE_KEY] = user_model.roles[0]
