import fitz
import os
import boto3
import time
import logging
import re

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# =========================================================
# CONFIG
# =========================================================

def get_config():
    """Get configuration from environment or defaults"""
    return {
        "BUCKET_NAME": os.getenv("S3_BUCKET", "tfs-faq-poc"),
        "OUTPUT_PREFIX": os.getenv("S3_OUTPUT_PREFIX", "tfs-form-filling-bucket/outputs/")
    }

config = get_config()

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(TOOLS_DIR, "templates", "lease_end_template.pdf")

# Initialize S3 client
s3 = boto3.client("s3")

# =========================================================
# REQUIRED FIELDS
# =========================================================

REQUIRED_FIELDS = [
    "name",
    "vin",
    "account_number",
    "make",
    "model",
    "body_type",
    "year",
    "miles",
    "date",
    "address"
]

# =========================================================
# FIELD MAP
# =========================================================

FIELD_MAPPING = [
    {"field": "name", "anchor_text": "Lessee's Name", "fill_all": True},
    {"field": "vin", "anchor_text": "VEHICLE IDENTIFICATION NUMBER", "placement": "below"},
    {"field": "account_number", "anchor_text": "ACCOUNT NUMBER", "placement": "below"},
    {"field": "make", "anchor_text": "MAKE", "placement": "below"},
    {"field": "model", "anchor_text": "MODEL", "placement": "below"},
    {"field": "body_type", "anchor_text": "BODY TYPE", "placement": "below"},
    {"field": "year", "anchor_text": "YEAR", "placement": "below"},
    {"field": "miles", "anchor_text": "odometer now reads", "placement": "right"},
    {"field": "date", "anchor_text": "Date of Statement", "placement": "right"},
    {"field": "address", "anchor_text": "Lessee's Address", "placement": "below"},
    {"field": "signature", "anchor_text": "(Lessee's Signature)", "conditional": "confirm_signature"}
]

# =========================================================
# OFFSETS
# =========================================================

FIELD_X_OFFSET = {
    "name": 34,
    "vin": 10,
    "account_number": 10,
    "make": 10,
    "model": 55,
    "body_type": 10,
    "year": 35,
    "miles": 70,
    "date": 15,
    "address": 0,
    "signature": 10
}

# =========================================================
# SANITIZE VALUES
# =========================================================

def clean_value(value):
    if not isinstance(value, str):
        return str(value)

    value = re.split(
        r'(VIN:|Account number:|Make:|Model:|Body type:|Year:|Miles:|Date:|Address:|confirm_signature:)',
        value
    )[0]

    return value.strip()

# =========================================================
# NORMALIZE INPUT
# =========================================================

def normalize_data(data):
    cleaned = {}

    for key in REQUIRED_FIELDS:
        if key in data:
            cleaned[key] = clean_value(data[key])

    return cleaned

# =========================================================
# PDF FILL
# =========================================================

def fill_pdf(data, confirm_signature=False):
    data = normalize_data(data)

    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]

    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    outputs_dir = os.path.join(TOOLS_DIR, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    output_file = os.path.join(
        outputs_dir,
        f"filled_odometer_statement_{int(time.time())}.pdf"
    )

    doc = fitz.open(TEMPLATE_PATH)

    for mapping in FIELD_MAPPING:
        field = mapping["field"]
        anchor_text = mapping["anchor_text"]
        placement = mapping.get("placement", "right")
        fill_all = mapping.get("fill_all", False)
        conditional_flag = mapping.get("conditional")

        if conditional_flag == "confirm_signature" and not confirm_signature:
            continue

        value = data.get("name") if field == "signature" else data.get(field)

        if not value:
            continue

        anchor_words = anchor_text.lower().split()
        inserted = False

        for page in doc:
            words = page.get_text("words")

            for i in range(len(words)):
                candidate = words[i:i+len(anchor_words)]

                candidate_text = " ".join(w[4].lower() for w in candidate)

                if candidate_text == " ".join(anchor_words):
                    first = candidate[0]
                    last = candidate[-1]

                    anchor_rect = fitz.Rect(
                        first[0],
                        first[1],
                        last[2],
                        last[3]
                    )

                    if field == "signature":
                        insert_point = fitz.Point(anchor_rect.x0, anchor_rect.y0 - 8)

                    elif field == "name":
                        if not inserted:
                            insert_point = fitz.Point(anchor_rect.x1 + 34, anchor_rect.y1 - 2)
                        else:
                            insert_point = fitz.Point(anchor_rect.x0, anchor_rect.y0 - 8)

                    elif placement == "below":
                        insert_point = fitz.Point(anchor_rect.x0, anchor_rect.y1 + 14)

                    else:
                        insert_point = fitz.Point(
                            anchor_rect.x1 + FIELD_X_OFFSET.get(field, 20),
                            anchor_rect.y1 - 2
                        )

                    page.insert_text(insert_point, str(value), fontsize=10)

                    inserted = True

                    logger.debug(f"{field} inserted: {value}")

                    if not fill_all:
                        break

            if inserted and not fill_all:
                break

    doc.save(output_file)
    doc.close()

    return output_file

# =========================================================
# S3 UPLOAD
# =========================================================

def upload_to_s3(local_file):
    output_key = f"{config['OUTPUT_PREFIX']}{os.path.basename(local_file)}"

    with open(local_file, "rb") as f:
        s3.put_object(
            Bucket=config['BUCKET_NAME'],
            Key=output_key,
            Body=f,
            ContentType="application/pdf"
        )

    return f"https://{config['BUCKET_NAME']}.s3.amazonaws.com/{output_key}"

# =========================================================
# TOOL WRAPPER
# =========================================================

def form_fill_tool(data, confirm_signature=False):
    try:
        pdf_path = fill_pdf(data, confirm_signature)
        url = upload_to_s3(pdf_path)

        return {
            "status": "success",
            "download_url": url
        }

    except Exception as e:
        logger.exception("Form fill failed")

        return {
            "status": "error",
            "message": f"Form fill error: {str(e)}"
        }
