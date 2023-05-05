#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import sys
from functools import wraps
from flask import Blueprint, Response, request
import json
from ..app import db
import basicauth
import psycopg2.extras
import datetime

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
                cursor.execute("""insert into usuarios (nombre_usuario,email,password,cod_tipo_usuario,celular) values (%s,%s,%s,%s,%s)""",
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


@mod_auth.route('/pagos', methods=['POST'])
def pagos():
    try:
        cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        from gremio_back.modules.mod_pagos.controllers import Payment
        from gremio_back.modules.mod_pagos.controllers import PaymentCreate
        data = json.loads(request.data)
        payment = Payment()
        cursor.execute("begin")
        monto_total = 0
        for d in data['alumnos']:
            if d['cod_pagos'] != None:
                cod_pagos = {}
                cod_pagos['cod_pagos'] = d['cod_pagos']
            else:
                dia_vencimiento = datetime.datetime.now().replace(day=10) + datetime.timedelta(days=30)
                pagos = "insert into pagos (cod_usuario,fecha_pago,fecha_vencimiento, monto, desc_pagos,cod_alumno) values (%s,%s,%s,%s,%s,%s) returning cod_pagos"
                cursor.execute(pagos,[d['cod_usuario'], datetime.datetime.now(), dia_vencimiento, d['monto'],'Pendiente', d['cod_alumno']])
                cod_pagos = cursor.fetchone()
            # detalle_pagos = "insert into detalle_pagos (cod_pagos, monto, cod_usuario) values (%s,%s,%s)"
            # cursor.execute(detalle_pagos, [cod_pagos['cod_pagos'], d['monto'], d['cod_usuario']])
            monto_total += d['monto']
        data_order = {
            'amount': monto_total,
            'commerceOrder': cod_pagos['cod_pagos'],
            'currency': 'CLP',
            'email': 'Escuelagremiochile@gmail.com',
            'subject': 'Pago Mensualidad Escuela Gremio',
            'urlConfirmation': 'https://186.64.122.205/alumnos/confimacion_pago',
            'urlReturn': 'https://186.64.122.205/alumno/retorno_pago',
        }
        create_payment = payment.create_order(payment_data=PaymentCreate(**data_order))
        if create_payment.status_code == 200:
            url_pay = create_payment.json()['url'] + '?token=' + create_payment.json()['token']
            cursor.execute("commit")
            return Response(response=json.dumps(url_pay, default=str), status=200, mimetype='application/json')
                # sql_update = "update pagos set flow_token=%s, desc_pagos where cod_pagos=%s"
                # cursor.execute(sql_update, [create_payment.json()['token'], 'Pagado', cod_pagos['cod_pagos']])
        return Response(response=json.dumps('ok', default=str), status=200,
                        mimetype='application/json')
    except Exception as e:
        print(e)
        cursor.execute("rollback")
        return Response(response=json.dumps('error', default=str), status=500,
                        mimetype='application/json')


@mod_auth.route('/recuperar_password', methods=['POST'])
def recuperar_password():
    try:
        cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        data = json.loads(request.data)
        email = data['email']
        cursor.execute("select * from usuarios where email=%s", [email])
        user = cursor.fetchone()
        if user:
            send_mail(user['email'], user['nombre_usuario'], user['password'])
            return Response(response=json.dumps('ok', default=str), status=200,
                            mimetype='application/json')
        else:
            return Response(response=json.dumps('error', default=str), status=500,
                            mimetype='application/json')
    except Exception as e:
        print(e)
        return Response(response=json.dumps('error', default=str), status=500,
                        mimetype='application/json')


def send_mail(email, nombre, password):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    fromaddr = "xvidaaalx@gmail.com"
    toaddr = email
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] ="Recuperacion de password gremio webapp"
    body = "Hola "+nombre+" tu password es: "+password
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "aymcwztzbleymltv")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
    return True


@mod_auth.route('/crear_pagos_cron', methods=['GET'])
def crear_pagos_cron():
    try:
        fecha_actual = datetime.datetime.now()
        cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if fecha_actual.day == 10:
            cursor.execute("select * from alumnos")
            alumnos = cursor.fetchall()
            cursor.execute("begin")
            for a in alumnos:
                dia_vencimiento = datetime.datetime.now().replace(day=10) + datetime.timedelta(days=30)
                sql_plan_asociado = "select monto from alumnos where cod_alumno=%s"
                cursor.execute(sql_plan_asociado, [a['cod_alumno']])
                monto = cursor.fetchone()
                pagos = "insert into pagos (cod_usuario,fecha_pago,fecha_vencimiento, monto, desc_pagos,cod_alumno) values (%s,%s,%s,%s,%s,%s) returning cod_pagos"
                cursor.execute(pagos,[a['cod_usuario'], datetime.datetime.now(), dia_vencimiento, monto, 'Pendiente', a['cod_alumno']])
            cursor.execute("commit")
            return Response(response=json.dumps('ok', default=str), status=200,
                            mimetype='application/json')
    except Exception as e:
        print(e)
        cursor.execute("rollback")
        return Response(response=json.dumps('error', default=str), status=500,
                        mimetype='application/json')