from google import genai
from google.genai import types

from dotenv import load_dotenv

from pathlib import Path

import os
import json
import csv

# =========================
# 設定
# =========================

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# =========================
# レシート画像検索
# =========================

receipt_dir = Path("receipts")

images = (
    list(receipt_dir.glob("*.jpg"))
    + list(receipt_dir.glob("*.jpeg"))
    + list(receipt_dir.glob("*.png"))
)

if len(images) == 0:
    raise FileNotFoundError(
        "receiptsフォルダに画像がありません"
    )

image_path = images[0]

print(f"読み込みファイル: {image_path}")

# =========================
# 画像読み込み
# =========================

with open(image_path, "rb") as f:
    image_bytes = f.read()

# =========================
# Geminiへ送信
# =========================

prompt = """
このレシートから情報を抽出してください。

以下のJSONのみ出力してください。

{
  "purchase_date": "",
  "store": "",
  "total_amount": 0
}

ルール:
- JSON以外出力しない
- 日付は YYYY-MM-DD
- 金額は数値のみ
"""

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=[
        prompt,
        types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg"
        )
    ],
    config=types.GenerateContentConfig(
        response_mime_type="application/json"
    )
)

# =========================
# JSON変換
# =========================

data = json.loads(response.text)

print("取得データ")
print(json.dumps(data, ensure_ascii=False, indent=2))

# =========================
# CSV保存
# =========================

csv_path = "receipts.csv"

file_exists = os.path.exists(csv_path)

with open(
    csv_path,
    "a",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)

    if not file_exists:
        writer.writerow([
            "購入日",
            "購入先",
            "金額"
        ])

    writer.writerow([
        data["purchase_date"],
        data["store"],
        data["total_amount"]
    ])

print("CSV保存完了")