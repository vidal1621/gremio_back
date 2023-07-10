#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Blueprint, Response, request
import json
from ..app import db
import psycopg2.extras

mod_maestro = Blueprint('maestro', __name__, url_prefix='/maestro')


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


@mod_maestro.route('/maestro_pagos_api', methods=['GET', 'POST'])
def maestro_pagos():
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    data = json.loads(request.data)
    if request.method == 'GET':
        sql_alumnos = """SELECT (fecha_pago) ultima_fecha_pago, desc_pagos, nombre_categoria, nombre_alumno, rut_alumno, fecha_nacimiento, peso, altura,verificado, 
                        cod_convenios, cod_categoria, cod_alumno, cod_planes_pagos
                        FROM alumnos a
                        JOIN categorias c USING (cod_categoria)
                        JOIN pagos p USING (cod_alumno)
                        where extract(month from fecha_vencimiento)=%s and extract(year from fecha_vencimiento)=%s
                        """
        cursor.execute(sql_alumnos, [data['mes'], data['anio']])
        alumnos = cursor.fetchall()
        sql_categoria = "select * from categorias"
        cursor.execute(sql_categoria)
        categorias = cursor.fetchall()
        sql_convenios = "select * from convenios"
        cursor.execute(sql_convenios)
        convenios = cursor.fetchall()
        maestro_pagos = {
            'alumnos_gremio': alumnos,
            'categorias': categorias,
            'convenios': convenios
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
        sql_total_deuda = "select coalesce (sum(monto),0) monto from pagos where desc_pagos='Pendiente' and extract(month from fecha_emision)=%s and extract(year from fecha_emision)=extract(year from now())"
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


@mod_maestro.route('/maestro_verificaciones_alumnos', methods=['POST'])
def maestro_verificaciones_alumnos():
    try:
        cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        data = json.loads(request.data)
        cursor.execute("begin")
        if data['verificado'] == 'true':
            estado= True
        else:
            estado = False
        if data['cod_convenios'] in (3, '3'):  # becado
            sql_cod_planes_pago = "select precio from planes_pagos where cod_categoria=%s and precio=0"
            cursor.execute(sql_cod_planes_pago, [data['cod_categoria']])
            precio = cursor.fetchone()
            sql_cod_planes_pagos = """select cod_planes_pagos from planes_pagos where cod_categoria=%s and precio=%s"""
            cursor.execute(sql_cod_planes_pagos, [data['cod_categoria'], precio['precio']])
            cod_planes_pagos = cursor.fetchone()
        elif data['cod_convenios'] in (5, '5'):  # sin convenios
            sql_planes_pago = """select max(precio)precio from planes_pagos where cod_categoria=%s and precio!=0"""
            cursor.execute(sql_planes_pago, [data['cod_categoria']])
            precio = cursor.fetchone()
            sql_cod_planes_pagos = """select cod_planes_pagos from planes_pagos where cod_categoria=%s and precio=%s"""
            cursor.execute(sql_cod_planes_pagos, [data['cod_categoria'], precio['precio']])
            cod_planes_pagos = cursor.fetchone()
        elif data['cod_convenios'] in (1, '1', '2', 2):  # san martin o santo tomas
            sql_cod_planes_pago = "select min(precio) precio from planes_pagos where cod_categoria=%s"
            cursor.execute(sql_cod_planes_pago, [data['cod_categoria']])
            precio = cursor.fetchone()
            sql_cod_planes_pagos = """select cod_planes_pagos from planes_pagos where cod_categoria=%s and precio=%s"""
            cursor.execute(sql_cod_planes_pagos, [data['cod_categoria'], precio['precio']])
            cod_planes_pagos = cursor.fetchone()
        sql_categoria_alumno = "update alumnos set cod_categoria=%s, verificado=%s, cod_convenios=%s, cod_planes_pagos=%s where cod_alumno=%s"
        cursor.execute(sql_categoria_alumno,
                       [data['cod_categoria'], estado, data['cod_convenios'],
                        cod_planes_pagos['cod_planes_pagos'], data['cod_alumno']])
        sql_update_pagos = "update pagos set desc_pagos=%s, monto=%s  where cod_alumno=%s"
        cursor.execute(sql_update_pagos, [data['desc_pagos'], precio['precio'], data['cod_alumno']])
        cursor.execute("commit")
        return Response(response=json.dumps({'status': 'ok'}), status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        cursor.execute("rollback")
        return Response(response=json.dumps({'status': 'error'}, default=str), status=500, mimetype='application/json')
