import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import *
from fuzzywuzzy import process
import tkinter as tk
from tkinter import *
import customtkinter
from PIL import Image
import random
import os
import pkg_resources



#Authenticate with Google Sheets API
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/parkermiconi/Desktop/sss/sss_package/creds.json', scope)
client = gspread.authorize(creds)

#Opens GOPAYMENT as first Google Sheet (to be converted into DataFrame 1)
sheet1 = client.open('FCPay7-GoPayment').sheet1
data1 = sheet1.get_all_values()
df1 = pd.DataFrame(data1[1:], columns=data1[0])  #Indexed row that starts column headers (0=A)
#Rename GoPayment ID column name to "ID"
df1.rename(columns={"Auth ID": "ID"}, inplace=True)

#Opens EINVOICE as second Google Sheet (to be converted into DataFrame 2)
sheet2 = client.open('FCPay7-EInvoice').sheet1
data2 = sheet2.get_all_values()
df2 = pd.DataFrame(data2[1:], columns=data2[0])  #Indexed row that starts column headers (0=A)
#Rename E-Invoice column name to "ID"
df2.rename(columns={"Payment Type Name": "ID"}, inplace=True)

#Opens third Google Sheet (Existing sheet to be written on)
output_sheet = client.open('FC pay 7 sorted').sheet1
output_sheet.resize(rows=7000, cols=26)

#Create empty ID DataFrame from GoPayment
noid_df = df1[~(df1['ID'].astype(str).str.strip() != '')]
#Remove from GoPayment
df1 = df1[df1['ID'].astype(str).str.strip() != '']

#Creates a new DataFrame for rows where Warranty is True and adds them
warranty_df = df2[df2['Warranty'].str.startswith('Free')]
#Remove Warranty rows from df2
df2 = df2[~df2['Warranty'].str.startswith('Free')]

#Create prepaid DataFrame
prepaid_names = ['Prepaid', 'Prepay','Pre Paid', 'Pre Pay']
prepaid_df = df2[df2['ID'].str.contains('|'.join(prepaid_names), case=False)] #Created this much after the checks df. Chat GPT method for passing multiple strings. If encounter error, put all strings together seperated by | like in 'Check|Ck'
#Remove from df2. Important to catch before cash df is created
df2 = df2[~df2['ID'].str.contains('|'.join(prepaid_names), case=False)]

#Creates a new DataFrame for Free Premier Batteries and adds them
freepremier_df = df2[df2['ID'].str.contains('Free Premier Battery', case=False)]
#Remove free premier batteries from df2
df2 = df2[~df2['ID'].str.contains('Free Premier Battery', case=False)]

#Creates a new DataFrame for checks and adds them
checks_df = df2[df2['ID'].str.contains('Check|Ck', case=False)]
#Remove checks from df2
df2 = df2[~df2['ID'].str.contains('Check|Ck', case=False)]

#Creates a new DataFrame for rows where ID starts with "Cash" and adds them
cash_df = df2[df2['ID'].str.startswith('Cash')]
#Remove the "Cash" rows from df2
df2 = df2[~df2['ID'].str.startswith('Cash')]

# Function to strip prefixes
def strip_prefixes(id_with_prefix):
    prefixes = ['Visa | auth #', 'Visa | Auth #', 'Master Card | auth #', 'Master Card | Auth #', 'Visa |', 'Master Card |', 'Discover |', 'AMEX |' ] #Important to put most "descriptive" prefixes first
    for prefix in prefixes:
        if id_with_prefix.startswith(prefix):
            return id_with_prefix[len(prefix):].strip()  #Strip whitespace after removing prefix
    return id_with_prefix  #If no prefix found, return the original string

# Function to strip suffixes (New Battery)
def strip_suffixes(id_with_suffix):
    if id_with_suffix.endswith("New Battery"):
        return id_with_suffix[:-len("New Battery")].strip()  #Strip whitespace before removing suffix
    return id_with_suffix  #If no suffix found, return the original string

#Function to remove spaces from truncated IDs
def remove_spaces(id_with_space):
    return id_with_space.replace(" ", "")

# Function to make ID letters lowercase, truncate any characters making the length > 6, and add leading zeros to make each ID 6 characters long
def edit_id(id_val):
    id_val = id_val.lower() #Converts ID's letters to lowercase
    while len(id_val) > 6: #Shrinks ID to 6 letters (if longer)
        id_val = id_val[1:]
    while len(id_val) < 6: #Makes ID 6 letters by adding 0s (if shorter)
        id_val = '0' + id_val
    return id_val

#Strip prefixes suffixes, and spaces from df2 IDs
df2['ID'] = df2['ID'].apply(strip_prefixes).apply(strip_suffixes).apply(remove_spaces)

#Add zeros to IDs in df1 and df2
df1['ID'] = df1['ID'].apply(edit_id)
df2['ID'] = df2['ID'].apply(edit_id)

