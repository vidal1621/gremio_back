#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Blueprint, Response, request
import json
from ..app import db
import datetime
import psycopg2.extras

mod_maestro= Blueprint('maestro', __name__, url_prefix='/maestro')

@mod_maestro.route('/maestro_pagos_api', methods=['GET','POST'])
def maestro_pagos():
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    data = json.loads(request.data)
    if request.method == 'GET':
        sql_pendiente = "select * from pagos p join alumnos using (cod_usuario) where desc_pagos='Pendiente'"
        cursor.execute(sql_pendiente)
        pendientes = cursor.fetchall()
        sql_pagados = "select * from pagos p join alumnos using (cod_usuario) where desc_pagos='Pagado'"
        cursor.execute(sql_pagados)
        pagados = cursor.fetchall()
        maestro_pagos = {
            'pendientes': pendientes,
            'pagados': pagados
        }
        return Response(response=json.dumps(maestro_pagos, default=str), status=200,
                        mimetype='application/json')
    elif request.method == 'POST':
        sql_pendiente_usuario = "select * from pagos p join alumnos using (cod_usuario) where desc_pago='Pendiente' and cod_usuario=%s"
        cursor.execute(sql_pendiente_usuario, [data['cod_usuario']])
        pendientes_usuario = cursor.fetchall()
        sql_pagados_usuario = "select * from pagos p join alumnos using (cod_usuario) where desc_pago='Pagado' and cod_usuario=%s"
        cursor.execute(sql_pagados_usuario, [data['cod_usuario']])
        pagados_usuario = cursor.fetchall()
        maestro_pagos_usuario = {
            'pendientes': pendientes_usuario,
            'pagados': pagados_usuario
        }
        return Response(response=json.dumps('ok', default=str), status=200,
                        mimetype='application/json')