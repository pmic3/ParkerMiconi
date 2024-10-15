import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Sample DataFrames (replace with your actual data)
df1 = pd.DataFrame({
    'Customer Name': ['Alice', 'Bob', 'Charlie'],
    'Date': ['1/1/2023', '11/4/2023', '10/15/2024'],
    'item1': ['ItemA', 'ItemB', 'ItemC'],
    'Tip': ['$ -', '$34.56', '$12.34'],
    'Class': ['ClassA', 'ClassB', 'ClassC']
})

df2 = pd.DataFrame({
    'name': ['Alice', 'Charlie', 'Eve']
})

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
def create_qbxml(name, date, class_ref, item1, tip):
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
    ET.SubElement(item_ref1, "FullName").text = item1

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

# Iterate and match
names_not_found = []
for idx, row in df1.iterrows():
    name = row['Customer Name']
    date = convert_date(row['Date'])
    class_ref = row['Class']
    item1 = row['item1']
    tip = convert_tip(row['Tip'])

    if name in df2['name'].values:
        create_qbxml(name, date, class_ref, item1, tip)
    else:
        names_not_found.append(name)

# Print names not found
print("Names not found in the second dataframe:", names_not_found)