# Creating both variations of the unmatched DataFrames
un1 = df1[~df1['ID'].isin(df2['ID'])]
un2 = df2[~df2['ID'].isin(df1['ID'])]

#Merge df1 and df2 on 'ID' column. Every manipulation needs to be done BEFORE here
merged_df = pd.merge(df1, df2, on='ID')

unmatched_ids = pd.DataFrame()
# Match df2 ID to df1 ID that when checked against it returned the highest similarity score
for i, query in enumerate(un2["ID"]):
    result = process.extractOne(query, un1["ID"])
    best_match = result[0]  # Extracting the best match
    score = result[1]  # Extracting the similarity score

    if score >= 83:
        # Perform the same operation as before
        # Find the original index of the query in un2 DataFrame
        original_index = un2.index[un2['ID'] == query][0]
        # Create a copy of the DataFrame slice to avoid the warning
        un2_copy = un2.copy()
        un2_copy.at[original_index, "ID"] = best_match
        un2 = un2_copy
    
    else:
        # If the score is less than 83, add it to the unmatched_ids DataFrame
        unmatched_ids = pd.concat([unmatched_ids, un2.iloc[[i]]], ignore_index=True)  # Add the entire row to unmatched_ids DataFrame



#Create new DataFrame by merging the two unmatched DataFrames
#Concat them onto the main DataFrame
unmatched_merged_df = pd.merge(un1, un2, on="ID")
result = pd.concat([merged_df, unmatched_merged_df], ignore_index=True)

#Create DataFrame of unmatched GoPayment IDs
un1_indices_not_merged = ~un1['ID'].isin(unmatched_merged_df['ID'])
unmatchedgopayment_ids = un1.loc[un1_indices_not_merged]

#Only print columns neccessary for QuickBooks
columns = ['Date', 'Customer Name','ID', 'Amount', 'Tip', 'Tech Name', 'SKU']
result_subset = result[columns] 

#Delete unwanted columns
cash_df = cash_df.drop(['Store Name', 'Vehicle Description', 'Conv Fee', 'Call ID', 'Sub Total', 'Tax', 'Quantity', 'Is Member', 'VIN'], axis=1)
checks_df = checks_df.drop(['Store Name', 'Vehicle Description', 'Conv Fee', 'Call ID', 'Sub Total', 'Tax', 'Quantity', 'Is Member', 'VIN'], axis=1)
warranty_df = warranty_df.drop(['Store Name', 'Vehicle Description', 'Conv Fee', 'Call ID', 'Sub Total', 'Tax', 'Quantity', 'Is Member', 'VIN'], axis=1)
prepaid_df = prepaid_df.drop(['Store Name', 'Vehicle Description', 'Conv Fee', 'Call ID', 'Sub Total', 'Tax', 'Quantity', 'Is Member', 'VIN'], axis=1)
freepremier_df = freepremier_df.drop(['Store Name', 'Vehicle Description', 'Conv Fee', 'Call ID', 'Sub Total', 'Tax', 'Quantity', 'Is Member', 'VIN'], axis=1)
unmatched_ids = unmatched_ids.drop(['Store Name', 'Vehicle Description', 'Conv Fee'], axis=1)

#Clear existing data in Google Sheet
output_sheet.clear()


#Write all of the DataFrames into the empty Google Sheet

#Sort merged DataFrame by driver and date
result_subset = result_subset.sort_values(by=['Tech Name', 'Date'])

#Write the merged DataFrame to Google Sheet

merged_data_values = [result_subset.columns.tolist()] + result_subset.values.tolist()

#Color
# Assuming you have a dictionary `format_dict` that describes your desired formatting:
format_dict = {
    'textFormat': {'bold': True},
    'backgroundColor': {'red': 0.68, 'green': 0.85, 'blue': 0.9}
}
# Convert dictionary to CellFormat
cell_format = CellFormat(**format_dict)
#Apply formatting
format_cell_range(output_sheet, 'A1:Z1', cell_format)

#Format data for batch update
batch_update_merged = [
    {
        #Name
        'range': 'A1',
        'values': [[ 'Matches' ]],
    },
    {
        #Write
        'range': 'A2',
        'values': merged_data_values,
    },
    {
        #Empty row
        'range': f'A{str(len(merged_data_values) + 2)}',
        'values': [[]],
    }
]

#Perform the batch update
output_sheet.batch_update(batch_update_merged)


