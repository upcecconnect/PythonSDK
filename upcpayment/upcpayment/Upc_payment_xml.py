import base64
import datetime
import errno
import os
import random
import string
from dataclasses import dataclass
from io import BytesIO

import signxml
from lxml import etree
from OpenSSL import crypto
from signxml import XMLSigner, XMLVerifier

from .exceptions import InvalidInput


def _ecc_xml_base(order_id, mid, tid):
    eccNSMAP = {'xenc': 'http://www.w3.org/2001/04/xmlenc#',
                'ds': 'http://www.w3.org/2000/09/xmldsig#',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'noNamespaceSchemaLocation': 'https://secure.upc.ua/go/pub/schema/xmlpay-1.21.xsd'}
    ECommerceConnect = etree.Element("ECommerceConnect", nsmap=eccNSMAP)
    Message = etree.SubElement(ECommerceConnect, 'Message')
    Message.set('id', order_id)
    Message.set('version', '1.0')
    XMLPayRequest = etree.SubElement(Message, 'XMLPayRequest')
    RequestData = etree.SubElement(XMLPayRequest, 'RequestData')
    MerchantID = etree.SubElement(RequestData, 'MerchantID')
    MerchantID.text = mid
    TerminalID = etree.SubElement(RequestData, 'TerminalID')
    TerminalID.text = tid
    Transactions = etree.SubElement(RequestData, 'Transactions')
    Transaction = etree.SubElement(Transactions, 'Transaction')
    Transaction.set('id', order_id)
    return ECommerceConnect

def _sign_xml_with_private_key(xml, private_key):
    if os.path.exists(private_key): 
        key = open(private_key).read()
        if key.startswith('-----BEGIN RSA PRIVATE KEY'):
            signed_root = XMLSigner(method=signxml.methods.enveloped,signature_algorithm='rsa-sha1',digest_algorithm="sha1", c14n_algorithm='http://www.w3.org/2001/10/xml-exc-c14n#').sign(xml, key=key)
        else:
            raise InvalidInput('You have to use private key(*.pem)')
    else:
        raise FileNotFoundError()
    return etree.tostring(element_or_tree=signed_root)

def _add_invoice_with_data(parent_element, order_id, date, total_amount, currency, description):
    Invoice = etree.SubElement(parent_element, 'Invoice')
    OrderID = etree.SubElement(Invoice, 'OrderID')
    OrderID.text = order_id
    Date = etree.SubElement(Invoice, 'Date')
    Date.text = date
    TotalAmount = etree.SubElement(Invoice, 'TotalAmount')
    TotalAmount.text = total_amount
    Currency = etree.SubElement(Invoice, 'Currency')
    Currency.text = currency
    if description:
        Description = etree.SubElement(Invoice, 'Description')
        Description.text = description

def _add_card_with_data(parent_element, card_num, exp_year, exp_month, cv_num, tavv):
    Card = etree.SubElement(parent_element, 'Card')
    CardNum = etree.SubElement(Card, 'CardNum')
    CardNum.text = self.card_num
    ExpYear = etree.SubElement(Card, 'ExpYear')
    ExpYear.text = self.exp_year
    ExpMonth = etree.SubElement(Card, 'ExpMonth')
    ExpMonth.text = self.exp_month
    if cv_num:
        CVNum = etree.SubElement(Card, 'CVNum')
        CVNum.text = self.cv_num
    if tavv:
        ExtDataToken = etree.SubElement(Card, 'ExtDataToken')
        TAVV = etree.SubElement(ExtDataToken, 'TAVV')
        TAVV.text = tavv

def _add_pares_with_data(parent_element, status, cavv, eci, cavv_alg):
    PARes = etree.SubElement(parent_element, 'PARes')
    Status = etree.SubElement(PARes, 'Status')
    Status.text = status
    CAVV = etree.SubElement(PARes, 'CAVV')
    CAVV.text = cavv
    ECI = etree.SubElement(PARes, 'ECI')
    ECI.text = eci
    CavvAlgorithm = etree.SubElement(PARes, 'CavvAlgorithm')
    CavvAlgorithm.text = cavv_alg

def _convert_response_to_xml(response):
    if type(response) is str:
        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        return etree.fromstring(response.encode('utf-8'), parser=parser)
    else:
        raise TypeError('Waited for response as string with xml declaration')

