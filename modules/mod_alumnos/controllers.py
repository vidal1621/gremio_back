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


def registro_alumno_correo(destinatario, password):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    fromaddr = "xvidaaalx@gmail.com"
    toaddr = [destinatario, "xvidaaalx@gmail.com"]
    for to in toaddr:
        msg = MIMEMultipart('related')
        msg['From'] = fromaddr
        msg['To'] = to
        msg['Subject'] = "Registro de usuario GREMIO"
        contenido_html = """
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office">

<head>
    <meta charset="UTF-8">
    <meta content="width=device-width, initial-scale=1" name="viewport">
    <meta name="x-apple-disable-message-reformatting">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta content="telephone=no" name="format-detection">
    <title></title>
    <!--[if (mso 16)]>
    <style type="text/css">
    a {text-decoration: none;}
    </style>
    <![endif]-->
    <!--[if gte mso 9]><style>sup { font-size: 100% !important; }</style><![endif]-->
    <!--[if gte mso 9]>
<xml>
    <o:OfficeDocumentSettings>
    <o:AllowPNG></o:AllowPNG>
    <o:PixelsPerInch>96</o:PixelsPerInch>
    </o:OfficeDocumentSettings>
</xml>
<![endif]-->
    <!--[if !mso]><!-- -->
    <link href="https://fonts.googleapis.com/css2?family=Imprima&display=swap" rel="stylesheet">
    <!--<![endif]-->
</head>

<body>
    <div class="es-wrapper-color">
        <!--[if gte mso 9]>
			<v:background xmlns:v="urn:schemas-microsoft-com:vml" fill="t">
				<v:fill type="tile" color="#ffffff"></v:fill>
			</v:background>
		<![endif]-->
        <table class="es-wrapper" width="100%" cellspacing="0" cellpadding="0">
            <tbody>
                <tr>
                    <td class="esd-email-paddings" valign="top">
                    
                        <table cellpadding="0" cellspacing="0" class="es-content" align="center">
                            <tbody>
                                <tr>
                                    <td class="esd-stripe" align="center">
                                        <table bgcolor="#efefef" class="es-content-body" align="center" cellpadding="0" cellspacing="0" width="600" style="border-radius: 20px 20px 0 0 ">
                                            <tbody>
                                                <tr>
                                                    <td class="esd-structure es-p40t es-p40r es-p40l" align="left">
                                                        <table cellpadding="0" cellspacing="0" width="100%">
                                                            <tbody>
                                                                <tr>
                                                                    <td width="520" class="esd-container-frame" align="center" valign="top">
                                                                        <table cellpadding="0" cellspacing="0" width="100%">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td align="left" class="esd-block-image es-m-txt-c" style="font-size: 0px;"><a target="_blank" href=""https://escuelagremiochile.cl/static/assets/images/gremio/logo.png alt="Gremio" style="display: block; border-radius: 100px;" width="100" title="Gremio"></a></td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td class="es-p20t es-p40r es-p40l esd-structure" align="left">
                                                        <table cellpadding="0" cellspacing="0" width="100%">
                                                            <tbody>
                                                                <tr>
                                                                    <td width="520" class="esd-container-frame" align="center" valign="top">
                                                                        <table cellpadding="0" cellspacing="0" width="100%" bgcolor="#fafafa" style="background-color: #fafafa; border-radius: 10px; border-collapse: separate;">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td align="left" class="esd-block-text es-p20">
                                                                                        <h3>Bienvenido,&nbsp;"""+ destinatario +"""</h3>
                                                                                        <p><br></p>
                                                                                        <p>Muchas gracias por registrarte en la escuela de futbol de Gremio <br><br> tu usuario es: """+ destinatario +"""<br> tu clave ingresada es: """+ str(password) +"""<br> 
                                                                                        ¡Es un honor y un placer darte la más cálida bienvenida a la Escuela de Fútbol de Gremio! Queremos expresar nuestro entusiasmo por contar con un talento como el tuyo en nuestra familia futbolística. <br>
                                                                                        Aquí, te esperan emocionantes aventuras, aprendizajes inolvidables y la oportunidad de crecer tanto dentro como fuera del campo.<br>
Como parte de la familia de Gremio, te aseguramos que recibirás una formación de primer nivel, guiada por entrenadores apasionados y experimentados que están comprometidos con tu desarrollo futbolístico. Nuestra misión es fomentar y nutrir tus habilidades, impulsando tu potencial al máximo para que alcances tus metas deportivas.</p>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <table cellpadding="0" cellspacing="0" class="es-content" align="center">
                            <tbody>
                                <tr>
                                    <td class="esd-stripe" align="center">
                                        <table bgcolor="#efefef" class="es-content-body" align="center" cellpadding="0" cellspacing="0" width="600">
                                            <tbody>
                                                
                                                <tr>
                                                    <td class="esd-structure es-p40r es-p40l" align="left">
                                                        <table cellpadding="0" cellspacing="0" width="100%">
                                                            <tbody>
                                                                <tr>
                                                                    <td width="520" class="esd-container-frame" align="center" valign="top">
                                                                        <table cellpadding="0" cellspacing="0" width="100%">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td align="left" class="esd-block-text">
                                                                                        <p>Gremio<br></p>
                                                                                    </td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td align="center" class="esd-block-spacer es-p40t es-p20b" style="font-size:0">
                                                                                        <table border="0" width="100%" height="100%" cellpadding="0" cellspacing="0">
                                                                                            <tbody>
                                                                                                <tr>
                                                                                                    <td style="border-bottom: 1px solid #666666; background: unset; height: 1px; width: 100%; margin: 0px;"></td>
                                                                                                </tr>
                                                                                            </tbody>
                                                                                        </table>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <table cellpadding="0" cellspacing="0" class="es-content" align="center">
                            <tbody>
                                <tr>
                                    <td class="esd-stripe" align="center">
                                        <table bgcolor="#efefef" class="es-content-body" align="center" cellpadding="0" cellspacing="0" width="600" style="border-radius: 0 0 20px 20px">
                                            <tbody>
                                                <tr>
                                                    <td class="esd-structure es-p20t es-p20b es-p40r es-p40l esdev-adapt-off" align="left">
                                                        <table width="520" cellpadding="0" cellspacing="0" class="esdev-mso-table">
                                                            <tbody>
                                                                <tr>
                                                                    <td class="esdev-mso-td" valign="top">
                                                                        <table cellpadding="0" cellspacing="0" align="left" class="es-left">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td width="47" class="esd-container-frame" align="center" valign="top">
                                                                                        <table cellpadding="0" cellspacing="0" width="100%">
                                                                                            <tbody>
                                                                                                <tr>
                                                                                                    <td align="center" class="esd-block-image es-m-txt-l" style="font-size: 0px;"><a target="_blank" href="https://viewstripo.email"><img src="https://tlr.stripocdn.email/content/guids/CABINET_ee77850a5a9f3068d9355050e69c76d26d58c3ea2927fa145f0d7a894e624758/images/group_4076325.png" alt="Demo" style="display: block;" width="47" title="Demo"></a></td>
                                                                                                </tr>
                                                                                            </tbody>
                                                                                        </table>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                    <td width="20"></td>
                                                                    <td class="esdev-mso-td" valign="top">
                                                                        <table cellpadding="0" cellspacing="0" class="es-right" align="right">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td width="453" class="esd-container-frame" align="center" valign="top">
                                                                                        <table cellpadding="0" cellspacing="0" width="100%">
                                                                                            <tbody>
                                                                                                <tr>
                                                                                                    <td align="left" class="esd-block-text">
                                                                                                        <p style="font-size: 16px;">Este correo es seguro, <a target="_blank" style="font-size: 16px;" href="https://escuelagremiochile.cl"></a></p>
                                                                                                    </td>
                                                                                                </tr>
                                                                                            </tbody>
                                                                                        </table>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <table cellpadding="0" cellspacing="0" class="es-footer" align="center">
                            <tbody>
                                <tr>
                                    <td class="esd-stripe" align="center">
                                        <table bgcolor="#bcb8b1" class="es-footer-body" align="center" cellpadding="0" cellspacing="0" width="600">
                                            <tbody>
                                                <tr>
                                                    <td class="esd-structure es-p40t es-p30b es-p20r es-p20l" align="left" esd-custom-block-id="853188">
                                                        <table cellpadding="0" cellspacing="0" width="100%">
                                                            <tbody>
                                                                <tr>
                                                                    <td width="560" align="left" class="esd-container-frame">
                                                                        <table cellpadding="0" cellspacing="0" width="100%">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td align="center" class="esd-block-social es-m-txt-c es-p10t es-p20b" style="font-size:0">
                                                                                        <table cellpadding="0" cellspacing="0" class="es-table-not-adapt es-social">
                                                                                            <tbody>
                                                                                                <tr>
                                                                                                    <td align="center" valign="top" esd-tmp-icon-type="twitter" class="es-p5r"><a target="_blank" href><img src="https://tlr.stripocdn.email/content/assets/img/social-icons/logo-black/twitter-logo-black.png" alt="Tw" title="Twitter" height="24"></a></td>
                                                                                                    <td align="center" valign="top" esd-tmp-icon-type="facebook" class="es-p5r"><a target="_blank" href><img src="https://tlr.stripocdn.email/content/assets/img/social-icons/logo-black/facebook-logo-black.png" alt="Fb" title="Facebook" height="24"></a></td>
                                                                                                    <td align="center" valign="top" esd-tmp-icon-type="linkedin"><a target="_blank" href><img src="https://tlr.stripocdn.email/content/assets/img/social-icons/logo-black/linkedin-logo-black.png" alt="In" title="Linkedin" height="24"></a></td>
                                                                                                </tr>
                                                                                            </tbody>
                                                                                        </table>
                                                                                    </td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td align="center" class="esd-block-text" esd-links-underline="none">
                                                                                        <p style="font-size: 13px;"><a target="_blank" style="text-decoration: none;"></a><a target="_blank" style="text-decoration: none;">Privacy Policy</a><a target="_blank" style="font-size: 13px; text-decoration: none;"></a> • <a target="_blank" style="text-decoration: none;">Unsubscribe</a></p>
                                                                                    </td>
                                                                                </tr>
                                                                                <tr>
                                                                                    <td align="center" class="esd-block-text es-p20t" esd-links-underline="none">
                                                                                        <p><a target="_blank"></a>Copyright © 2023&nbsp;Christian Mendoza<a target="_blank"></a></p>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <table cellpadding="0" cellspacing="0" class="es-footer esd-footer-popover" align="center">
                            <tbody>
                                <tr>
                                    <td class="esd-stripe" align="center" esd-custom-block-id="819294">
                                        <table bgcolor="#ffffff" class="es-footer-body" align="center" cellpadding="0" cellspacing="0" width="600">
                                            <tbody>
                                                <tr>
                                                    <td class="esd-structure es-p20" align="left">
                                                        <table cellpadding="0" cellspacing="0" width="100%">
                                                            <tbody>
                                                                <tr>
                                                                    <td width="560" class="esd-container-frame" align="left">
                                                                        <table cellpadding="0" cellspacing="0" width="100%">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td align="center" class="esd-block-image es-infoblock made_with" style="font-size:0"><a target="_blank" href="https://viewstripo.email/?utm_source=templates&utm_medium=email&utm_campaign=cold_emails_2&utm_content=account_registration"><img src="https://tlr.stripocdn.email/content/guids/CABINET_09023af45624943febfa123c229a060b/images/7911561025989373.png" alt width="125" style="display: block;"></a></td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</body>

</html>"""
        msg = MIMEMultipart('alternative')
        parte_html = MIMEText(contenido_html, 'html')
        msg.attach(parte_html)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(fromaddr, "aymcwztzbleymltv")
        text = msg.as_string()
        server.sendmail(fromaddr, to, text)
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
