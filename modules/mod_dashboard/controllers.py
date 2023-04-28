#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Blueprint, Response, request
import json
from ..app import db
import psycopg2.extras
import datetime

mod_dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@mod_dashboard.route('/dashboard_api', methods=['GET','POST'])
def dashboard():
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    data = json.loads(request.data)
    if request.method == 'GET':
        sql_alumnos = "select * from alumnos a join pagos p using (cod_usuario) where a.cod_usuario=%s"
        cursor.execute(sql_alumnos, [data['cod_usuario']])
        alumnos_pagos = cursor.fetchall()
        return Response(response=json.dumps(alumnos_pagos), status=200, mimetype='application/json')
    elif request.method == 'POST':
        dia_vencimiento = datetime.datetime.now().replace(day=10) + datetime.timedelta(days=30)
        pagos = "insert into pagos (cod_usuario,fecha_pago,fecha_vencimiento, monto, desc_pagos) values (%s,%s,%s,%s,%s) returning cod_pagos"
        cursor.execute(pagos,
                       [data['cod_usuario'], datetime.datetime.now(), dia_vencimiento, data['monto'],
                        'Pendiente'])
        cod_pagos = cursor.fetchone()
        data_order = {
            'amount': data['monto'],
            'commerceOrder': cod_pagos['cod_pagos'],
            'currency': 'CLP',
            'email': 'Escuelagremiochile@gmail.com',
            'subject': 'Pago Mensualidad Escuela Gremio',
            'urlConfirmation': 'https://escuelagremiochile.cl/confimacion_pago',
            'urlReturn': 'https//escuelagremiochile.cl/retorno_pago',
        }
        create_payment = payment.create_order(payment_data=PaymentCreate(**data_order))
        return Response(response=json.dumps(alumnos_pagos), status=200, mimetype='application/json')