@dataclass(frozen=True, order=True)
class MPIEnrolRequest:
    merchant_id: str
    terminal_id: str
    total_amount: str
    currency: str
    order_id: str
    purchase_desc: str
    card_num: str = ''
    exp_year: str = ''
    exp_month: str = ''
    device_category: str = "0"
    upctoken: str = ''

    def generate_xml_with_signature(self, private_key) -> str:
        eccNSMAP = {'xenc': 'http://www.w3.org/2001/04/xmlenc#',
                'ds': 'http://www.w3.org/2000/09/xmldsig#',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'noNamespaceSchemaLocation': 'https://secure.upc.ua/go/pub/schema/xmlpay-1.21.xsd'}
        ECommerceConnect = etree.Element("ECommerceConnect", nsmap=eccNSMAP)
        Message = etree.SubElement(ECommerceConnect, 'Message')
        Message.set('id', self.order_id)
        Message.set('version', '1.0')
        XMLMPIRequest = etree.SubElement(Message, 'XMLMPIRequest')
        MerchantID = etree.SubElement(XMLMPIRequest, 'MerchantID')
        MerchantID.text = self.merchant_id
        TerminalID = etree.SubElement(XMLMPIRequest, 'TerminalID')
        TerminalID.text = self.terminal_id
        MPIRequest = etree.SubElement(XMLMPIRequest, 'MPIRequest')
        MPIRequest.set('id', self.order_id)
        MPIEnrolRequest_node = etree.SubElement(MPIRequest, 'MPIEnrolRequest')
        if not self.upctoken:
            CardNum = etree.SubElement(MPIEnrolRequest_node, 'CardNum')
            CardNum.text = self.card_num
            ExpYear = etree.SubElement(MPIEnrolRequest_node, 'ExpYear')
            ExpYear.text = self.exp_year
            ExpMonth = etree.SubElement(MPIEnrolRequest_node, 'ExpMonth')
            ExpMonth.text = self.exp_month
        else:
            Token = etree.SubElement(MPIEnrolRequest_node, 'Token')
            UpcToken = etree.SubElement(Token, 'UpcToken')
            TokenID = etree.SubElement(UpcToken, 'TokenID')
            TokenID.text = self.upctoken
        TotalAmount = etree.SubElement(MPIEnrolRequest_node, 'TotalAmount')
        TotalAmount.text = self.total_amount
        Currency = etree.SubElement(MPIEnrolRequest_node, 'Currency')
        Currency.text = self.currency
        Description = etree.SubElement(MPIEnrolRequest_node, 'Description')
        Description.text = self.purchase_desc
        DeviceCategory = etree.SubElement(MPIEnrolRequest_node, 'DeviceCategory')
        DeviceCategory.text = self.device_category

        return _sign_xml_with_private_key(ECommerceConnect, private_key)
        
@dataclass(frozen=True, order=True)
class MPIEnrolResponse:
    code: str
    enrolled: str
    acsurl: str
    pareq: str
    xid: str

@dataclass(frozen=True, order=True)
class MPIAuthRequest:
    merchant_id: str
    terminal_id: str
    order_id: str
    status: str
    cavv: str
    eci: str
    cavv_alg: str
    
    def generate_xml_with_signature(self, private_key) -> str:
        eccNSMAP = {'xenc': 'http://www.w3.org/2001/04/xmlenc#',
                'ds': 'http://www.w3.org/2000/09/xmldsig#',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'noNamespaceSchemaLocation': 'https://secure.upc.ua/go/pub/schema/xmlpay-1.21.xsd'}
        ECommerceConnect = etree.Element("ECommerceConnect", nsmap=eccNSMAP)
        Message = etree.SubElement(ECommerceConnect, 'Message')
        Message.set('id', self.order_id)
        Message.set('version', '1.0')
        XMLMPIRequest = etree.SubElement(Message, 'XMLMPIRequest')
        MerchantID = etree.SubElement(XMLMPIRequest, 'MerchantID')
        MerchantID.text = self.merchant_id
        TerminalID = etree.SubElement(XMLMPIRequest, 'TerminalID')
        TerminalID.text = self.terminal_id
        MPIRequest = etree.SubElement(XMLMPIRequest, 'MPIRequest')
        MPIRequest.set('id', self.order_id)
        MPIAuthRequest = etree.SubElement(MPIRequest, 'MPIAuthRequest')

        _add_pares_with_data(MPIAuthRequest, self.status, self.cavv, self.eci, self.cavv_alg)

        return _sign_xml_with_private_key(ECommerceConnect, private_key)

@dataclass(frozen=True, order=True)
class MPIAuthResponse:
    code: str
    status: str
    cavv: str
    eci: str
    cavv_alg: str

