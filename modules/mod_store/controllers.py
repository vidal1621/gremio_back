#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import string
import sys
from functools import wraps
from flask import Blueprint, Response, request, current_app
import json
from ..app import db
import basicauth
import psycopg2.extras
import datetime
from modules.mod_pagos.controllers import Payment
from modules.mod_pagos.controllers import PaymentCreate

mod_store = Blueprint('store', __name__, url_prefix='/store')


