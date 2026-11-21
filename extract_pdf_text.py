
import os
import boto3
import pymupdf4llm

from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ==========================================
# 1. LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")


# ==========================================
# 2. SQLALCHEMY DATABASE CONNECTION
# ==========================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# ==========================================
# 3. AWS S3 CLIENT
# ==========================================

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)


# ==========================================
# 4. FETCH PDF PATH FROM NEON DB
# ==========================================

def fetch_pdf_documents():

    query = text("""
        SELECT
            document_name,
            file_name,
            bucket_name,
            s3_key
        FROM hr_documents
    """)

    with engine.connect() as connection:

        result = connection.execute(query)

        documents = [
            dict(row._mapping)
            for row in result
        ]

    return documents


# ==========================================
# 5. DOWNLOAD PDF FROM S3
# ==========================================
def download_pdf(bucket_name, s3_key, local_path):

    s3_client.download_file(
        bucket_name,
        s3_key,
        str(local_path)
    )

    print(f"PDF downloaded temporarily: {local_path}")


# ==========================================
# 6. EXTRACT PDF CONTENT AS MARKDOWN
# ==========================================

def extract_markdown(pdf_path):

    markdown_content = pymupdf4llm.to_markdown(
        str(pdf_path),
        table_strategy="lines",
        page_chunks=False,
        show_progress=False
    )

    return markdown_content


# ==========================================
# 7. SAVE MARKDOWN FILE
# ==========================================

def save_markdown(markdown_content, markdown_path):

    with open(markdown_path, "w", encoding="utf-8") as file:

        file.write(markdown_content)

    print(f"Markdown saved: {markdown_path}")


# ==========================================
# 8. MAIN EXECUTION
# ==========================================


from tempfile import TemporaryDirectory
from pathlib import Path

def main():

    documents = fetch_pdf_documents()

    print(f"Total PDF documents: {len(documents)}")

    # Permanent folder for Markdown files only
    output_folder = Path("output/markdown")
    output_folder.mkdir(parents=True, exist_ok=True)

    for document in documents:

        document_name = document["document_name"]
        file_name = document["file_name"]
        bucket_name = document["bucket_name"]
        s3_key = document["s3_key"]

        print(f"\nProcessing: {document_name}")

        try:

            # Create temporary directory
            with TemporaryDirectory() as temp_dir:

                temp_dir = Path(temp_dir)

                # PDF will be downloaded here temporarily
                pdf_filename = Path(file_name).name
                pdf_path = temp_dir / pdf_filename

                # Download PDF from S3
                download_pdf(
                    bucket_name,
                    s3_key,
                    pdf_path
                )

                # Extract PDF content
                markdown_content = extract_markdown(pdf_path)

                if not markdown_content.strip():
                    print("No content extracted!")
                    continue

                # Create Markdown file
                markdown_filename = (
                    Path(file_name).stem + ".md"
                )

                markdown_path = output_folder / markdown_filename

                # Save only Markdown permanently
                save_markdown(
                    markdown_content,
                    markdown_path
                )

            # Temporary PDF is automatically deleted

            print(f"Successfully processed: {document_name}")

        except Exception as error:

            print(f"Error processing {document_name}: {error}")



if __name__ == "__main__":

    try:
        main()

    finally:
        engine.dispose()