@dataclass(frozen=True, order=True)
class AuthorizationRequest:
    """
    authrequest
    """
    merchant_id: str
    terminal_id: str
    order_id: str
    date: str
    total_amount: str
    currency: str
    purchase_desc: str
    card_num: str
    exp_year: str
    exp_month: str
    cv_num: str
    status: str
    cavv: str
    eci: str
    cavv_alg: str

    def generate_xml_with_signature(self, private_key) -> str:
        ECommerceConnect = _ecc_xml_base(self.order_id, self.merchant_id, self.terminal_id)
        Transaction = ECommerceConnect.find('.//Transaction')
        Authorization = etree.SubElement(Transaction, 'Authorization')
        PayData = etree.SubElement(Authorization, 'PayData')

        _add_invoice_with_data(PayData, self.order_id, self.date, self.total_amount, self.currency, self.purchase_desc)

        _add_card_with_data(PayData, self.card_num, self.exp_year, self.exp_month, self.cv_num, '')

        _add_pares_with_data(PayData, self.status, self.cavv, self.eci, self.cavv_alg)

        return _sign_xml_with_private_key(ECommerceConnect, private_key)    

@dataclass(frozen=True, order=True)
class AuthorizationResponse:
    merchant_id: str
    terminal_id: str
    order_id: str
    tran_code: str
    approval_code: str
    rrn: str
    comment: str = ''
    host_code: str = ''

@dataclass(frozen=True, order=True)
class RefundRequest:
    merchant_id: str
    terminal_id: str
    order_id: str
    date: str
    total_amount: str
    currency: str
    purchase_desc: str
    approval_code: str
    rrn: str
    refund_amount: str

    def generate_xml_with_signature(self, private_key) -> str:
        ECommerceConnect = _ecc_xml_base(self.order_id, self.merchant_id, self.terminal_id)
        Transaction = ECommerceConnect.find('.//Transaction')
        Refund = etree.SubElement(Transaction, 'Refund')
        RefundData = etree.SubElement(Refund, 'RefundData')

        _add_invoice_with_data(RefundData, self.order_id, self.date, self.total_amount, self.currency, self.purchase_desc)

        AuthorizationRef = etree.SubElement(RefundData, 'AuthorizationRef')
        ApprovalCode = etree.SubElement(AuthorizationRef, 'ApprovalCode')
        ApprovalCode.text = self.approval_code
        Rrn = etree.SubElement(AuthorizationRef, 'Rrn')
        Rrn.text = self.rrn

        RefundAmount = etree.SubElement(RefundData, 'RefundAmount')
        RefundAmount.text = self.refund_amount

        return _sign_xml_with_private_key(ECommerceConnect, private_key)

@dataclass(frozen=True, order=True)
class RefundResponse:
    order_id: str
    merchant_id: str
    terminal_id: str
    tran_code: str
    comment: str = ""

@dataclass(frozen=True, order=True)
class PreAuthorizationRequest:
    merchant_id: str
    terminal_id: str
    order_id: str
    date: str
    total_amount: str
    currency: str
    purchase_desc: str
    card_num: str
    exp_year: str
    exp_month: str
    cv_num: str
    status: str
    cavv: str
    eci: str
    cavv_alg: str
    wallet_id: str = ''

    def generate_xml_with_signature(self, private_key) -> str:
        ECommerceConnect = _ecc_xml_base(self.order_id, self.merchant_id, self.terminal_id)
        Transaction = ECommerceConnect.find('.//Transaction')
        Preauthorization = etree.SubElement(Transaction, 'Preauthorization')
        PayData = etree.SubElement(Preauthorization, 'PayData')

        _add_invoice_with_data(PayData, self.order_id, self.date, self.total_amount, self.currency, self.purchase_desc)

        _add_card_with_data(PayData, self.card_num, self.exp_year, self.exp_month, self.cv_num, '')

        _add_pares_with_data(PayData, self.status, self.cavv, self.eci, self.cavv_alg)

        if self.wallet_id:
            WalletID = etree.SubElement(PayData, 'Walletid')
            WalletID.text = self.wallet_id

        return _sign_xml_with_private_key(ECommerceConnect, private_key)   

@dataclass(frozen=True, order=True)
class PreAuthorizationResponse:
    order_id: str
    merchant_id: str
    terminal_id: str
    tran_code: str
    approval_code: str
    rrn: str
    comment: str = ''
    host_code: str = ''

