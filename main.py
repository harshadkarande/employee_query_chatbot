
from config import (
    get_database_engine,
    get_s3_client
)

from extract_pdf_text import process_documents


def main():

    engine = get_database_engine()

    try:

        s3_client = get_s3_client()

        process_documents(engine,s3_client)

    finally:

        engine.dispose()


if __name__ == "__main__":

    main()
