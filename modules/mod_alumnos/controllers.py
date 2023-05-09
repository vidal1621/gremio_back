#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from flask import Blueprint, Response, request, current_app
import json
from ..app import db
import datetime
import psycopg2.extras

mod_alumnos = Blueprint('alumnos', __name__, url_prefix='/alumnos')


@mod_alumnos.route('/alumnos_api', methods=['GET', 'POST', 'PUT'])
def alumnos_api():
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    data = json.loads(request.data)
    if request.method == 'GET':
        sql_pendiente = """select distinct(a.cod_alumno), a.cod_usuario,nombre_alumno,cod_planes_pagos,rut_alumno,fecha_nacimiento,fecha_pago,fecha_vencimiento,monto,altura,peso,desc_pagos,fecha_emision,cod_pagos
                        from alumnos a join pagos p using (cod_alumno) where a.cod_usuario=%s and extract(month from fecha_emision)=%s and extract(year from fecha_emision)=extract(year from now())"""
        cursor.execute(sql_pendiente, [data['cod_usuario'], data['mes']])
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
        try:
            cursor.execute("begin")
            for d in data['alumnos']:
                sql_alumno_existente = "select * from alumnos where rut_alumno=%s"
                cursor.execute(sql_alumno_existente, [d['rut_alumno']])
                alumno_existente = cursor.fetchone()
                if alumno_existente:
                    print(alumno_existente)
                else:
                    sql_cod_categoria = "select cod_categoria from planes_pagos where cod_planes_pagos=%s"
                    cursor.execute(sql_cod_categoria, [d['cod_planes_pagos']])
                    cod_categoria = cursor.fetchone()
                    cursor.execute(
                        "insert into alumnos (cod_usuario,nombre_alumno,rut_alumno,cod_planes_pagos, fecha_nacimiento,altura,peso,cod_categoria) values (%s,%s,%s,%s,%s,%s,%s,%s) returning cod_alumno",
                        [d['cod_usuario'], d['nombre_alumno'], d['rut_alumno'],
                         d['cod_planes_pagos'], d['fecha_nacimiento'], d['altura'], d['peso'], cod_categoria['cod_categoria']])
                    cod_alumno = cursor.fetchone()
                    sql_planes_pago = "select precio from planes_pagos where cod_planes_pagos=%s"
                    cursor.execute(sql_planes_pago, [d['cod_planes_pagos']])
                    precio = cursor.fetchone()
                    pagos = "insert into pagos (cod_usuario,fecha_emision,fecha_vencimiento, monto, desc_pagos, cod_alumno) values (%s,%s,%s,%s,%s,%s) returning cod_pagos"
                    cursor.execute(pagos,
                                   [data['alumnos'][0]['cod_usuario'], datetime.datetime.now(), datetime.datetime.now(),
                                    precio['precio'],
                                    'Pendiente', cod_alumno['cod_alumno']])
            cursor.execute("commit")
            return Response(response=json.dumps('ok', default=str), status=200, mimetype='application/json')
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


@mod_alumnos.route('/confimacion_pago', methods=['POST'])
def confimacion_pago():
    try:
        cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        req_body = request.get_data()
        token = str(req_body).split("=")[1].replace("'", "")
        cursor.execute("begin")
        current_app.logger.info(token)
        sql_update_pago = "update pagos set desc_pagos='Pagado', fecha_pago=%s where flow_token=%s"
        cursor.execute(sql_update_pago, [datetime.datetime.now(), token])
        cursor.execute("commit")
        # print(token)
        # logging.info(request.is_json, request.get_data(), request.__dict__)
        logging.info(token)
        return Response(response=json.dumps({"mensaje": token}), status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        cursor.execute("rollback")
        return Response(response=json.dumps(e), status=500, mimetype='application/json')


@mod_alumnos.route('/retorno_pago', methods=['POST'])
def retorno_pago():
    try:
        cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        req_body = request.body()
        token = str(req_body).split("=")[1].replace("'", "")
        cursor.execute("begin")
        sql_update_pago = "update pagos set flow_token=%s, fecha_pago=%s"
        cursor.execute(sql_update_pago, [token, datetime.datetime.now()])
        cursor.execute("commit")
        return True

    except Exception as e:
        print(e)
        cursor.execute("rollback")
        return Response(response=json.dumps(e), status=500, mimetype='application/json')