@dataclass(frozen=True, order=True)
class PostAuthorizationRequest:
    merchant_id: str
    terminal_id: str
    order_id: str
    date: str
    total_amount: str
    currency: str
    purchase_desc: str
    approval_code: str
    rrn: str
    postauth_amount: str

    def generate_xml_with_signature(self, private_key) -> str:
        ECommerceConnect = _ecc_xml_base(self.order_id, self.merchant_id, self.terminal_id)
        Transaction = ECommerceConnect.find('.//Transaction')
        PostAuthorization = etree.SubElement(Transaction, 'Postauthorization')
        PostAuthorizationData = etrr.SubElement(PostAuthorization, 'PostauthorizationData')

        _add_invoice_with_data(PostAuthorizationData, self.order_id, self.date, self.total_amount, self.currency, self.purchase_desc)

        PreAuthorizationRef = etree.SubElement(PostAuthorizationData, 'PreauthorizationRef')
        ApprovalCode = etree.SubElement(PreAuthorizationRef, 'ApprovalCode')
        ApprovalCode.text = self.approval_code
        Rrn = etree.SubElement(PreAuthorizationRef, 'Rrn')
        Rrn.text = self.rrn

        PostAuthorizationAmount = etree.SubElement(PostAuthorizationData, 'PostauthorizationAmount')
        PostAuthorizationAmount.text = self.postauth_amount

        return _sign_xml_with_private_key(ECommerceConnect, private_key) 

@dataclass(frozen=True, order=True)
class PostAuthorizationResponse:
    order_id: str
    merchant_id: str
    terminal_id: str
    tran_code: str
    comment: str = ''

@dataclass(frozen=True, order=True)
class TransactionStateRequest:
    merchant_id: str
    terminal_id: str
    order_id: str
    date: str
    total_amount: str
    currency: str

    def generate_xml_with_signature(self, private_key) -> str:
        ECommerceConnect = _ecc_xml_base(self.order_id, self.merchant_id, self.terminal_id)
        Transaction = ECommerceConnect.find('.//Transaction')
        TransactionStateReq = etree.SubElement(Transaction, 'TransactionStateReq')
        TransactionStateReqData = etree.SubElement(TransactionStateReq, 'TransactionStateReqData')

        _add_invoice_with_data(TransactionStateReqData, self.order_id, self.date, self.total_amount, self.currency, '')

        return _sign_xml_with_private_key(ECommerceConnect, private_key) 

@dataclass(frozen=True, order=True)
class TransactionStateResponse:
    order_id: str
    merchant_id: str
    terminal_id: str
    tran_code: str
    approval_code: str = ''
    rrn: str = ''
    comment: str = ''

@dataclass(frozen=True, order=True)
class AccountVerificationRequest:
    merchant_id: str
    terminal_id: str
    order_id: str
    date: str
    total_amount: str
    currency: str
    purchase_desc: str
    card_num: str
    exp_year: str
    exp_month: str
    cv_num: str

    def generate_xml_with_signature(self, private_key) -> str:
        ECommerceConnect = _ecc_xml_base(self.order_id, self.merchant_id, self.terminal_id)
        Transaction = ECommerceConnect.find('.//Transaction')
        Authorization = etree.SubElement(Transaction, 'Authorization')
        PayData = etree.SubElement(Authorization, 'PayData')

        _add_invoice_with_data(PayData, self.order_id, self.date, self.total_amount, self.currency, self.purchase_desc)

        _add_card_with_data(PayData, self.card_num, self.exp_year, self.exp_month, self.cv_num, '')

        return _sign_xml_with_private_key(ECommerceConnect, private_key)

@dataclass(frozen=True, order=True)
class TransactionStateResponse:
    order_id: str
    merchant_id: str
    terminal_id: str
    tran_code: str
    cvresult: str
    host_code: str
    approval_code: str = ''
    rrn: str = ''
    comment: str = ''

@dataclass(frozen=True, order=True)
class RecurrentRequest:
    merchant_id: str
    terminal_id: str
    order_id: str
    date: str
    total_amount: str
    currency: str
    purchase_desc: str
    card_num: str
    exp_year: str
    exp_month: str
    cv_num: str

    def generate_xml_with_signature(self, private_key) -> str:
        ECommerceConnect = _ecc_xml_base(self.order_id, self.merchant_id, self.terminal_id)
        Transaction = ECommerceConnect.find('.//Transaction')
        Authorization = etree.SubElement(Transaction, 'Authorization')
        PayData = etree.SubElement(Authorization, 'PayData')

        _add_invoice_with_data(PayData, self.order_id, self.date, self.total_amount, self.currency, self.purchase_desc)

        _add_card_with_data(PayData, self.card_num, self.exp_year, self.exp_month, self.cv_num, '')

        Recurrent = etree.SubElement(PayData, 'Recurrent')
        Recurrent.text = 'true'

        return _sign_xml_with_private_key(ECommerceConnect, private_key)

