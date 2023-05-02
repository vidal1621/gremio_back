#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Blueprint, Response, request
import json
from ..app import db
import psycopg2.extras
import datetime

mod_dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@mod_dashboard.route('/dashboard_api', methods=['GET'])
def dashboard():
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    data = json.loads(request.data)
    if request.method == 'GET':
        sql_alumnos = """select distinct(a.cod_alumno), cod_usuario,nombre_alumno,cod_planes_pagos,rut_alumno,fecha_nacimiento,fecha_pago,fecha_vencimiento,monto
                        from alumnos a join pagos p using (cod_usuario) where a.cod_usuario=%s"""
        cursor.execute(sql_alumnos, [data['cod_usuario']])
        alumnos_pagos = cursor.fetchall()
        return Response(response=json.dumps(alumnos_pagos, default=str), status=200,
                        mimetype='application/json')