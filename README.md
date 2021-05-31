UPC Python SDK allows you to implement accepting payments from Visa/MasterCard on your website<br />
Documentation: [Ukrainian](https://docs.ecconnect.com.ua/display/DOCUK), [Russian](https://docs.ecconnect.com.ua/pages/viewpage.action?pageId=65626), [English](https://docs.ecconnect.com.ua/display/DOCEN/Online+payments+for+any+business)<br/>

# Generate sign for PaymentPage-method:
```
import upcpayment
from upcpayment.Upc_payment import Upc_payment

#example with additional fields
payment = Upc_payment('1756190', 'E7884956', 100, '980', 'ua', 123, 'description', alt_total_amount=123, alt_currency=978, sd='qwe', delay=1, ref3='something')
payment.generate_signature('path_to_file')
print('1: ', payment.signature)

#example for standard payment
payment = Upc_payment('1756190', 'E7884956', 100, '980', 'ua', 123, 'description')
payment.generate_signature('path_to_file')
print('2: ', payment.signature)

#example of wrong payment
payment = Upc_payment('1756190', 'E7884956', 100, '980', 'ua', 123, 'description', alt_total_amount=123, sd='qwe', delay=1, ref3='something')
payment.generate_signature('path_to_file')
print('3: ', payment.signature)
```
PurchaseTime generated like this - datetime.datetime.now().strftime("%d%m%Y%H%M%S")<br />
When you make POST-request to gateway - take PurchaseTime from object payment - **payment.purchase_time**<br />
<br />

# XML-method
To generate xml with signature use generate_xml_with_signature method to all objects:
```
xml_with_sign = payment.generate_xml_with_signature('private_key')
```

## MPIEnrol

#### MPIEnrolRequest
```
from upcpayment import Upc_payment_xml

#With card data:
payment = Upc_payment_xml.MPIEnrolRequest('merchant_id', 'terminal_id', 'amount', 'currency', 'order_id', 'description', card_num='card_number', exp_year='exp_year', exp_month='exp_month')
#With UpcToken:
payment = Upc_payment_xml.MPIEnrolRequest('merchant_id', 'terminal_id', 'amount', 'currency', 'order_id', 'description', upctoken='upctoken')
```
Additional arguments: **device_category**

#### MPIAuthRequest
```
payment = Upc_payment_xml.MPIAuthRequest('merchant_id', 'terminal_id', 'order_id', 'status', 'cavv', 'eci', cavv_alg')
```

## AuthorizationRequest
```
payment = Upc_payment_xml.AuthorizationRequest('merchant_id', 'terminal_id', 'order_id', 'date', 'total_amount', 'currency',  'description', 'card_num', 'exp_year', 'exp_month', 'cv_num', 'status', 'cavv', 'eci', 'cavv_alg)
```

## RefundRequest
```
payment = Upc_payment_xml.RefundRequest('merchant_id', 'terminal_id', 'order_id', 'date', 'total_amount', 'currency', 'description', 'approval_code', 'rrn', 'refund_amount')
```

## PreAuthorizationRequest
```
payment = Upc_payment_xml.PreAuthorizationRequest('merchant_id', 'terminal_id', 'order_id', 'date', 'total_amount', 'currency', 'description', 'card_num', 'exp_year', 'exp_month', 'cv_num', 'status', 'cavv', 'eci', 'cavv_alg')
```
Additional arguments: **wallet_id**

## PostAuthorizationRequest
```
payment = Upc_payment_xml.PostAuthorizationRequest('merchant_id', 'terminal_id', 'order_id', 'date', 'total_amount', 'currency', 'description', 'approval_code', 'rrn', 'postauth_amount')
```

## TransactionStateRequest
```
payment = Upc_payment_xml.TransactionStateRequest('merchant_id', 'terminal_id', 'order_id', 'date', 'total_amount', 'currency')
```

## AccountVerificationRequest
```
payment = Upc_payment_xml.AccountVerificationRequest('merchant_id', 'terminal_id', 'order_id', 'date', 'total_amount', 'currency', 'description', 'card_num', 'exp_year', 'exp_month', 'cv_num')
```

## RecurrentRequest
```
payment = Upc_payment_xml.RecurrentRequest('merchant_id', 'terminal_id', 'order_id', 'date', 'total_amount', 'currency', 'description', 'card_num', 'exp_year', 'exp_month', 'cv_num')
```

## SettlementRefundRequest
```
payment = Upc_payment_xml.SettlementRefundRequest('merchant_id', 'terminal_id', 'order_id', 'date', 'total_amount', 'currency', 'description', 'card_num', 'exp_year', 'exp_month', 'ref3')
```
Additional arguments: **approval_code**, **rrn**, **eci**, **posconditioncode**

## MasterPassAuthorizationRequest
```
payment = Upc_payment_xml.MasterPassAuthorizationRequest('merchant_id', 'terminal_id', 'order_id', 'date', 'total_amount', 'currency', 'description', 'card_num', 'exp_year', 'exp_month', 'cv_num', 'status', 'cavv', 'eci', 'cavv_alg', 'wallet_id')
```

## VisaCheckoutAuthorizationRequest
```
payment = Upc_payment_xml.VisaCheckoutAuthorizationRequest('merchant_id', 'terminal_id', 'order_id', 'date', 'total_amount', 'currency', 'description', 'callid')
```

## VisaCheckoutPCIAuthorizationRequest
```
payment = Upc_payment_xml.VisaCheckoutPCIAuthorizationRequest('merchant_id', 'terminal_id', 'order_id', 'date', 'total_amount', 'currency', 'description', 'card_num', 'exp_year', 'exp_month', 'cv_num', 'status', 'cavv', 'eci', 'cavv_alg', 'callid')
```

## AppleGooglePayAuthorizationRequest
```
payment = Upc_payment_xml.AppleGooglePayAuthorizationRequest('merchant_id', 'terminal_id', 'order_id', 'date', 'total_amount', 'currency',  'description', 'card_num', 'exp_year', 'exp_month', 'tavv')
```