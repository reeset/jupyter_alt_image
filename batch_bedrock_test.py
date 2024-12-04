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
if os.path.exists('output.txt'):
    os.remove('output.txt')
    
f = open('output.txt', 'w')

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


folder_name = "slides/"
file_list = os.listdir(folder_name)

for x in file_list: 
    # will assume all files are images
    print("processing file name" + x)
    filename = x
    image_path = folder_name + filename
    tmp_image = folder_name + filename + '.png'
    
    image_size = os.path.getsize(image_path)

    print(image_size)
    if image_size < 4000000:
        tmp_image = image_path
    else:    
        base_width = 800
        img = Image.open(image_path)
        wpercent = (base_width / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((base_width, hsize), Image.Resampling.LANCZOS)
        img.save(tmp_image)

    print(tmp_image)
    with open(tmp_image, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode()

    if tmp_image != image_path:
        # delete temp file
        os.remove(tmp_image)



    prompt = """Generate WCAG 2.1-compliant alt text, a longer description for a stand-alone image, and provide a list of subject access points for the item. The output must be in strict JSON format as follows:" _
    {\"image\":  {\"alt\": \"Alternative text\",\"desc\": \"Long-description\", \"subjects\": \"subject list delimited by a semicolon\"}
    Follow these guidelines to create appropriate and effective alt text:
    1. Image Description:
       - Describe the key elements of the image, including objects, people, scenes, and any visible text.
       - Consider the image’s role within the PDF. What information or function does it provide?
    2. WCAG 2.1 Compliance:
       a) Text in Image:
          - If duplicated nearby, use empty alt text: alt=“”
          - For functional text (e.g., icons), describe the function
          - Otherwise, include the exact text
       b) Functional Images:
          - For links/buttons, describe the action/destination
       c) Informative Images:
          - Provide a concise description of essential information
          - For complex images, summarize key data or direct to full information
       d) Decorative Images:
          - Use empty alt text: alt=“”
    3. Output Guidelines:
       - Keep alt text short, clear, and relevant and no longer than 25 words
       - Keep long description clear and relevant and no longer than 250 words
       - Subject list should capitalize the first let of the term, and provide no more than 3 subjects
       - Avoid subjective terms (e.g., "beautiful, tranquil, vintage')
       - Do not attempt to identify content you are not sure about
       - Avoid using phrases 'image of' or 'photo of' or the term 'vintage'.
       - Ensure it enhances accessibility for assistive technology users
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
    f.write(filename + "\t" + alt_text['image']['alt'] + "\t" + alt_text['image']['desc'] + "\t" + alt_text['image']['subjects'] + "\n")  # python will convert \n to os.linesep
    
print("Script has completed")