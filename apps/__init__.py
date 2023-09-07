# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
import logging

from flask import Flask
from flask_session import Session
from flask_login import LoginManager
from importlib import import_module
from pathlib import Path
from prettytable import PrettyTable
import mongoengine as me

from apps.common import config_reader, constants
from apps.common.custom_exceptions import MissingConfigException
from apps.services.company_folder_creator import create_company_folder_structure
login_manager = LoginManager()


def register_extensions(app):
    login_manager.init_app(app)


def register_blueprints(app: Flask):
    # ---- register citadel blueprints
    from apps.citadel import citadel_blueprint as citadel_blueprint_parent_module

    # scan the citadel blueprints folder for all child blueprints and register them to citadel_blueprint_parent
    app_base_dir = config_reader.config_data.get("Main", "app_base_dir")
    citadel_blueprints_parent_folder = Path(app_base_dir + "/apps/citadel").absolute()
    for child_blueprint_item in os.scandir(citadel_blueprints_parent_folder):
        if child_blueprint_item.is_dir() and not child_blueprint_item.name.startswith("__"):
            logging.info("Registering '%s' blueprint.", child_blueprint_item.name)
            child_blueprint_module = import_module(f"apps.citadel.{child_blueprint_item.name}.routes")
            citadel_blueprint_parent_module.register_blueprint(child_blueprint_module.blueprint)
    app.register_blueprint(citadel_blueprint_parent_module)

    # -- register the other blueprints that came with sample apps
    for module_name in ("authentication", "home"):
        module = import_module("apps.{}.routes".format(module_name))
        app.register_blueprint(module.blueprint)

    # log the registered routes as a table
    pt = PrettyTable()
    pt.align = "l"
    pt.field_names = ["Route", "HTTP Methods", "Handler"]
    for route in app.url_map.iter_rules():
        pt.add_row([route.rule, route.methods, route.endpoint])
        # logging.info("Route: '%s', HTTP Methods: %s, Handler: '%s'", route.rule, route.methods, route.endpoint)
    logging.info("Following routes registered successfully:\n%s", pt.get_string())


def setup_session(app):
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    logging.info(
        "Flask session store is: %s", (config_reader.config_data.get("Main", "app_base_dir") + "/flask-session-store")
    )
    app.config["SESSION_FILE_DIR"] = config_reader.config_data.get("Main", "app_base_dir") + "/flask-session-store"
    session = Session()
    session.init_app(app)


def configure_database(app):
    if config_reader.config_data.has_option("Main", "mongodb-connection-string"):
        mongodb_conn_str = config_reader.config_data.get("Main", "mongodb-connection-string").strip('"')
        logging.info("Using mongodb connection str -> '%s'", mongodb_conn_str)
        me.connect(
            host=mongodb_conn_str,
            alias=constants.MONGODB_CONN_ALIAS,
            appName=constants.MONGODB_CONN_ALIAS,
            maxPoolSize=200,
        )
    else:
        raise MissingConfigException("'mongodb-connection-string' config is missing.")


def __check_and_create_company_data():
    # this import needs to be here to avoid a circular dependency on flask login_manager
    from apps.models.company_model import CompanyModel, ContactNumber, ContactNumberType, CompanyAddress, AddressCountry
    from apps.common import utils

    company: CompanyModel = CompanyModel.objects(full_name="AARK Global Inc.").first()
    if company is None:
        company_address = CompanyAddress(
            street_name_line_1="794 Mcallister St",
            street_name_line_2="",
            address_city="San Francisco",
            address_country=AddressCountry.US,
            address_state=utils.us_states_dict["CA"],
            address_zip="94102",
        )
        company = CompanyModel(
            full_name="AARK Global Inc.",
            short_name="AARK Global",
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
        create_company_folder_structure(company.pk)
        logging.info("Successfully created default company with full_name %s", company.full_name)
    else:
        logging.info("Company data already exists with full_name %s", company.full_name)


def __check_and_create_aark_global_admin_user():
    # this import needs to be here to avoid a circular dependency on flask login_manager
    from apps.models.user_model import UserModel, UserRole, UserType, UserSalutationTypes
    from apps.models.company_model import CompanyModel

    user: UserModel = UserModel.objects(email="test@test.com").first()
    if user is None:
        company: CompanyModel = CompanyModel.objects(full_name="AARK Global Inc.").first()
        user = UserModel(
            salutation=UserSalutationTypes.Mr,
            first_name="Test First Name",
            middle_name="",
            last_name="Test Last Name",
            email="test@test.com",
            password="pass",
            user_type=UserType.AARK_GLOBAL,
            company=company,
            is_active=True,
            is_deleted=False,
            roles=[UserRole.ADMIN],
        )
        user.save()
        user.reload()
        logging.info("Successfully created AARK Global Admin user with email %s and row_id %s", user.email, user.id)
    else:
        logging.info("AARK Global Admin user already exists with email %s and row_id %s", user.email, user.id)


def check_and_load_initial_data():
    logging.info("Starting initial data load....")
    __check_and_create_company_data()
    __check_and_create_aark_global_admin_user()
    logging.info("Finished initial data load....")


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    setup_session(app)
    configure_database(app)
    check_and_load_initial_data()
    return app
