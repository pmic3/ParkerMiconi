from openai import OpenAI
import base64
import json
import os
from urllib.parse import urlparse

#Function to encode image in base64 to be read by AI model
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

#Sample image paths
fakeinvoice1path = '/Users/parkermiconi/Desktop/textdetectionapp/sampleimages/fakeinvoice1.jpeg'
handwritteninvoice1path = '/Users/parkermiconi/Desktop/textdetectionapp/sampleimages/handwritteninvoice1.jpeg'
signwtext1path = '/Users/parkermiconi/Desktop/textdetectionapp/sampleimages/signwtext.jpeg'


#Pass image to be encoded and used
local_image = handwritteninvoice1path
full_image_path = f'data:image/jpeg;base64,{encode_image(local_image)}'
#Also possible to pass url from the internet as shown below
#image_url = 'website url here'

#Create OpenAI client
client = OpenAI(api_key='hiddenkey')

#Create chat completions
response = client.chat.completions.create(
    model='gpt-4-vision-preview',
    messages=[
        {
            'role': 'user',
            'content':[
                #Prompt to be passed into model
                {'type': 'text', 'text': 'Return JSON document with data. Only return JSON not other text'},
                {
                    'type': 'image_url',
                    'image_url': {'url': full_image_path}
                }
            ],
        }
    ],
    max_tokens=500,
)

#Extract JSON data from the response and remove the Markdown formatting
json_string = response.choices[0].message.content
json_string = json_string.replace("```json\n", "").replace("\n```", "")

#Parse the string into a JSON object
json_data = json.loads(json_string)

#For internet URL image
#filename_without_extension = os.path.splitext(os.path.basename(urlparse(image_url).path))[0]
#For local image
filename_without_extension = os.path.splitext(os.path.basename(full_image_path))[0]

#Add .json extension to the filename
json_filename = f'{filename_without_extension}.json'

#Save the JSON data to a file with proper formatting
#Make sure to be in Desktop dir
with open('/Users/parkermiconi/Desktop/textdetectionapp/data/' + json_filename, 'w') as file:
    json.dump(json_data, file, indent=4)

print(f'JSON data saved to {json_filename}')