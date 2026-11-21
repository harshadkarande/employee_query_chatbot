
from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf4llm
from chunks  import process_markdown_content
from sqlalchemy import text

from database import insert_document_chunks
from embeddings import generate_embeddings


# =====================================
# 1. FETCH DOCUMENTS FROM DATABASE
# =====================================

def fetch_pdf_documents(engine):

    query = text("""
        SELECT
            document_id,
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


# =====================================
# 2. DOWNLOAD PDF FROM S3
# =====================================

def download_pdf(s3_client, bucket_name, s3_key, local_path):

    s3_client.download_file(
        bucket_name,
        s3_key,
        str(local_path)
    )


# =====================================
# 3. EXTRACT PDF AS MARKDOWN
# =====================================

def extract_markdown(pdf_path):

    markdown_content = pymupdf4llm.to_markdown(
        str(pdf_path),
        table_strategy="lines",
        page_chunks=False,
        show_progress=True
    )

    return markdown_content


# =====================================
# 4. SAVE MARKDOWN FILE
# =====================================

def save_markdown(markdown_content, markdown_path):

    with open(markdown_path, "w", encoding="utf-8") as file:

        file.write(markdown_content)


# =====================================
# 5. PROCESS ALL DOCUMENTS
# =====================================

def process_documents(engine, s3_client):

    documents = fetch_pdf_documents(engine)

    print(f"Total PDF documents: {len(documents)}")

    output_folder = Path("output/markdown")

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )
    all_chunks = []
    for document in documents:
        document_id = document['document_id']
        document_name = document["document_name"]
        file_name = document["file_name"]
        bucket_name = document["bucket_name"]
        s3_key = document["s3_key"]

        print(f"\nProcessing: {document_name}")

        try:

            with TemporaryDirectory() as temp_dir:

                temp_dir = Path(temp_dir)

                # Temporary PDF location
                pdf_filename = Path(file_name).name

                pdf_path = temp_dir / pdf_filename

                # Download PDF
                download_pdf(
                    s3_client,
                    bucket_name,
                    s3_key,
                    pdf_path
                )

                print("PDF downloaded successfully")

                # Extract Markdown
                markdown_content = extract_markdown(pdf_path)

                if not markdown_content.strip():

                    print("No content extracted!")
                    continue

                # Markdown output path
                markdown_filename = (
                    Path(file_name).stem + ".md"
                )

                markdown_path = (
                    output_folder / markdown_filename
                )

                # Save Markdown
                save_markdown(
                    markdown_content,
                    markdown_path
                )
                chunks = process_markdown_content(
                    markdown_content=markdown_content,
                    document_name=Path(file_name).stem
                )
                all_chunks.extend(chunks)

                embeddings = generate_embeddings(chunks)

                insert_document_chunks(

                    engine=engine,

                    document_id=document_id,

                    chunks=chunks,

                    embeddings=embeddings
                    )

                print(
                    f"Successfully created {len(chunks)} chunks "
                    f"for {document_name}"
                )

            print(f"Successfully processed: {document_name}")
        except Exception as error:

            print(
                f"Error processing {document_name}: {error}"
            )
    print(f"\nTotal chunks generated: {len(all_chunks)}")

    return all_chunks