@dataclass(frozen=True, order=True)
class RecurrentResponse:
    order_id: str
    merchant_id: str
    terminal_id: str
    tran_code: str
    approval_code: str
    rrn: str
    comment: str
    cvresult: str
    host_code: str

@dataclass(frozen=True, order=True)
class SettlementRefundRequest:
    merchant_id: str
    terminal_id: str
    order_id: str
    date: str
    total_amount: str
    currency: str
    purchase_desc: str
    card_num: str
    exp_year: str
    exp_month: str
    ref3: str
    approval_code: str = ''
    rrn: str = ''
    eci: str = ''
    posconditioncode: str = ''

    def generate_xml_with_signature(self, private_key) -> str:
        ECommerceConnect = _ecc_xml_base(self.order_id, self.merchant_id, self.terminal_id)
        Transaction = ECommerceConnect.find('.//Transaction')
        Settlement = etree.SubElement(Transaction, 'Settlement')
        SettlementRefundData = etree.SubElement(Settlement, 'SettlementRefundData')
        
        _add_invoice_with_data(SettlementRefundData, self.order_id, self.date, self.total_amount, self.currency, self.purchase_desc)

        _add_card_with_data(SettlementRefundData, self.card_num, self.exp_year, self.exp_month, '', '')

        if self.approval_code:
            ApprovalCode = etree.SubElement(SettlementRefundData, 'ApprovalCode')
            ApprovalCode.text = self.approval_code
        if self.rrn:
            Rrn = etree.SubElement(SettlementRefundData, 'Rrn')
            Rrn.text = self.rrn
        if self.eci:
            ECI = etree.SubElement(SettlementRefundData, 'ECI')
            ECI.text = self.eci
        if self.posconditioncode:
            PosConditionCode = etree.SubElement(SettlementRefundData, 'PosConditionCode')
            PosConditionCode.text = self.posconditioncode

        Ref3 = etree.SubElement(SettlementRefundData, 'Ref3')
        Ref3.text = self.ref3
    
        return _sign_xml_with_private_key(ECommerceConnect, private_key)

@dataclass(frozen=True, order=True)
class SettlementRefundResponse:
    merchant_id: str
    terminal_id: str
    tran_code: str
    comment: str

@dataclass(frozen=True, order=True)
class MasterPassAuthorizationRequest:
    merchant_id: str
    terminal_id: str
    order_id: str
    date: str
    total_amount: str
    currency: str
    purchase_desc: str
    card_num: str
    exp_year: str
    exp_month: str
    cv_num: str
    status: str
    cavv: str
    eci: str
    cavv_alg: str
    wallet_id: str

    def generate_xml_with_signature(self, private_key) -> str:
        ECommerceConnect = _ecc_xml_base(self.order_id, self.merchant_id, self.terminal_id)
        Transaction = ECommerceConnect.find('.//Transaction')
        Authorization = etree.SubElement(Transaction, 'Authorization')
        PayData = etree.SubElement(Authorization, 'PayData')

        _add_invoice_with_data(PayData, self.order_id, self.date, self.total_amount, self.currency, self.purchase_desc)

        _add_card_with_data(PayData, self.card_num, self.exp_year, self.exp_month, self.cv_num, '')

        _add_pares_with_data(PayData, self.status, self.cavv, self.eci, self.cavv_alg)

        WalletID = etree.SubElement(PayData, 'Walletid')
        WalletID.text = self.wallet_id

        return _sign_xml_with_private_key(ECommerceConnect, private_key) 

@dataclass(frozen=True, order=True)
class MasterPassAuthorizationResponse:
    order_id: str
    merchant_id: str
    terminal_id: str
    tran_code: str
    approval_code: str
    rrn: str
    comment: str = ''
    host_code: str = ''

