
import os
import boto3

from dotenv import load_dotenv
from sqlalchemy import create_engine


# Load environment variables
load_dotenv()


def get_required_env(variable_name):
    value = os.getenv(variable_name)

    if not value:
        raise ValueError(
            f"Missing environment variable: {variable_name}"
        )

    return value


# Database configuration
DATABASE_URL = get_required_env("DATABASE_URL")


# AWS configuration
AWS_REGION = get_required_env("AWS_REGION")
AWS_ACCESS_KEY = get_required_env("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = get_required_env("AWS_SECRET_ACCESS_KEY")


def get_database_engine():

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )

    return engine


def get_s3_client():

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

    return s3_client
