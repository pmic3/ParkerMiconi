import pandas as pd
import numpy as np
import json
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import *
from google.cloud import storage
from flask import Flask, request

app = Flask(__name__)

SCOPES = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

@app.route('/', methods=['POST'])
def hello_world(request):
    
    # --------------------------------------------------------------------
    # Google Sheets Auth
    # --------------------------------------------------------------------
    
    # Variables
    bucket_name = 'bubble_test_bucket'
    folder_name = 'sheets_creds'
    file_name = 'creds.json'
    object_path = f"{folder_name}/{file_name}"

    # Initialize the Storage client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_path)

    # Download the credentials file as a string
    creds_data = blob.download_as_text()
    credentials_dict = json.loads(creds_data)

    # Create Credentials object for Google Sheets API
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scopes=SCOPES)
    
    client = gspread.authorize(credentials)
    
    
    
    
    # Ensure Customer Report file came over
    if 'custRep' not in request.files:
        return "File(s) not found in request", 400
    
    # Get dynamic data from bubble
    uploaded_cust_rep = request.files['custRep']
    location = request.form.get('class', 'No class listed')
    print(f"999: Location: {location}")
    pay_period = request.form.get('pay', 'No Pay Period Added')
    print(f"999: Pay period: {pay_period}")
    matches_sheet_name = request.form.get('matches', 'No sheet entered')
    print(f"999: Matches Name: {matches_sheet_name}")
    start_range = int(request.form.get('start', 0))
    print(f"999: Start Range: {start_range}")
    end_range = int(request.form.get('end', 400))
    print(f"999: End Range: {end_range}")

    # Get the matches dataframe from Google Sheets
    sheet1 = client.open(matches_sheet_name).sheet1
    matches_data = sheet1.get_all_values()
    matches_df = pd.DataFrame(matches_data[start_range:end_range], columns=matches_data[start_range - 1])

    # Process Customer Report file if it is a CSV and create dataframe
    try:
        cust_df = pd.read_csv(io.StringIO(uploaded_cust_rep.stream.read().decode('utf-8')))
    except Exception as e:
        return f"Error processing file: {e}", 400

    
    

    # --------------------------------------------------------------------
    # DataFrame manipulation logic
    # --------------------------------------------------------------------
    
    # Rename report columns headers
    cust_df.columns = ['Name', 'Amount']
    
    # Remove everything in Amount that isn't a digit or a decimal point (or - for cust_rep)
    matches_df['Amount'] = matches_df['Amount'].str.replace(r'[^\d.]', '', regex=True).astype(float)
    cust_df['Amount'] = cust_df['Amount'].str.replace(r'[^\d.-]', '', regex=True)

    # Convert names to lowercase
    matches_df['Customer Name'] = matches_df['Customer Name'].str.lower()
    cust_df['Name'] = cust_df['Name'].str.lower()

    # Replace empty strings with NaN
    cust_df['Amount'] = cust_df['Amount'].replace('', np.nan)
    
    # Convert cust_df Amount from string to float
    cust_df['Amount'] = cust_df['Amount'].astype(float)
    
    # Create a helper column in both DataFrames for absolute Amount
    matches_df['abs_Amount'] = matches_df['Amount'].abs()
    cust_df['abs_Amount'] = cust_df['Amount'].abs()
    
    matches_df = matches_df.rename(columns={'Customer Name': 'Name'})
    
    # Merge to check which rows have a matching (Name, abs_Amount) in cust_df
    merged = matches_df.merge(cust_df[['Name', 'abs_Amount']], 
                           on=['Name', 'abs_Amount'], 
                           how='left', 
                           indicator=True)
    
    # Rows that do not match (left_only) should be removed
    removed = merged[merged['_merge'] == 'left_only'].copy()
    # Rows that match (both) will remain
    kept = merged[merged['_merge'] == 'both'].copy()

    # Drop the helper and merge indicator columns
    kept.drop(['abs_Amount', '_merge'], axis=1, inplace=True)
    removed.drop(['abs_Amount', '_merge'], axis=1, inplace=True)

    
    
    
    # --------------------------------------------------------------------
    # Download removed logic
    # --------------------------------------------------------------------

    # Create new Google Sheet
    new_sheet_name = f"{location}{pay_period} Removed"
    spreadsheet = client.create(new_sheet_name)

    # Share the sheet
    spreadsheet.share('parkermiconi@gmail.com', perm_type='user', role='writer')

    # Access the first worksheet of the new spreadsheet
    worksheet = spreadsheet.get_worksheet(0) 

    # Begin writing the removed DataFrame to Google Sheet 
    removed_values = [removed.columns.tolist()] + removed.values.tolist()
    
    # Color
    # Assuming you have a dictionary `format_dict` that describes your desired formatting:
    format_dict = {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.68, 'green': 0.85, 'blue': 0.9}
    }
    # Convert dictionary to CellFormat
    cell_format = CellFormat(**format_dict)

    # Apply formatting
    format_cell_range(worksheet, 'A1:Z1', cell_format)

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
            'values': removed_values,
        },
        {
            #Empty row
            'range': f'A{len(removed_values) + 2}',
            'values': [[]],
        }
    ]

    #Perform the batch update and write the removed dataframe to the new Google Sheet
    worksheet.batch_update(batch_update_merged)


    
    
    
    # Replace "$ -" Tip with 0
    kept['Tip'] = kept['Tip'].replace({'$ -': '0'})
    # Remove everything in Tip that isn't a digit or a decimal point
    kept['Tip'] = kept['Tip'].str.replace(r'[^\d.]', '', regex=True).astype(float)
    # Convert to numeric
    kept['Tip'] = pd.to_numeric(kept['Tip'], errors='coerce')

    # List of strings to remove
    strings_to_remove = ['visa cardholder', 'mobile', 'discover cardmember', 'chase visa cardholder']
    # Filter out rows containing any of those strings ^
    kept = kept[~kept['Name'].str.contains('|'.join(strings_to_remove), regex=True)]

    # Create a new class column and assign it the value gotten from Bubble
    kept['Class'] = location

    
    
    
    # 2. Convert DataFrame to JSON
    df_records = kept.to_dict(orient='records')
    json_str = json.dumps(df_records)  

    # 3. Upload the JSON to GCS
    bucket_name = "bubble_test_bucket" 
    blob_name = f"test_dataframes/to_iterate.json"

    # Initialize Storage client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Upload
    blob.upload_from_string(json_str, content_type='application/json')

    # 4. Return success message
    response = {
        "status": "success",
        "message": f"Uploaded DataFrame JSON to gs://{bucket_name}/{blob_name}",
    }
    return (json.dumps(response), 200, {"Content-Type": "application/json"})