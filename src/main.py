from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

with open("receipts/image.jpeg", "rb") as f:
    image_bytes = f.read()

prompt = """
このレシートから情報を抽出してください。

以下のJSONのみを出力してください。

{
  "purchase_date": "",
  "store": "",
  "total_amount": 0
}

JSON以外出力しないこと。
"""

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=[
        prompt,
        types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg",
        ),
    ],
)


print(response.text)