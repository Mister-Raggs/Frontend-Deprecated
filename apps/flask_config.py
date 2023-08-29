# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os, random, string
from apps.common import config_reader


class Config(object):
    basedir = config_reader.config_data.get("Main", "app_base_dir") + "/apps"

    # Assets Management
    ASSETS_ROOT = "/static/assets"

    # Set up the App SECRET_KEY
    SECRET_KEY = os.getenv("SECRET_KEY", None)


class ProductionConfig(Config):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600


class LocalConfig(Config):
    DEBUG = True
    FLASK_ENV = "development"


# Load all possible configurations
config_dict = {"Production": ProductionConfig, "Local": LocalConfig}
