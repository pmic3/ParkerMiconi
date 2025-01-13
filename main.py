from spyne import Application, rpc, ServiceBase, Unicode, Integer, Array
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from flask import Flask, request
from io import StringIO
import logging
import xml.etree.ElementTree as ET
import pandas as pd

logging.basicConfig(level=logging.INFO)


def getPriceFC(total: float, tip: float):
    # Constants
    FC_TAX_RATE = 0.0725
    possible_batteries = [122.99, 153.74, 184.49, 204.99, 254.99] # Expand as necessary
    possible_service_fees = [0, 18, 25, 50, 75]  # Expand as necessary

    for battery_price in possible_batteries:
        # Calculate the battery price with tax
        battery_with_tax = battery_price * (1 + FC_TAX_RATE)
        # Compute the service fee required to match the total
        computed_service_fee = total - tip - battery_with_tax

        # Check if computed_service_fee matches one of the allowed values
        if any(abs(computed_service_fee - fee) < 0.005 for fee in possible_service_fees):
            # If valid, return the breakdown
            return {
                "battery_price": round(battery_price, 2),
                "service_fee": round(computed_service_fee, 2),
                "tip": round(tip, 2)
            }

    # If no match is found
    return None

# Hardcoded DataFrame for demonstration
df = pd.DataFrame({
    'Name': ['Christian Ross', 'Craig Cassell', 'Daniel Cruz'],
    'Amount': [209.13, 209.13, 209.13],
    'Tip': [0, 0, 0],
    'Date': ['2024-01-07', '2024-02-18', '2024-03-12'],
    'Battery': ['35-C Battery', '121R-C Battery', '26-C Battery'],
    'Class': ['Franklin County', 'Franklin County', 'Franklin County']
})

# Global variables to track processing state
current_step = 0
current_row_index = 0

# These will be assigned per row from the DataFrame
customer_name = None
payment_amount = None
payment_date = None
payment_txn_id = None
payment_edit_sequence = None
invoice_txn_id = None
invoice_date = None
invoice_item_name = None
invoice_item_amount = None
invoice_class = 'Franklin County'