@dataclass(frozen=True, order=True)
class VisaCheckoutAuthorizationRequest:
    merchant_id: str
    terminal_id: str
    order_id: str
    date: str
    total_amount: str
    currency: str
    purchase_desc: str
    callid: str

    def generate_xml_with_signature(self, private_key) -> str:
        ECommerceConnect = _ecc_xml_base(self.order_id, self.merchant_id, self.terminal_id)
        Transaction = ECommerceConnect.find('.//Transaction')
        Authorization = etree.SubElement(Transaction, 'Authorization')
        PayData = etree.SubElement(Authorization, 'PayData')

        _add_invoice_with_data(PayData, self.order_id, self.date, self.total_amount, self.currency, self.purchase_desc)

        Card = etree.SubElement(PayData, 'Card')
        Wallet = etree.SubElement(Card, 'Wallet')
        VISACheckout = etree.SubElement(Wallet, 'VISACheckout')
        CallID = etree.SubElement(VISACheckout, 'CallID')
        CallID.text = self.callid

        return _sign_xml_with_private_key(ECommerceConnect, private_key) 

@dataclass(frozen=True, order=True)
class VisaCheckoutAuthorizationResponse:
    order_id: str
    merchant_id: str
    terminal_id: str
    tran_code: str
    approval_code: str
    rrn: str
    comment: str = ''
    host_code: str = ''

@dataclass(frozen=True, order=True)
class VisaCheckoutPCIAuthorizationRequest:
    merchant_id: str
    terminal_id: str
    order_id: str
    date: str
    total_amount: str
    currency: str
    purchase_desc: str
    card_num: str
    exp_year: str
    exp_month: str
    cv_num: str
    status: str
    cavv: str
    eci: str
    cavv_alg: str
    callid: str

    def generate_xml_with_signature(self, private_key) -> str:
        ECommerceConnect = _ecc_xml_base(self.order_id, self.merchant_id, self.terminal_id)
        Transaction = ECommerceConnect.find('.//Transaction')
        Authorization = etree.SubElement(Transaction, 'Authorization')
        PayData = etree.SubElement(Authorization, 'PayData')

        _add_invoice_with_data(PayData, self.order_id, self.date, self.total_amount, self.currency, self.purchase_desc)

        _add_card_with_data(PayData, self.card_num, self.exp_year, self.exp_month, self.cv_num, '')

        _add_pares_with_data(PayData, self.status, self.cavv, self.eci, self.cavv_alg)

        Wallet = etree.SubElement(PayData, 'Wallet')
        VISACheckout = etree.SubElement(Wallet, 'VISACheckout')
        CallID = etree.SubElement(VISACheckout, 'CallID')
        CallID.text = self.callid

        return _sign_xml_with_private_key(ECommerceConnect, private_key) 

@dataclass(frozen=True, order=True)
class VisaCheckoutPCIAuthorizationResponse:
    merchant_id: str
    terminal_id: str
    tran_code: str
    approval_code: str
    rrn: str
    comment: str
    host_code: str

@dataclass(frozen=True, order=True)
class AppleGooglePayAuthorizationRequest:
    merchant_id: str
    terminal_id: str
    order_id: str
    date: str
    total_amount: str
    currency: str
    purchase_desc: str
    card_num: str
    exp_year: str
    exp_month: str
    tavv: str

    def generate_xml_with_signature(self, private_key) -> str:
        ECommerceConnect = _ecc_xml_base(self.order_id, self.merchant_id, self.terminal_id)
        Transaction = ECommerceConnect.find('.//Transaction')
        Authorization = etree.SubElement(Transaction, 'Authorization')
        PayData = etree.SubElement(Authorization, 'PayData')

        _add_invoice_with_data(PayData, self.order_id, self.date, self.total_amount, self.currency, self.purchase_desc)

        _add_card_with_data(PayData, self.card_num, self.exp_year, self.exp_month, self.cv_num, self.tavv)

        return _sign_xml_with_private_key(ECommerceConnect, private_key)  

@dataclass(frozen=True, order=True)
class AppleGooglePayAuthResponse:
    order_id: str
    merchant_id: str
    terminal_id: str
    tran_code: str
    approval_code: str
    rrn: str
    comment: str
    host_code: str
    cvresult: str

def MPIEnrolResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return 'to do'

def MPIAuthResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return 'to do'

def AuthorizationResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return ''

def RefundResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return ''

def PreAuthorizationResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return ''

def PostAuthorizationResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return ''

def TransactionStateResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return ''

def AccountVerificationResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return ''

def RecurrentResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return ''

def SettlementRefundResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return ''

def MasterPassAuthorizationResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return ''

def VisaCheckoutAuthorizationResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return ''

def VisaCheckoutPCIAuthorizationResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return 'to do'

def AppleGooglePayAuthorizationResponse_check_sign_and_parse(response):
    #TODO
    res_xml = _convert_response_to_xml(response)
    return ''