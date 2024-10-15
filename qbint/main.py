import pandas as pd
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import gspread
from oauth2client.service_account import ServiceAccountCredentials

#Authenticate with Google Sheets API
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/parkermiconi/Desktop/qbint/creds.json', scope)
client = gspread.authorize(creds)


#Open matches Google Sheet and convert to DataFrame 1
sheet1 = client.open('FCPay3-Matches').sheet1
data1 = sheet1.get_all_values()
df1 = pd.DataFrame(data1[1:], columns=data1[0])

#DataFrame to store removed rows (Visa, Discover, etc...)
df_removed = pd.DataFrame(columns=df1.columns)

def remove_rows(df, column_name, value, df_removed):
    removed_rows = df[df[column_name] == value]
    df_removed = pd.concat([df_removed, removed_rows])
    df = df[df[column_name] != value]
    return df, df_removed

df1, df_removed = remove_rows(df1, 'Customer Name', 'Visa Cardholder', df_removed)
df1, df_removed = remove_rows(df1, 'Customer Name', 'Discover Cardmember', df_removed)
df1, df_removed = remove_rows(df1, 'Customer Name', 'Chase Visa Cardholder', df_removed)
df1, df_removed = remove_rows(df1, 'Customer Name', '', df_removed)

#Load customer json file
with open ('customers.json') as f:
    data = json.load(f)

#Check if the data is a list of dictionaries 
if isinstance(data, list) and all(isinstance(item, dict) for item in data):
    #Create second DataFrame from the list of dictionaries
    df2 = pd.DataFrame(data)
    
else:
    raise ValueError("Incorrect JSON structure")


# Convert dates from MM/DD/YYYY to YYYY-MM-DD
def convert_date(date_str):
    month, day, year = date_str.split('/')
    month = month.zfill(2)
    day = day.zfill(2)
    return f"{year}-{month}-{day}"

# Convert Tips to their value without the $
# Also convert the "special case" tip amount of "$ -" to 0
def convert_tip(tip_amount):
    if tip_amount == '$ -':
        return '0'
    elif tip_amount.startswith('$'):
        return tip_amount[1:]
    return tip_amount

# Function to pretty print XML
def prettify_xml(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

# Create Invoice Request QBXML file function
def create_qbxml(name, date, class_ref, battery, tip):
    # Create XML structure
    root = ET.Element("QBXML")
    qbxml_msgs_rq = ET.SubElement(root, "QBXMLMsgsRq", onError="stopOnError")
    invoice_add_rq = ET.SubElement(qbxml_msgs_rq, "InvoiceAddRq")

    invoice_add = ET.SubElement(invoice_add_rq, "InvoiceAdd")
    customer_ref = ET.SubElement(invoice_add, "CustomerRef")
    ET.SubElement(customer_ref, "FullName").text = name

    class_ref_elem = ET.SubElement(invoice_add, "ClassRef")
    ET.SubElement(class_ref_elem, "FullName").text = class_ref

    ET.SubElement(invoice_add, "TxnDate").text = date

    item_line1 = ET.SubElement(invoice_add, "InvoiceLineAdd")
    item_ref1 = ET.SubElement(item_line1, "ItemRef")
    ET.SubElement(item_ref1, "FullName").text = battery

    item_line2 = ET.SubElement(invoice_add, "InvoiceLineAdd")
    item_ref2 = ET.SubElement(item_line2, "ItemRef")
    ET.SubElement(item_ref2, "FullName").text = "AAA Install"
    ET.SubElement(item_line2, "Amount").text = tip

    # Generate the XML string
    xml_str = prettify_xml(root)
    
    # Remove the default XML declaration added by minidom
    xml_str = xml_str.split('\n', 1)[1]
    
    # Add XML and QBXML declarations manually
    xml_declaration = '<?xml version="1.0" encoding="utf-8"?>\n'
    qbxml_declaration = '<?qbxml version="13.0"?>\n'
    
    with open(f"{name}.xml", "w") as f:
       f.write(xml_declaration + qbxml_declaration + xml_str)

#Iterate and match
names_not_found = []
xmls = 0
total_not_found = 0
for idx, row in df1.iterrows():
    name = row['Customer Name']
    date = convert_date(row['Date'])
    class_ref = 'Franklin County' #Replace with user input to be class specific
    battery = row['SKU'] 
    #Replace empty quotes with item name from QuickBooks
    #Double check all batteries are listed
    if battery == '47E-C':
        battery = ''
    elif battery == '48AGM-C':
        battery = ''
    elif battery == '96R-C':
        battery = ''
    elif battery == '35N-C':
        battery = ''
    elif battery == '24F-C':
        battery = ''
    elif battery == '26R-C':
        battery = ''
    elif battery == '51RN-C':
        battery = ''
    elif battery == '94RAGM-C':
        battery = ''
    elif battery == '48-C':
        battery = ''
    elif battery == '124R-C':
        battery = ''
    elif battery == '75-C':
        battery = ''
    elif battery == '34-C':
        battery = ''
    elif battery == '6515-C':
        battery = ''
    elif battery == '78-XD':
        battery = ''
    elif battery == '124R-C':
        battery = ''
    elif battery == '49AGM-C':
        battery = ''
    elif battery == '47AGM-C':
        battery = ''
    elif battery == '151R-C':
        battery = ''
    elif battery == '86-C':
        battery = ''
    elif battery == '94R-C':
        battery = ''
    elif battery == '59-C':
        battery = ''
    elif battery == '65-C':
        battery = ''
    elif battery == '36R-C':
        battery = ''
    elif battery == '25-C':
        battery = ''
    elif battery == '140RAGM-C':
        battery = ''
     
    tip = convert_tip(row['Tip'])

    if name in df2['Name'].values:
        create_qbxml(name, date, class_ref, battery, tip)
        xmls += 1
    else:
        names_not_found.append(row)
        total_not_found+=1

# Print names not found
print("Names not found in the second dataframe:", [row['Customer Name']])
print("Total qbXMLs created:", xmls)
print("Total number of names not found:", total_not_found)

#Clear Google Sheet
sheet1.clear()

# Write the rows that didn't get an XML file created back to the Google Sheet
if names_not_found:
    # Convert the list of rows back to a DataFrame
    df_not_found = pd.DataFrame(names_not_found)
    
    # Write the DataFrame back to the Google Sheet
    sheet1.update([df_not_found.columns.values.tolist()] + df_not_found.values.tolist())

# Also write the removed rows to the Google Sheet
if not df_removed.empty:
    sheet1.append_rows([df_removed.columns.values.tolist()] + df_removed.values.tolist())