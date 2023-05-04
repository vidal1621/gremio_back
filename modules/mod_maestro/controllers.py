#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Blueprint, Response, request
import json
from ..app import db
import psycopg2.extras

mod_maestro= Blueprint('maestro', __name__, url_prefix='/maestro')


@mod_maestro.route('/maestro_pagos_alumnos_api', methods=['GET', 'POST'])
def maestro_pagos_alumnos():
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    data = json.loads(request.data)
    if request.method == 'GET':
        sql_alumnos = "select * from alumnos where cod_usuario=%s"
        cursor.execute(sql_alumnos, [data['cod_usuario']])
        alumnos_asociados = cursor.fetchall()
        return Response(response=json.dumps(alumnos_asociados, default=str), status=200,
                        mimetype='application/json')
    elif request.method == 'POST':
        sql_alumnos = """select * from pagos where cod_alumno=%s"""
        cursor.execute(sql_alumnos, [data['cod_alumno']])
        maestro_pagos_usuario = cursor.fetchall()
        return Response(response=json.dumps(maestro_pagos_usuario, default=str), status=200,
                        mimetype='application/json')


@mod_maestro.route('/maestro_pagos_api', methods=['GET','POST'])
def maestro_pagos():
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    data = json.loads(request.data)
    if request.method == 'GET':
        sql_alumnos = "select * from alumnos"
        cursor.execute(sql_alumnos)
        alumnos = cursor.fetchall()
        # sql_pagados = "select * from pagos p join alumnos using (cod_alumno) where desc_pagos='Pagado'"
        maestro_pagos = {
            'alumnos_gremio': alumnos,
        }
        return Response(response=json.dumps(maestro_pagos, default=str), status=200,
                        mimetype='application/json')
    elif request.method == 'POST':
        sql_alumnos = """select * from pagos where cod_alumno=%s"""
        cursor.execute(sql_alumnos, [data['cod_alumno']])
        maestro_pagos_usuario = cursor.fetchall()
        return Response(response=json.dumps(maestro_pagos_usuario, default=str), status=200,
                        mimetype='application/json')


@mod_maestro.route('/maestro_totales_api', methods=['POST'])
def maestro_totales_api():
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    data = json.loads(request.data)
    if request.method == 'POST':
        sql_total_pagos = "select coalesce (sum(monto),0) monto from pagos where desc_pagos='Pagado' and extract(month from fecha_pago)=%s and extract(year from fecha_pago)=extract(year from now())"
        cursor.execute(sql_total_pagos, [data['mes']])
        total_pagos = cursor.fetchall()
        sql_total_deuda = "select coalesce (sum(monto),0) monto from pagos where desc_pagos='Pendiente' and extract(month from fecha_pago)=%s and extract(year from fecha_pago)=extract(year from now())"
        cursor.execute(sql_total_deuda, [data['mes']])
        total_deuda = cursor.fetchall()
        sql_total_alumnos = "select count(*) total_alumnos from alumnos"
        cursor.execute(sql_total_alumnos)
        total_alumnos = cursor.fetchall()
        object = {
            'total_pagos': total_pagos,
            'total_deuda': total_deuda,
            'total_alumnos': total_alumnos
        }
        return Response(response=json.dumps(object, default=str), status=200, mimetype='application/json')