class QBWebConnectorService(ServiceBase):
    @rpc(Unicode, Unicode, _returns=Array(Unicode))
    def authenticate(ctx, strUserName, strPassword):
        print("999: Authenticate method called")
        if strUserName == 'Admin' and strPassword == 'Barcelona33#':
            return ['some_session_ticket', '']
        else:
            return ['nvu', '']

    @rpc(Unicode, Unicode, Unicode, Unicode, Integer, Integer, _returns=Unicode)
    def sendRequestXML(ctx, ticket, strHCPResponse, strCompanyFileName, qbXMLCountry, qbXMLMajorVers, qbXMLMinorVers):
        global current_step, current_row_index
        global customer_name, invoice_item_name, invoice_item_amount, payment_amount, payment_date
        global invoice_date, invoice_class
        
        # If we've processed all rows, return empty string to indicate no more requests.
        if current_row_index >= len(df):
            print("999: All rows processed. No more requests.")
            return ""

        # For the current row, set up the variables
        row = df.iloc[current_row_index]
        customer_name = row['Name']
        invoice_item_name = row['Battery']
        payment_date = row['Date']
        invoice_date = row['Date']
        payment_amount = row['Amount']
        
        tip_amount = row['Tip']  # Referred to as Install Labor in QBD

        # getPriceFC Method call for service charge and battery price pre tax
        result = getPriceFC(payment_amount, tip_amount)

        extra_service_charge = result['service_fee']
        invoice_item_amount = result['battery_price']



        print("999: Called sendRequestXML")
        
        if current_step == 0:
            # Step 0: Query for the receive payment
            print(f"999: sendRequestXML (current_row={current_row_index}) Step 0 - Query for receive payment for {customer_name}")
            
            # QBXML body to query for the current customer's payment  
            qbxml = f"""
            <?xml version="1.0" encoding="utf-8"?>
            <?qbxml version="13.0"?>
            <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <ReceivePaymentQueryRq requestID="1">
                <EntityFilter>
                    <FullName>{customer_name}</FullName>
                </EntityFilter>
                <IncludeRetElement>TxnID</IncludeRetElement>
                <IncludeRetElement>TotalAmount</IncludeRetElement>
                <IncludeRetElement>EditSequence</IncludeRetElement>
                </ReceivePaymentQueryRq>
            </QBXMLMsgsRq>
            </QBXML>
            """
            return qbxml.strip()

        elif current_step == 1:
            # Step 1: Create the invoice
            print(f"999: sendRequestXML (current_row={current_row_index}) Step 1 - Create the invoice for {customer_name}")
            # We will always add the battery line. If tip or extra_service_charge > 0, we add Install Labor line(s).
            
            # Battery line item being added to invoice_line_adds list to be added to full invoice qbxml
            invoice_line_adds = f"""
            <InvoiceLineAdd>
                <ItemRef>
                    <FullName>{invoice_item_name}</FullName>
                </ItemRef>
                <Amount>{invoice_item_amount}</Amount>
            </InvoiceLineAdd>
            """
            
            # Only adds new line item for tip if there is one (greater than 0)
            if tip_amount > 0:
                invoice_line_adds += f"""
                <InvoiceLineAdd>
                  <ItemRef>
                    <FullName>Install Labor</FullName>
                  </ItemRef>
                  <Amount>{tip_amount}</Amount>
                </InvoiceLineAdd>
                """

            # Only adds line item for extra install labor if there is one (greater than 0)
            if extra_service_charge > 0:
                invoice_line_adds += f"""
                <InvoiceLineAdd>
                  <ItemRef>
                    <FullName>Install Labor</FullName>
                  </ItemRef>
                  <Amount>{extra_service_charge}</Amount>
                </InvoiceLineAdd>
                """

            # Main QBXML body
            qbxml = f"""
            <?xml version="1.0" encoding="utf-8"?>
            <?qbxml version="13.0"?>
            <QBXML>
              <QBXMLMsgsRq onError="stopOnError">
                <InvoiceAddRq requestID="2">
                  <InvoiceAdd>
                    <CustomerRef>
                      <FullName>{customer_name}</FullName>
                    </CustomerRef>
                    <ClassRef>
                      <FullName>{invoice_class}</FullName>
                    </ClassRef>
                    <TxnDate>{invoice_date}</TxnDate>
                    {invoice_line_adds}
                  </InvoiceAdd>
                </InvoiceAddRq>
              </QBXMLMsgsRq>
            </QBXML>
            """
            return qbxml.strip()

        elif current_step == 2:
            # Step 2: Apply the payment to the invoice
            print(f"999: sendRequestXML (current_row={current_row_index}) Step 2 - Apply the payment to the invoice")
            
            # QBXML body that applies the payment found in step 0 to the invoice in step 1
            qbxml = f"""
            <?xml version="1.0" encoding="utf-8"?>
            <?qbxml version="13.0"?>
            <QBXML>
              <QBXMLMsgsRq onError="stopOnError">
                <ReceivePaymentModRq requestID="3">
                  <ReceivePaymentMod>
                      <TxnID>{payment_txn_id}</TxnID>
                      <EditSequence>{payment_edit_sequence}</EditSequence>
                      <AppliedToTxnMod>
                        <TxnID>{invoice_txn_id}</TxnID>
                        <PaymentAmount>{payment_amount}</PaymentAmount>
                      </AppliedToTxnMod>
                  </ReceivePaymentMod>
                </ReceivePaymentModRq>
              </QBXMLMsgsRq>
            </QBXML>
            """
            return qbxml.strip()

        else:
            # After step 3 is done, we will increment the row. But the Web Connector might call this again.
            # If we've reached here, no more requests.
            return ""

    @rpc(Unicode, Unicode, Unicode, Unicode, _returns=Integer)
    def receiveResponseXML(ctx, ticket, response, hresult, message):
        global current_step, payment_txn_id, payment_edit_sequence, invoice_txn_id, payment_amount
        global current_row_index
        root = ET.fromstring(response)

        if current_step == 0:
            # We're expecting ReceivePaymentQueryRs
            receive_payment_rets = root.findall(".//ReceivePaymentRet")

            found_payment = False
            for ret in receive_payment_rets:
                print(f"999: Full ret element == {ET.tostring(ret, encoding='unicode')}")
                
                txn_id = ret.find("TxnID")
                print(f"999: Txn ID == {txn_id.text} ")
                payment_txn_id = txn_id.text
                
                amount = ret.find("TotalAmount")
                print(f"999: Amount == {amount.text}")
                
                edit_seq = ret.find("EditSequence")
                print(f"999: Edit Sequence == {edit_seq.text}")
                payment_edit_sequence = edit_seq.text
                found_payment = True

            if found_payment:
                # Move to next step: create invoice
                print("999: Step 0 -> Step 1 (receiveResponseXML1)")
                current_step = 1
                print("999: Returning -> 50")
                return 50
            else:
                # Payment not found, end process for this row
                print("999: Payment not found -> end process for this row")
                # Move to next row
                current_row_index += 1
                current_step = 0
                # If no more rows, it's done
                if current_row_index >= len(df):
                    return 100
                else:
                    # Return !100 now; next time sendRequestXML is called it will handle next row.
                    return 50

        elif current_step == 1:
            print("999: Current step == 1")
            # Expecting InvoiceAddRs
            try:
                invoice_ret = root.find(".//InvoiceRet")  # Locate InvoiceRet in the response
                if invoice_ret is not None:
                    txn_id = invoice_ret.find("TxnID")
                    if txn_id is not None:
                        invoice_txn_id = txn_id.text  # Store Invoice TxnID for the next step
                        print(f"999: Invoice Txn ID == {invoice_txn_id}")
                        print("999: Step 1 -> Step 2 (receiveResponseXML2)")
                        current_step = 2  # Move to next step
                        return 75  # Indicate progress
            except Exception as e:
                logging.error(f"Error parsing InvoiceAddRs: {e}")
            # If invoice couldn't be created, move to next row
            current_row_index += 1
            current_step = 0
            if current_row_index >= len(df):
                return 100
            else:
                return 50

        elif current_step == 2:
            # Expecting ReceivePaymentModRs - payment applied
            print("999: Step 2 -> Step 3 (receiveResponseXML2)")
            current_step = 3

            # We've completed the current row's tasks. Move to next row and reset steps.
            current_row_index += 1
            current_step = 0

            # If we're past the last row, we're done
            if current_row_index >= len(df):
                return 100
            else:
                # 50 indicates done for the current run. Next request cycle will handle the next row.
                return 50

        return 100

    @rpc(Unicode, _returns=Unicode)
    def closeConnection(ctx, ticket):
        return "Connection closed"

    @rpc(Unicode, _returns=Unicode)
    def getLastError(ctx, ticket):
        return "No error"

    @rpc(Unicode, Unicode, Unicode, _returns=Unicode)
    def connectionError(ctx, ticket, hresult, message):
        return "Connection error handled"

    @rpc(_returns=Unicode)
    def serverVersion(ctx):
        return "1.0"

    @rpc(Unicode, _returns=Unicode)
    def clientVersion(ctx, strVersion):
        return ""

soap_app = Application(
    [QBWebConnectorService],
    tns='http://developer.intuit.com/',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

wsgi_app = WsgiApplication(soap_app)
app = Flask(__name__)

def main(request):
    response_data = []
    def start_response(status, headers):
        response_data.append((status, headers))

    result = wsgi_app(request.environ, start_response)
    status, headers = response_data[0]
    body = b''.join(result)
    status_code = int(status.split(' ')[0])

    resp = app.response_class(body, status=status_code)
    for k, v in headers:
        resp.headers[k] = v
    return resp