# Write the cash DataFrame to Google Sheet
cash_data_values = [cash_df.columns.tolist()] + cash_df.values.tolist()
start_row_cash = len(merged_data_values) + 3  # Start writing from the row immediately after the merged data and two empty rows
#Color 
format_cell_range(output_sheet, f'A{str(start_row_cash - 1)}:Z{str(start_row_cash - 1)}', cell_format)
#Format data for batch update
batch_update_cash = [
    {
        #Name
        'range': f'A{str(start_row_cash - 1)}',
        'values': [['Cash']],
    },
    {
        #Write
        'range': f'A{str(start_row_cash)}',
        'values': cash_data_values,
    },
    {
        #Empty row
        'range': f'A{str(start_row_cash + len(cash_data_values) + 1)}',
        'values': [[]],
    }
]

#Perform the batch update
output_sheet.batch_update(batch_update_cash)



#Write checks DataFrame into Google Sheets
checks_data_values = [checks_df.columns.tolist()] + checks_df.values.tolist()
start_row_checks = start_row_cash + len(cash_data_values) + 2
#Color
format_cell_range(output_sheet, f'A{str(start_row_checks - 1)}:Z{str(start_row_checks - 1)}', cell_format)

#Format data for batch update
batch_update_checks = [
    {
        #Name
        'range': f'A{str(start_row_checks - 1)}',
        'values': [[ 'Checks' ]],
    },
    {
        #Write
        'range': 'A' + str(start_row_checks),
        'values': checks_data_values,
    },
    {
        #Empty row
        'range': 'A' + str(start_row_checks + len(checks_data_values) + 1),
        'values': [[]],
    }
]

#Perform the batch update
output_sheet.batch_update(batch_update_checks)


#Write the warranty DataFrame to Google Sheet
warranty_data_values = [warranty_df.columns.tolist()] + warranty_df.values.tolist()
start_row_warranty = start_row_checks + len(checks_data_values) + 2  # Start writing from the row immediately after the cash data and two empty rows
#Color
format_cell_range(output_sheet, f'A{str(start_row_warranty - 1)}:Z{str(start_row_warranty - 1)}', cell_format)

#Format data for batch update
batch_update_warranty = [
    {
        #Name
        'range': f'A{str(start_row_warranty - 1)}',
        'values': [[ 'Free Warranties' ]],
    },
    {
        #Write
        'range': 'A' + str(start_row_warranty),
        'values': warranty_data_values,
    },
    {
        #Empty row
        'range': 'A' + str(start_row_warranty + len(warranty_data_values) + 1),
        'values': [[]],
    }
]

#Perform the batch update
output_sheet.batch_update(batch_update_warranty)


#Write the prepaid DataFrame to Google Sheet
prepaid_data_values = [prepaid_df.columns.tolist()] + prepaid_df.values.tolist()
start_row_prepaid = start_row_warranty + len(warranty_data_values) + 2
#Color
format_cell_range(output_sheet, f'A{str(start_row_prepaid - 1)}:Z{str(start_row_prepaid - 1)}', cell_format)

#Format data for batch update
batch_update_prepaid = [
    {
        #Name
        'range': f'A{str(start_row_prepaid - 1)}',
        'values': [[ 'Prepaids' ]],
    },
    {
        #Write
        'range': 'A' + str(start_row_prepaid),
        'values': prepaid_data_values,
    },
    {
        #Empty row
        'range': 'A' + str(start_row_prepaid + len(prepaid_data_values) + 1),
        'values': [[]],
    }
]

#Perform the batch update
output_sheet.batch_update(batch_update_prepaid)


#Write the free premier DataFrame to Google Sheet
premier_data_values = [freepremier_df.columns.tolist()] + freepremier_df.values.tolist()
start_row_premier = start_row_prepaid + len(prepaid_data_values) + 2
#Color
format_cell_range(output_sheet, f'A{str(start_row_premier - 1)}:Z{str(start_row_premier - 1)}', cell_format)

#Format data for batch update
batch_update_premier = [
    {
        #Name
        'range': f'A{str(start_row_premier - 1)}',
        'values': [[ 'Free Premier' ]],
    },
    {
        #Write
        'range': 'A' + str(start_row_premier),
        'values': premier_data_values,
    },
    {
        #Empty row
        'range': 'A' + str(start_row_premier + len(premier_data_values) + 1),
        'values': [[]],
    }
]

#Perform the batch update
output_sheet.batch_update(batch_update_premier)


#Drop unwanted columns from unmatched e-inovices
unmatched_einvoice = unmatched_ids.drop(['Call ID', 'Sub Total', 'Tax', 'Quantity', 'Warranty', 'Is Member', 'VIN'], axis=1)

#Concatenate unmatched gopayments
unmatched_gopayment = pd.concat([noid_df, unmatchedgopayment_ids])

#Put Unmatched gopayments in driver and date order
unmatched_gopayment = unmatched_gopayment.sort_values(by=["Last Name", 'Date'])


