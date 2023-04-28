#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from functools import wraps
from flask import Blueprint, Response, request
import json
from ..app import db
import basicauth
import psycopg2.extras

mod_auth = Blueprint('auth', __name__, url_prefix='/auth')


@mod_auth.route('/checkAuth', methods=['POST'])
def checkAuth():
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    authorization = request.headers.get('Authorization')
    if authorization is not None and "Basic " in authorization:
        username, passwd = basicauth.decode(authorization)
        print(username, passwd)
    email = username
    password = passwd
    exist_user = """select * from usuarios where email = %s and password = %s"""
    cursor.execute(exist_user, [email, password])
    user = cursor.fetchone()
    if user:
        obj ={
            'status': 'ok',
            'user': user
        }
        return Response(response=json.dumps(obj), status=200, mimetype='application/json')
    else:
        return Response('Unauthorized', status=401, mimetype='application/json')


@mod_auth.route('/signup', methods=['POST'])
def signup():
    cursor = db.cursor()
    try:
        data = json.loads(request.data)
        if data['password'] == data['confirmPass']:
            try:
                cursor.execute(
                    "insert into usuarios (nombre_usuario,email,password,cod_tipo_usuario,celular) values (%s,%s,%s,%s,%s)",
                    [data['email'], data['email'], data['password'], 2, int(data['celular'])])
                return Response(response=json.dumps('ok'), status=200, mimetype='application/json')
            except Exception as e:
                print(e)
                return Response(response=json.dumps(e), status=500, mimetype='application/json')
        else:
            return Response(response=json.dumps('error contrasenas'), status=500, mimetype='application/json')

    except:
        print("error no esperado", sys.exc_info())
        return Response(response=json.dumps('error masivo'), status=500, mimetype='application/json')


def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not authenticate(request.headers.get('Authorization')):
            return Response('Unauthorized', 401, mimetype='application/json')

        return func(*args, **kwargs)

    return decorated_view


def authenticate(req):
    authorization = req
    cursor = db.cursor()
    if authorization is not None and "Basic " in authorization:
        username, passwd = basicauth.decode(authorization)
        return username, passwd
