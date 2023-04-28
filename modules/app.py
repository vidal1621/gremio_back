#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Import flask and template operators
from datetime import date
import basicauth
from flask import Flask
from psycopg2 import connect
from flask_cors import CORS


class InterceptRequestMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        auth = environ.get('HTTP_AUTHORIZATION', None)
        # req =environ.get('werkzeug.request')
        # try:
        #     print("****URL:", req.method, req.path)
        #     # print(req.query_string,"\tDATA:", req.data)
        # except:
        #     pass

        if auth and auth.startswith('Basic'):
            user, passw = basicauth.decode(auth)
            environ['user'] = user
        return self.wsgi_app(environ, start_response)


app = Flask(__name__)
CORS(app)

app.wsgi_app = InterceptRequestMiddleware(app.wsgi_app)
today = date.today()
t = today.strftime("%Y")  # Configurations
app.config.from_object('config')

db = connect(**app.config.get("DATABASE_CONNECT_OPTIONS"))
db.autocommit = True

# Define the WSGI application object
from modules.mod_auth.controllers import mod_auth
# from modules.mod_sii.controllers import mod_sii
# from modules.mod_empresa.controllers import mod_empresa
# from modules.mod_bancos.controllers import mod_bancos
# from modules.mod_cuenta.controllers import mod_cuenta
# from modules.mod_cliente_proveedor.controllers import mod_cliente_proveedor
# from modules.mod_indicadores.controllers import mod_indicadores
# from modules.mod_compra.controllers import mod_compra
# from modules.mod_venta.controllers import mod_venta
# from modules.mod_reporte.controllers import mod_reporte
# from modules.mod_credito.controllers import mod_credito
# from modules.mod_saldos.controllers import mod_saldos
# from modules.mod_correo.controllers import mod_correo
# from modules.mod_ingreso_gasto.controllers import mod_ingreso_gasto
from modules.mod_pagos.controllers import mod_pagos
from modules.mod_dashboard.controllers import mod_dashboard
from modules.mod_alumnos.controllers import mod_alumnos
from modules.mod_maestro.controllers import mod_maestro

# from modules.mod_comunes.controllers import mod_comunes
# from modules.mod_remuneraciones.controllers import mod_remuneraciones
# from modules.mod_auditoria.controllers import mod_auditoria
# from modules.mod_importador.controllers import mod_importador
# from modules.mod_centro_costo.controllers import mod_centro_costo

# Register blueprint(s)
# app.register_blueprint(mod_sii)
app.register_blueprint(mod_auth)
# app.register_blueprint(mod_empresa)
# app.register_blueprint(mod_bancos)
# app.register_blueprint(mod_cuenta)
# app.register_blueprint(mod_cliente_proveedor)
# app.register_blueprint(mod_indicadores)
# app.register_blueprint(mod_compra)
# app.register_blueprint(mod_venta)
# app.register_blueprint(mod_reporte)
# app.register_blueprint(mod_credito)
# app.register_blueprint(mod_saldos)
# app.register_blueprint(mod_correo)
# app.register_blueprint(mod_ingreso_gasto)
app.register_blueprint(mod_pagos)
app.register_blueprint(mod_dashboard)
app.register_blueprint(mod_alumnos)
app.register_blueprint(mod_maestro)
# app.register_blueprint(mod_comunes)
# app.register_blueprint(mod_remuneraciones)
# app.register_blueprint(mod_auditoria)
# app.register_blueprint(mod_importador)
# app.register_blueprint(mod_centro_costo)


secret_key = app.config.get("SECRET_KEY")
app.secret_key = secret_key

if __name__ == '__main__':
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.run(host='0.0.0.0', port=8889, debug=True)
