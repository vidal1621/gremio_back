#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Blueprint, Response, request
import json
from ..app import db
import datetime
import psycopg2.extras

mod_alumnos = Blueprint('alumnos', __name__, url_prefix='/alumnos')


@mod_alumnos.route('/alumnos_api', methods=['GET','POST','PUT'])
def alumnos_api():
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    data = json.loads(request.data)
    if request.method == 'GET':
        sql_pendiente = """select distinct(a.cod_alumno), a.cod_usuario,nombre_alumno,cod_planes_pagos,rut_alumno,fecha_nacimiento,fecha_pago,fecha_vencimiento,monto,altura,peso,desc_pagos
                        from alumnos a join pagos p using (cod_alumno) where a.cod_usuario=%s"""
        cursor.execute(sql_pendiente, [data['cod_usuario']])
        alumnos = cursor.fetchall()
        planes_pago = "select * from planes_pagos"
        cursor.execute(planes_pago)
        planes = cursor.fetchall()
        object = {
            'alumnos': alumnos,
            'planes': planes
        }
        return Response(response=json.dumps(object, default=str), status=200,
                        mimetype='application/json')
    elif request.method == 'POST':
        from gremio_back.modules.mod_pagos.controllers import Payment
        from gremio_back.modules.mod_pagos.controllers import PaymentCreate
        payment = Payment()
        try:
            cursor.execute("begin")
            for d in data['alumnos']:
                cursor.execute(
                    "insert into alumnos (cod_usuario,nombre_alumno,rut_alumno,cod_planes_pagos, fecha_nacimiento,altura,peso) values (%s,%s,%s,%s,%s,%s,%s) returning cod_alumno",
                    [d['cod_usuario'], d['nombre_alumno'], d['rut_alumno'],
                     d['cod_planes_pagos'], d['fecha_nacimiento'], d['altura'], d['peso']])
                cod_alumno = cursor.fetchone()
                sql_planes_pago = "select precio from planes_pagos where cod_planes_pagos=%s"
                cursor.execute(sql_planes_pago, [d['cod_planes_pagos']])
                precio = cursor.fetchone()
                # dia_vencimiento = datetime.datetime.now().replace(day=10) + datetime.timedelta(days=30)
                pagos = "insert into pagos (cod_usuario,fecha_pago,fecha_vencimiento, monto, desc_pagos, cod_alumno) values (%s,%s,%s,%s,%s,%s) returning cod_pagos"
                cursor.execute(pagos, [data['alumnos'][0]['cod_usuario'], datetime.datetime.now(), datetime.datetime.now(), precio['precio'],
                                       'Pendiente', cod_alumno['cod_alumno']])
                cod_pagos = cursor.fetchone()
                data_order = {
                    'amount': precio['precio'],
                    'commerceOrder': cod_pagos['cod_pagos'],
                    'currency': 'CLP',
                    'email':  'Escuelagremiochile@gmail.com',
                    'subject': 'Pago Mensualidad Escuela Gremio',
                    'urlConfirmation': 'https://escuelagremiochile.cl/confimacion_pago',
                    'urlReturn': 'https//escuelagremiochile.cl/retorno_pago',
                }
                create_payment = payment.create_order(payment_data=PaymentCreate(**data_order))
                if create_payment.status_code == 200:
                    cursor.execute("update pagos set flow_token=%s, desc_pagos=%s where cod_pagos=%s",
                                   [create_payment.json()['token'], 'Pagado', cod_pagos['cod_pagos']])
            cursor.execute("commit")
            return Response(response=json.dumps('ok', default=str), status=200,
                            mimetype='application/json')
        except Exception as e:
            cursor.execute("rollback")
            print(e)
            return Response(response=json.dumps(e), status=500, mimetype='application/json')
    elif request.method == 'PUT':
        try:
            cursor.execute("begin")
            for d in data['alumnos']:
                cursor.execute(
                    "update alumnos set nombre_alumno=%s,rut_alumno=%s,cod_planes_pagos=%s, fecha_nacimiento=%s,altura=%s,peso=%s where cod_alumno=%s",
                    [d['nombre_alumno'], d['rut_alumno'],
                     d['cod_planes_pagos'], d['fecha_nacimiento'], d['altura'], d['peso'], d['cod_alumno']])
            cursor.execute("commit")

        except Exception as e:
            cursor.execute("rollback")
            print(e)
            return Response(response=json.dumps(e), status=500, mimetype='application/json')
        return Response(response=json.dumps('ok', default=str), status=200,
                        mimetype='application/json')


@mod_alumnos.route('/pagos_view_api', methods=['POST'])
def pagos_view_api():
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    data = json.loads(request.data)
    if request.method == 'POST':
        sql_view_alumno_pago = """ select distinct(a.cod_alumno), a.cod_usuario,nombre_alumno,cod_planes_pagos,rut_alumno,fecha_nacimiento,fecha_pago,fecha_vencimiento,monto,altura,peso,desc_pagos 
        from alumnos a join pagos p using (cod_alumno) where a.cod_alumno=%s"""
        cursor.execute(sql_view_alumno_pago, [data['cod_alumno']])
        pagos = cursor.fetchall()
        return Response(response=json.dumps(pagos, default=str), status=200,
                        mimetype='application/json')