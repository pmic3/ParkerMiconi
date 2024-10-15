from openai import OpenAI
import base64
import json
import os
from urllib.parse import urlparse
from tkinter import *
import customtkinter

def main():
    
    #Function to create a json file with the text in the designated image
    def create_json(path_name):
        #Function to encode image in base64 to be read by AI model
        def encode_image(image_path):
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

        #Pass image to be encoded and used
        local_image = path_name
        full_image_path = f'data:image/jpeg;base64,{encode_image(local_image)}'

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

        #For local image
        filename_without_extension = os.path.splitext(os.path.basename(full_image_path))[0]

        #Add .json extension to the filename
        json_filename = f'{filename_without_extension}.json'

        #Save the JSON data to a file with proper formatting
        #Make sure to be in Desktop dir
        with open('/Users/parkermiconi/Desktop/textdetectionapp/data/' + json_filename, 'w') as file:
            json.dump(json_data, file, indent=4)

        print(f'JSON data saved to {json_filename}')
        

    def print_json(path_name):
        #Function to encode image in base64 to be read by AI model
        def encode_image(image_path):
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')

        #Pass image to be encoded and used
        local_image = path_name
        full_image_path = f'data:image/jpeg;base64,{encode_image(local_image)}'

        #Create OpenAI client
        client = OpenAI(api_key='sk-proj-LLl8fvEJwl8Mi0DEKcMIT3BlbkFJhP3Z5gH2G3WqK0BSgKhM')

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
        text_box.insert('0.0', json_data)

        print('Printed to UI text box')
    
    #UI
    customtkinter.set_appearance_mode('dark')
    customtkinter.set_default_color_theme('dark-blue')

    root = customtkinter.CTk()
    root.title('Text Detection AI')
    root.geometry('800x900') #Width x Height

    def submit():
        path_name = path_name_entry.get()

        if check_var1.get() == 'on':
            #Pass function to print the text in the image
            print_json(path_name)
            
        if check_var2.get() == 'on':
            #Pass function to create a json file of the text in the image
            create_json(path_name)

    def clear():
        text_box.delete(0.0, 'end')

    def copy():
        text = ''
        text = text_box.get(0.0, 'end')
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()

        
    #Top Text (Label)
    top_text = customtkinter.CTkLabel(root, text='Enter Full File Path Name', font=('Roboto', 34), text_color='white')
    top_text.pack(pady=15)

    #Bottom text
    bottom_text = customtkinter.CTkLabel(root, text="Developed by Parker Miconi", font=('Georgia', 15))
    bottom_text.pack(side="bottom", pady=10)

    #Input box for path name
    path_name_entry = customtkinter.CTkEntry(root,
        height=35,
        width=500,
        font=('Roboto', 16)                               
        )
    path_name_entry.pack(pady=10)

    #Check Boxes
    check_var1 = customtkinter.StringVar(value='off')
    print_text_check = customtkinter.CTkCheckBox(root,
        text='Print the text in the image',
        font=('Roboto', 22),
        fg_color='red',
        variable=check_var1,
        onvalue='on',
        offvalue='off',
        checkbox_width=28,
        checkbox_height=28,
        )
    print_text_check.pack(padx=(0, 158), pady=(20, 7))

    check_var2 = customtkinter.StringVar(value='off')
    create_json_check = customtkinter.CTkCheckBox(root,
        text='Create a JSON file with the text in the image',
        font=('Roboto', 22),
        fg_color='red',
        variable=check_var2,
        onvalue='on',
        offvalue='off',
        checkbox_width=28,
        checkbox_height=28,
        )
    create_json_check.pack(padx=(19, 0),pady=(7, 10))

    #Submit button
    submit_button = customtkinter.CTkButton(root, 
        text='Submit',
        command=submit
        )
    submit_button.pack(pady=10)

    #Text box to be filled if user selects the text to be printed
    text_box = customtkinter.CTkTextbox(root,
        width=600,
        height=430                          
        )
    text_box.pack(pady=(10))
    frame = customtkinter.CTkFrame(root)
    frame.pack(pady=10)

    clear_button = customtkinter.CTkButton(frame, 
        text='Clear',
        command = clear,
        )

    copy_button = customtkinter.CTkButton(frame, 
        text='Copy',
        command = copy,
        )

    clear_button.grid(row=0, column=0, padx=10)
    copy_button.grid(row=0, column=1)

    root.mainloop()



if __name__ == "__main__":
    main()