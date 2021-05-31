import datetime, random, string
import errno
import os
from OpenSSL import crypto
import base64
from .exceptions import InvalidInput, AltCurrencyAmountNullException

class Upc_payment(object):
    def __init__(self, merchantId, terminalid, total_amount, currency, locale, order_id, purchase_desc, **kwargs):
        self.version = 1
        self.merchantId = merchantId
        self.terminalid = terminalid
        self.total_amount = total_amount
        self.currency = currency
        self.locale = locale
        self.purchase_time = datetime.datetime.now().strftime("%d%m%Y%H%M%S")
        self.order_id = order_id
        self.signature = ''
        self.purchase_desc = purchase_desc
        self.alt_total_amount = kwargs.get('alt_total_amount', '')
        self.alt_currency = kwargs.get('alt_currency', '')
        self.sd = kwargs.get('sd', '')
        self.delay = kwargs.get('delay', '')
        self.ref3 = kwargs.get('ref3', '')

    def generate_signature(self, private_key):
        data = "{};{};{};".format(self.merchantId, self.terminalid, self.purchase_time)
        if self.delay != '':
            data += "{},{};".format(self.order_id, self.delay)
        else:
            data += "{};".format(self.order_id)
        
        if self.alt_currency != '' and self.alt_total_amount != '':
            data += "{},{};{},{};".format(self.currency, self.alt_currency, self.total_amount, self.alt_total_amount)
        elif self.alt_currency == '' and self.alt_total_amount == '':
            data += "{};{};".format(self.currency, self.total_amount)
        else:
            raise AltCurrencyAmountNullException('AltCurrency or AltAmount is not defined')

        data += "{};".format(self.sd)

        if self.ref3 != '':
            data += "{};".format(self.ref3)

        if os.path.exists(private_key): 
            key_id = open(private_key).read();
            if key_id.startswith('-----BEGIN RSA PRIVATE KEY'):
                priv_key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_id)
                signature_bin_str = crypto.sign(priv_key, data, 'sha1')
                base64_bytes = base64.b64encode(signature_bin_str)
                base64_message = base64_bytes.decode('ascii')
                self.signature = base64_message
            else:
                raise InvalidInput('You have to use private key(*.pem)')
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), private_key)
        