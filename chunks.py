
import json

from pathlib import Path

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter
)


# ==========================================
# 1. MARKDOWN HEADER CONFIGURATION
# ==========================================

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]


# ==========================================
# 2. RECURSIVE CHUNK CONFIGURATION
# ==========================================

recursive_splitter = RecursiveCharacterTextSplitter(

    chunk_size=1000,

    chunk_overlap=150,

    length_function=len,

    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]

)


# ==========================================
# 3. MARKDOWN HEADER SPLITTING
# ==========================================

def split_by_markdown_headers(markdown_content):

    markdown_splitter = MarkdownHeaderTextSplitter(

        headers_to_split_on=headers_to_split_on,

        strip_headers=False

    )

    header_chunks = markdown_splitter.split_text(
        markdown_content
    )

    return header_chunks


# ==========================================
# 4. RECURSIVE CHARACTER SPLITTING
# ==========================================

def split_recursively(header_chunks):

    final_chunks = recursive_splitter.split_documents(
        header_chunks
    )

    return final_chunks


# ==========================================
# 5. COMPLETE CHUNKING PIPELINE
# ==========================================

def create_chunks(markdown_content, document_name):

    header_chunks = split_by_markdown_headers(
        markdown_content
    )

    final_chunks = split_recursively(
        header_chunks
    )

    for index, chunk in enumerate(final_chunks):

        chunk.metadata["document_name"] = document_name

        chunk.metadata["chunk_index"] = index

    return final_chunks


# ==========================================
# 6. SAVE CHUNKS AS JSONL
# ==========================================

def save_chunks(chunks, output_path):

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(output_path, "w", encoding="utf-8") as file:

        for chunk in chunks:

            chunk_data = {

                "content": chunk.page_content,

                "metadata": chunk.metadata

            }

            file.write(
                json.dumps(chunk_data, ensure_ascii=False) + "\n"
            )

    print(f"Chunks saved: {output_path}")


# ==========================================
# 7. PROCESS MARKDOWN CONTENT
# ==========================================

def process_markdown_content(
    markdown_content,
    document_name,
    output_folder="output/chunks"
):

    if not markdown_content.strip():

        print(f"Empty Markdown content: {document_name}")

        return []

    # Create chunks directly from extracted text
    chunks = create_chunks(
        markdown_content,
        document_name
    )

    # Define output file
    output_path = (
        Path(output_folder) /
        f"{document_name}.jsonl"
    )

    # Save chunks
    save_chunks(
        chunks,
        output_path
    )
    
    print(f"Total chunks created: {len(chunks)}")

    return chunks
