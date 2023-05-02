#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Blueprint, session, Response, request, jsonify
import json

from pydantic import BaseModel

from ..app import db
import datetime
import basicauth
from dateutil.relativedelta import relativedelta
import psycopg2.extras
import config
import hashlib
import hmac
import urllib.parse
from typing import Dict, Optional
import requests
import os


mod_pagos = Blueprint('pagos', __name__, url_prefix='/pagos')

# @mod_pagos.route('/create_order', methods=['POST'])
# def create_order():
#     amount: int = 1000
#     apiKey: str = self.API_KEY
#     commerceOrder: str = "12345"
#     currency: str = "CLP"
#     email: str = "Escuelagremiochile@gmail.com"
#     merchantId: str = None
#     optional: str = None
#     # payment_currency: str = "CLP"
#     payment_method: int = 9
#     subject: str = ""
#     timeout: int = None
#     urlConfirmation: str = "https://www.google.com"
#     urlReturn: str = "https://www.google.com"
#     s: str = ""
#     payment = Payment()
#     payment_data = PaymentCreate(
#         amount=amount,
#         apiKey=apiKey,
#         commerceOrder=commerceOrder,
#         currency=currency,
#         email=email,
#         merchantId=merchantId,
#         optional=optional,
#         # payment_currency=payment_currency,
#         payment_method=payment_method,
#         subject=subject,
#         timeout=timeout,
#         urlConfirmation=urlConfirmation,
#         urlReturn=urlReturn,
#         s=s
#     )
#     signature = payment.create_order(payment_data)
#     return Response(response=json.dumps(signature), status=200, mimetype='application/json')


class PaymentCreate(BaseModel):
    amount: int
    apiKey: Optional[str] = None
    commerceOrder: str
    currency: str
    email: str
    merchantId: Optional[str] = None
    optional: Optional[str] = None
    # payment_currency: str
    payment_method: Optional[int] = None
    subject: str
    timeout: Optional[int] = None
    urlConfirmation: str
    urlReturn: str
    s: Optional[str] = None


class RefundCreate:
    amount: int
    apiKey: str
    commerceOrder: str
    currency: str
    email: str
    merchantId: str
    optional: str
    # payment_currency: str
    payment_method: int
    subject: str
    timeout: int
    urlConfirmation: str
    urlReturn: str
    s: str



class Payment:
    def __init__(self):
        self.API_URL = 'https://sandbox.flow.cl/api'
        self.API_KEY = '7F77DD8F-DDDA-4496-BB12-6D9F9BL8729C'
        self.API_SECRET = '726ae63459d59cf567d026f78c40c2d716c67283'

    def create_signature(self, params: Dict):
        sorted_data = ''.join([f'{k}{v}' for k, v in sorted(params.items()) if k != 's'])
        hash_string = hmac.new(self.API_SECRET.encode(), sorted_data.encode(), hashlib.sha256).hexdigest()
        return hash_string

    def create_order(self, payment_data: PaymentCreate):
        payment_data.apiKey = self.API_KEY
        params = payment_data.dict(exclude_none=True)
        signature = self.create_signature(params=params)

        # Agregar la firma al diccionario de parámetros
        payment_data.s = signature

        payload = payment_data.dict(exclude_none=True)
        headers = {"content-type": "application/x-www-form-urlencoded"}
        resp = requests.request(
            "POST",
            self.API_URL + "/payment/create",
            data=urllib.parse.urlencode(payload),
            headers=headers
        )
        return resp

    def create_refund(self, refund_data: RefundCreate):
        refund_data.apiKey = self.API_KEY
        params = refund_data.dict(exclude_none=True)
        signature = self.create_signature(params=params)
        refund_data.s = signature
        payload = refund_data.dict(exclude_none=True)
        headers = {"content-type": "application/x-www-form-urlencoded"}
        resp = requests.request(
            "POST",
            self.API_URL + "/refund/create",
            data=urllib.parse.urlencode(payload),
            headers=headers
        )
        return resp

    def cancel_refund(self, token):
        params = {
            "apiKey": self.API_KEY,
            "token": token
        }
        signature = self.create_signature(params=params)
        params["s"] = signature
        headers = {"content-type": "application/x-www-form-urlencoded"}
        resp = requests.request(
            "POST",
            self.API_URL + "/refund/cancel",
            data=urllib.parse.urlencode(params),
            headers=headers
        )
        return resp

    def get_refund_status(self, token):
        params = {
            "apiKey": self.API_KEY,
            "token": token
        }
        signature = self.create_signature(params=params)
        params["s"] = signature
        headers = {"content-type": "application/x-www-form-urlencoded"}
        resp = requests.request(
            "GET",
            self.API_URL + "/refund/getStatus"+ f"?{urllib.parse.urlencode(params)}",
            # data=urllib.parse.urlencode(params),
            headers=headers
        )
        return resp


# if __name__ == "_main_":
#     payment = Payment()
#     url_confirmation = "http://api/v1/flow_refund_confirm/crear"
#     payment_d = {
#         "refundCommerceOrder": "123456",
#         "flowTrxId": "1575525",
#         # "commerceTrxId": "1572955",
#         "amount": 500,
#         "receiverEmail": "osmanicasanueva@gmail.com",
#         "urlCallBack": url_confirmation
#     }
#     # ri = payment.create_refund(refund_data=RefundCreate(**payment_d))
#     tokens = [
#         "3F85DBD6022EA268AB311647541B3D3695C267FA",
#         "E0520F66673FD909BBABC069267753F1825C3ECE",
#         "9C919FC8992EBE44C4AAFA4098C8CA675CCC3DAE",
#         "8E297BF628758ADBFE199C371F14EBB7AC9E263P",
#         "246FBAEDA8501210AB4EFC1501C921226580A5FT",
#     ]
#     for token in tokens:
#
#         re = payment.get_refund_status(token=token)
#         print(re.json())


