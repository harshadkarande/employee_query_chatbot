
import os
import boto3
import psycopg2

from pathlib import PurePosixPath
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# -----------------------------------
# CONFIGURATION
# -----------------------------------

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")
DATABASE_URL = os.getenv("DATABASE_URL")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")


if not BUCKET_NAME or not DATABASE_URL:
    raise ValueError(
        "S3_BUCKET_NAME or DATABASE_URL is missing in .env"
    )

# -----------------------------------
# S3 CONNECTION
# -----------------------------------

s3 = boto3.client(
    "s3",
    aws_access_key_id= AWS_ACCESS_KEY,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# -----------------------------------
# NEON CONNECTION
# -----------------------------------

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# -----------------------------------
# GET ALL OBJECTS FROM S3
# -----------------------------------

paginator = s3.get_paginator("list_objects_v2")

print(paginator)

total_pdfs = 0

print("Scanning S3 bucket...")

for page in paginator.paginate(Bucket=BUCKET_NAME):
    print(page)

    for obj in page.get("Contents", []):

        s3_key = obj["Key"]

        # Skip non-PDF files
        if not s3_key.lower().endswith(".pdf"):
            continue

        # Extract filename
        file_name = PurePosixPath(s3_key).name

        # Create readable document name
        document_name = PurePosixPath(s3_key).stem.replace("_", " ")

        # Extract category from folder
        path_parts = PurePosixPath(s3_key).parts

        if len(path_parts) > 1:
            category = path_parts[0]
        else:
            category = "General"

        file_size = obj.get("Size", 0)

        # S3 path
        file_url = f"s3://{BUCKET_NAME}/{s3_key}"

        # -----------------------------------
        # INSERT INTO NEON
        # -----------------------------------

        cursor.execute("""
            INSERT INTO hr_documents (
                document_name,
                file_name,
                bucket_name,
                s3_key,
                file_url,
                category,
                document_type,
                content_type,
                file_size,
                processing_status
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, 'PENDING'
            )
            ON CONFLICT (bucket_name, s3_key)
            DO UPDATE SET
                document_name = EXCLUDED.document_name,
                file_name = EXCLUDED.file_name,
                file_url = EXCLUDED.file_url,
                category = EXCLUDED.category,
                file_size = EXCLUDED.file_size,
                updated_at = CURRENT_TIMESTAMP
        """, (
            document_name,
            file_name,
            BUCKET_NAME,
            s3_key,
            file_url,
            category,
            "HR Policy",
            "application/pdf",
            file_size
        ))

        total_pdfs += 1

        print(f"Inserted/Updated: {s3_key}")

# -----------------------------------
# COMMIT CHANGES
# -----------------------------------

conn.commit()

cursor.close()
conn.close()

print("-----------------------------------")
print(f"Sync completed successfully!")
print(f"Total PDFs processed: {total_pdfs}")
print("-----------------------------------")
