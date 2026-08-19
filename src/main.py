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
        "通し番号",
        "購入日",
        "品名",
        "単価",
        "数量",
        "送料",
        "その品目の合計金額",
        "購入先",
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
  "items": [
    {
      "name": "",
      "unit_price": 0,
      "quantity": 1
    }
  ]
}

ルール:
- JSON以外出力しない
- 日付は YYYY-MM-DD
- 金額は数値のみ
- quantity が不明なら 1
- unit_price が不明なら 0
- shipping_fee が無い場合は 0
- store が不明なら ""
"""

# =========================
# レシート処理
# =========================

for image_path in images:

    print(f"\n処理中: {image_path}")

    receipt_id = image_path.stem

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
            receipt_id,
            data.get("purchase_date"),
            "",
            "",
            "",
            data.get("shipping_fee"),
            "",
            data.get("store"),
        ])

        continue

    for item in items:

        unit_price = item.get("unit_price") or 0
        quantity = item.get("quantity") or 1

        item_total = unit_price * quantity

        writer.writerow([
            receipt_id,                    # 通し番号
            data.get("purchase_date"),     # 購入日
            item.get("name"),              # 品名
            unit_price,                    # 単価
            quantity,                      # 数量
            data.get("shipping_fee"),      # 送料
            item_total,                    # 品目合計
            data.get("store"),             # 購入先
        ])

csv_file.close()

print("\nCSV保存完了")