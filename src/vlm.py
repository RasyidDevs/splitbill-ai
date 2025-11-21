from openai import OpenAI
import os
import base64
import sys
import streamlit as st 
import json 

sys.path.append(os.path.dirname(__file__))
from prompt import split_bill_prompt

class SplitBillGPT:
     def __init__(self,  template=split_bill_prompt ):
          _api_key = st.secrets["api"]["openai"]
          self.client = OpenAI(api_key=_api_key)
          self.template = template
     def encode_image(self, image_file):
          """
          This method allows to encode image to base64
          """
          try:
            file_bytes = image_file.read()
            return base64.b64encode(file_bytes).decode("utf-8")
          except Exception as e:
              print("error")
          
     def response(self, mime_type, image_file):
         """
         This method allows you to generate output from GPT Models
         """
         response = self.client.responses.create(
                model="gpt-4.1",
                input=[
                    {
                        "role": "user",
                        "content": [
                            { "type": "input_text", "text": split_bill_prompt},
                            {
                                "type": "input_image",
                                "image_url": f"data:{mime_type};base64,{self.encode_image(image_file=image_file)}",
                            },
                        ],
                    }
                ],
            )
         try:
            response_json = json.loads(response.output_text)
            return response_json
         except json.JSONDecodeError as e:
            raise ValueError(f"Gagal parse JSON dari GPT output: {e}\nOutput: {response.output_text}")
         
 