#Write the unmatched GoPayments to Google Sheet
unmatchedgp_data_values = [unmatched_gopayment.columns.tolist()] + unmatched_gopayment.values.tolist()
start_row_unmatched_gopayment = start_row_premier + len(premier_data_values) + 2  # Start writing from the row immediately after the warranty data and one empty row
#Color
format_cell_range(output_sheet, f'A{str(start_row_unmatched_gopayment - 1)}:Z{str(start_row_unmatched_gopayment - 1)}', cell_format)

#Format data for batch update
batch_update_ungp = [
    {
        #Name
        'range': f'A{str(start_row_unmatched_gopayment - 1)}',
        'values': [[ 'Unmatched GoPayments and Service Income' ]],
    },
    {
        #Write
        'range': 'A' + str(start_row_unmatched_gopayment),
        'values': unmatchedgp_data_values,
    },
    {
        #Empty row
        'range': 'A' + str(start_row_unmatched_gopayment + len(unmatchedgp_data_values) + 1),
        'values': [[]],
    }
]

#Perform the batch update
output_sheet.batch_update(batch_update_ungp)


#Write empty E-Invoices to Google Sheet
unmatchedei_data_values = [unmatched_einvoice.columns.tolist()] + unmatched_einvoice.values.tolist()
start_row_unmatched_einvoice = start_row_unmatched_gopayment + len(unmatchedgp_data_values) + 2  # Start writing from the row immediately after the warranty data and one empty row
#Color
format_cell_range(output_sheet, f'A{str(start_row_unmatched_einvoice - 1)}:Z{str(start_row_unmatched_einvoice - 1)}', cell_format)

#Format data for batch update
batch_update_unei = [
    {
        #Name
        'range': f'A{str(start_row_unmatched_einvoice - 1)}',
        'values': [[ 'Unmatched E-Invoices' ]],
    },
    {
        #Write
        'range': 'A' + str(start_row_unmatched_einvoice),
        'values': unmatchedei_data_values,
    },
]

#Perform the batch update
output_sheet.batch_update(batch_update_unei)


#Algorithm insertion to color match potential matches from the unmatched DFs

#Create lists for batch updating the formats (color)
gp_formats = []
ei_formats = []

#Modify cells in first loop before comparing with other df in second loop
real_index = 0
for index1, row1 in unmatched_gopayment.iterrows():
    
    first_name = row1['First Name']
    first_name = first_name.split()[-1]
    full_name_gp = first_name + ' ' + row1['Last Name']
    full_name_gp = full_name_gp.lower()
    amount = row1['Amount'].replace('$', '').replace(',', '').strip()
    amount = float(amount)
    tip = row1['Tip'].replace('$', '').strip()
    if tip == '-':
        tip = 0
    tip = float(tip)
    difference = amount-tip
    date1 = row1['Date']
    real_index += 1
    #Modify cells in second loop then compare
    for index2, row2 in unmatched_einvoice.iterrows():
        total = row2['Total'].replace('$', '').strip()
        total = float(total)
        date2 = row2['Invoice Date']
        name_ei = row2['Tech Name']
        name_ei = name_ei.lower()
        if name_ei == 'thomas':
            name_ei = 'thomas allen'
        if name_ei == 'christopher':
            name_ei = 'christopher jeffers'
        if name_ei == 'tommy howland':
            name_ei = 'thomas howland'
        if name_ei == 'charles':
            name_ei = 'charles montague'
        if name_ei == 'joe':
            name_ei = 'joe fromm'
        if name_ei == 'william':
            name_ei = 'william alexander'
        if name_ei == 'earnie vinson':
            name_ei = 'earnest vinson'
        if name_ei == 'shane':
            name_ei = 'shane harris' 

        #Color "maybe" matches with a unique color in both DataFrames 
        if full_name_gp == name_ei and difference == total and date1 == date2:
            
            #Create a random color and assign it
            red = random.random()
            blue = random.random()
            green = random.random()

            #Create the GoPayment dictionary to be added to the batch update to color
            new_gp_entries = {'range':f'A{str(start_row_unmatched_gopayment + real_index)}:Z{str(start_row_unmatched_gopayment + real_index)}', 
                              'format': {
                                  'backgroundColorStyle':{
                                      'rgbColor':{
                                          'red':red,
                                          'green':green,
                                          'blue':blue
                                      }
                                  }
                              }}
            gp_formats.append(new_gp_entries)

            #Create the EInvoice dictionary to be added to the batch update to color
            new_ei_entries = {'range':f'A{str(start_row_unmatched_einvoice + index2 + 1)}:Z{str(start_row_unmatched_einvoice + index2 + 1)}', 
                              'format': {
                                  'backgroundColorStyle':{
                                      'rgbColor':{
                                          'red':red,
                                          'green':green,
                                          'blue':blue
                                      }
                                  }
                              }}
            ei_formats.append(new_ei_entries)

output_sheet.batch_format(gp_formats)
output_sheet.batch_format(ei_formats)       

print("Complete")