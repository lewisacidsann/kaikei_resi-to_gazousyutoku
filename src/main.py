from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

with open("receipt.jpg", "rb") as f:
    image_bytes = f.read()

prompt = """
レシートから以下のJSONのみ出力してください

{
  "purchase_date":"",
  "store":"",
  "total_amount":0
}
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        prompt,
        {
            "mime_type": "image/jpeg",
            "data": image_bytes,
        }
    ]
)

print(response.text)