#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Blueprint, Response, request
import json
from ..app import db
import psycopg2.extras

mod_maestro= Blueprint('maestro', __name__, url_prefix='/maestro')


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