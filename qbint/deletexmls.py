import os
import glob

def delete_xml_files(folder_path):
    # Construct the search pattern for XML files
    search_pattern = os.path.join(folder_path, "*.xml")
    
    # Find all files that match the pattern
    xml_files = glob.glob(search_pattern)
    
    # Iterate over the list of files and delete each one
    for xml_file in xml_files:
        try:
            os.remove(xml_file)
            print(f"Deleted: {xml_file}")
        except Exception as e:
            print(f"Error deleting {xml_file}: {e}")

# Specify the folder path
folder_path = "/Users/parkermiconi/Desktop/qbint"

# Call the function to delete XML files
delete_xml_files(folder_path)
