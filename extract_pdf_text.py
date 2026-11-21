
import os
import boto3
import fitz  # PyMuPDF

from dotenv import load_dotenv
from pathlib import PurePosixPath

# Load environment variables
load_dotenv()

# -----------------------------------------
# CONFIGURATION
# -----------------------------------------

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

if not BUCKET_NAME:
    raise ValueError("S3_BUCKET_NAME is missing in .env")

# -----------------------------------------
# S3 CONNECTION
# -----------------------------------------

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION
)

# -----------------------------------------
# OUTPUT FOLDER
# -----------------------------------------

OUTPUT_FOLDER = "extracted_markdown"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# -----------------------------------------
# PDF TO MARKDOWN EXTRACTION
# -----------------------------------------

def extract_pdf_to_markdown(pdf_bytes, document_name):

    pdf_document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    markdown_content = []

    # Document title
    markdown_content.append(f"# {document_name}\n")

    markdown_content.append(
        "> Source: HR Policy Document\n"
    )

    # Extract text page by page
    for page_number, page in enumerate(pdf_document, start=1):

        text = page.get_text("text").strip()

        if not text:
            text = "*No extractable text found on this page.*"

        markdown_content.append(
            f"\n---\n\n## Page {page_number}\n\n{text}\n"
        )

    pdf_document.close()

    return "\n".join(markdown_content)


# -----------------------------------------
# FETCH PDFs FROM S3
# -----------------------------------------

paginator = s3.get_paginator("list_objects_v2")

total_pdfs = 0

print("Starting PDF to Markdown extraction...")

for page in paginator.paginate(Bucket=BUCKET_NAME):

    for obj in page.get("Contents", []):

        s3_key = obj["Key"]

        # Process only PDF files
        if not s3_key.lower().endswith(".pdf"):
            continue

        file_name = PurePosixPath(s3_key).name

        document_name = PurePosixPath(s3_key).stem.replace("_", " ")

        print(f"\nProcessing: {file_name}")

        try:

            # Download PDF into memory
            response = s3.get_object(
                Bucket=BUCKET_NAME,
                Key=s3_key
            )

            pdf_bytes = response["Body"].read()

            # Extract Markdown
            markdown_text = extract_pdf_to_markdown(
                pdf_bytes,
                document_name
            )

            # Save as Markdown file
            output_file = (
                PurePosixPath(s3_key).stem + ".md"
            )

            output_path = os.path.join(
                OUTPUT_FOLDER,
                output_file
            )

            with open(
                output_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(markdown_text)

            total_pdfs += 1

            print(f"Successfully extracted: {output_file}")

        except Exception as e:

            print(f"Failed to process {file_name}: {e}")


# -----------------------------------------
# COMPLETION
# -----------------------------------------

print("\n----------------------------------")
print("Markdown extraction completed!")
print(f"Total PDFs processed: {total_pdfs}")
print(f"Output folder: {OUTPUT_FOLDER}")
print("----------------------------------")
