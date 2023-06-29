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
        sql_pendiente = """select distinct(a.cod_alumno), a.cod_usuario,nombre_alumno,cod_planes_pagos,rut_alumno,fecha_nacimiento,fecha_pago,fecha_vencimiento,monto,altura,peso,desc_pagos,fecha_emision,cod_pagos,verificado
                        from alumnos a join pagos p using (cod_alumno) where a.cod_usuario=%s and extract(month from fecha_emision)=extract(month from now()) and extract(year from fecha_emision)=extract(year from now())
                        """
        cursor.execute(sql_pendiente, [data['cod_usuario']])
        alumnos = cursor.fetchall()
        planes_pago = "select * from categorias"
        cursor.execute(planes_pago)
        planes = cursor.fetchall()
        convenios_ = "select * from convenios"
        cursor.execute(convenios_)
        convenios = cursor.fetchall()
        object = {
            'alumnos': alumnos,
            'planes': planes,
            'convenios': convenios
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
                    cursor.execute(sql_cod_categoria, [d['cod_categorias']])
                    cod_categoria = cursor.fetchone()
                    estado = 'Pendiente'
                    if d['cod_convenios'] in (5, '5'):  # SIN CONVENIO
                        sql_planes_pago = """select max(precio)precio from planes_pagos where cod_categoria=%s and precio!=0"""
                        cursor.execute(sql_planes_pago, [cod_categoria['cod_categoria']])
                        precio = cursor.fetchone()
                        sql_cod_planes_pagos = """select cod_planes_pagos from planes_pagos where cod_categoria=%s and precio=%s"""
                        cursor.execute(sql_cod_planes_pagos, [cod_categoria['cod_categoria'], precio['precio']])
                        cod_planes_pagos = cursor.fetchone()
                    elif d['cod_convenios'] in (3, '3'):  # BECADO
                        sql_planes_pago = "select precio from planes_pagos where cod_categoria=%s and precio=0"
                        cursor.execute(sql_planes_pago, [cod_categoria['cod_categoria']])
                        precio = cursor.fetchone()
                        sql_cod_planes_pagos = """select cod_planes_pagos from planes_pagos where cod_categoria=%s and precio=%s"""
                        cursor.execute(sql_cod_planes_pagos, [cod_categoria['cod_categoria'], precio['precio']])
                        cod_planes_pagos = cursor.fetchone()
                        estado = 'Pagado'
                    elif d['cod_convenios'] in (1, '1', 2, '2'):  # SAN MARTIN O SANTO TOMAS
                        sql_planes_pago = """select min(precio) precio from planes_pagos where cod_categoria=%s and precio!=0"""
                        cursor.execute(sql_planes_pago, [cod_categoria['cod_categoria']])
                        precio = cursor.fetchone()
                        sql_cod_planes_pagos = """select cod_planes_pagos from planes_pagos where cod_categoria=%s and precio=%s"""
                        cursor.execute(sql_cod_planes_pagos, [cod_categoria['cod_categoria'], precio['precio']])
                        cod_planes_pagos = cursor.fetchone()
                    cursor.execute(
                        "insert into alumnos (cod_usuario,nombre_alumno,rut_alumno,cod_planes_pagos, fecha_nacimiento,altura,peso,cod_categoria,cod_convenios,verificado) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning cod_alumno",
                        [d['cod_usuario'], d['nombre_alumno'], d['rut_alumno'],
                         cod_planes_pagos['cod_planes_pagos'], d['fecha_nacimiento'], d['altura'], d['peso'],
                         cod_categoria['cod_categoria'], d['cod_convenios'], 'false'])
                    cod_alumno = cursor.fetchone()
                    pagos = "insert into pagos (cod_usuario,fecha_emision,fecha_vencimiento, monto, desc_pagos, cod_alumno) values (%s,%s,%s,%s,%s,%s) returning cod_pagos"
                    cursor.execute(pagos,
                                   [data['alumnos'][0]['cod_usuario'], datetime.datetime.now(), datetime.datetime.now(),
                                    precio['precio'],
                                    estado, cod_alumno['cod_alumno']])
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


@mod_alumnos.route('/confimacion_pago', methods=['POST', 'GET'])
def confimacion_pago():
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        req_body = request.get_data()
        current_app.logger.info(req_body)
        token = str(req_body).split("=")[1].replace("'", "")
        current_app.logger.info(token)
        sql_update_pago = "update pagos set desc_pagos='Pagado', fecha_pago=%s where flow_token=%s"
        cursor.execute(sql_update_pago, [datetime.datetime.now(), token])
        sql_usuario = """select email,fecha_pago  from pagos p 
                               join usuarios u using (cod_usuario) 
                               where flow_token=%s"""
        cursor.execute(sql_usuario, [token])
        usuario = cursor.fetchone()
        current_app.logger.info(usuario)
        destinatario = 'christian.mendozac@outlook.com'
        asunto = 'verificacion en el pago'
        contenido = 'pago verificado token: ' + token + ' usuario:' + usuario['email']

        enviar_correo(destinatario, asunto, contenido)
        return Response(response=json.dumps({"mensaje": token}), status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        current_app.logger.info(e)
        destinatario = 'christian.mendozac@outlook.com'
        asunto = 'error en el pago'
        contenido = 'revisa el error en el pago'
        enviar_correo(destinatario, asunto, contenido)
        return Response(response=json.dumps(e), status=500, mimetype='application/json')


def enviar_correo(destinatario, asunto, contenido):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    fromaddr = "xvidaaalx@gmail.com"
    toaddr = destinatario
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = asunto
    body = contenido
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "aymcwztzbleymltv")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
    return True


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
