import json

def filter_negative_balances():
    # Read the original JSON file
    with open('customers_balances.json', 'r') as json_file:
        customers = json.load(json_file)
    
    # Filter customers with negative balances
    negative_customers = [customer for customer in customers if float(customer['Balance']) < 0]
    
    # Save the filtered data to a new JSON file
    with open('negative_balances.json', 'w') as json_file:
        json.dump(negative_customers, json_file, indent=4)
    
    print("Filtered JSON file with negative balances created successfully.")

if __name__ == "__main__":
    filter_negative_balances()
