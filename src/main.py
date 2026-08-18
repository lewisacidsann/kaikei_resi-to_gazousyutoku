from google import genai
from google.genai import types
from dotenv import load_dotenv

from pathlib import Path

import os
import json
import csv
import time

# =========================
# 設定
# =========================

MAX_RETRY = 5

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# =========================
# レシート検索
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

# =========================
# CSV準備
# =========================

csv_path = "receipts.csv"

file_exists = os.path.exists(csv_path)

csv_file = open(
    csv_path,
    "a",
    newline="",
    encoding="utf-8"
)

writer = csv.writer(csv_file)

if not file_exists:
    writer.writerow([
        "購入日",
        "購入先",
        "送料",
        "合計金額",
        "品名",
        "単価",
        "数量",
    ])

# =========================
# Geminiプロンプト
# =========================

prompt = """
このレシートから情報を抽出してください。

以下のJSONのみ出力してください。

{
  "purchase_date": "",
  "store": "",
  "shipping_fee": 0,
  "total_amount": 0,
  "items": [
    {
      "name": "",
      "unit_price": 0,
      "quantity": 0
    }
  ]
}

ルール:
- JSON以外出力しない
- 日付は YYYY-MM-DD
- 金額は数値のみ
- 分からない場合は null
"""

# =========================
# 画像ごとに処理
# =========================

for image_path in images:

    print(f"\n処理中: {image_path}")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    response = None

    for attempt in range(MAX_RETRY):

        try:

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

            break

        except Exception as e:

            print(
                f"失敗 {attempt + 1}/{MAX_RETRY}"
            )

            print(e)

            if attempt == MAX_RETRY - 1:
                print(
                    f"{image_path} をスキップ"
                )
                response = None
                break

            time.sleep(5)

    if response is None:
        continue

    try:

        data = json.loads(response.text)

    except Exception as e:

        print("JSON変換失敗")
        print(e)

        continue

    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )

    items = data.get("items", [])

    if len(items) == 0:

        writer.writerow([
            data.get("purchase_date"),
            data.get("store"),
            data.get("shipping_fee"),
            data.get("total_amount"),
            "",
            "",
            "",
        ])

        continue

    for item in items:

        writer.writerow([
            data.get("purchase_date"),
            data.get("store"),
            data.get("shipping_fee"),
            data.get("total_amount"),
            item.get("name"),
            item.get("unit_price"),
            item.get("quantity"),
        ])

csv_file.close()

print("\nCSV保存完了")