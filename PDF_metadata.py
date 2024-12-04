import os
import boto3
import json
import dotenv
from PIL import Image
import base64
import sys

def print_to_stderr(*a):
 
    # Here a is the array holding the objects
    # passed as the argument of the function
    print(*a, file=sys.stderr)


#setup the save file
if os.path.exists('pdf_output.txt'):
    os.remove('pdf_output.txt')
    
f = open('pdf_output.txt', 'w')

dotenv.load_dotenv(".env", override=True)
# set our credentials from the environment values loaded form the .env file
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION')


# instantiate a bedrock client using boto3 (AWS' official Python SDK)
bedrock_runtime_client = boto3.client(
    'bedrock-runtime',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# select the model id
model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"


folder_name = "pdfs/"
file_list = os.listdir(folder_name)

for x in file_list: 
    # will assume all files are images
    print("processing file name" + x)
    filename = x
    image_path = folder_name + filename
    


    with open(image_path, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode()





    prompt = """The data provided is a theses from Ohio State University.  From the document, Extract data out the document and place it in strict json format:" _
    {\"pdf\":  {\"title\": \"Title text\",\"author\": \"author text\", \"subjects\": \"subject list delimited by a semicolon\", \"department\" : \"Department of the theses\", \"year\" : \"year of the publication\"}
    
    1. Output Guidelines:
       - Subject list should capitalize the first let of the term, and provide no more than 3 subjects           
    Remember:
    - Provide only the JSON output with no additional explanation
    - Do not use unnecessary phrases like “Certainly!” or “Here’s the alt text:”
    - If you’re unsure about specific details, focus on describing what you can clearly determine from the context provided
    Now, based on the information given and these guidelines, generate the appropriate alt text in the required JSON format."""

    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": encoded_image
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "max_tokens": 10000,
        "anthropic_version": "bedrock-2023-05-31"
    }


    # we're ready to invoke the model!
    response = bedrock_runtime_client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        body=json.dumps(payload)
    )

    # now we need to read the response. It comes back as a stream of bytes 
    # so if we want to display the response in one go we need to read the full stream first
    # then convert it to a string as json and load it as a dictionary 
    # so we can access the field containing the content without all the metadata noise
    output_binary = response["body"].read()
    output_json = json.loads(output_binary)
    output = output_json["content"][0]["text"]

    # save the output
    
    
    alt_text = json.loads(output)
    f.write(filename + "\t" + alt_text['pdf']['title'] + "\t" + alt_text['pdf']['author'] + "\t" + alt_text['pdf']['subjects'] + "\t" + alt_text['pdf']['department'] + alt_text['pdf']['year'] + "\t""\n")  # python will convert \n to os.linesep
    
print("Script has completed")