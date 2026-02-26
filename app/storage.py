import base64
from datetime import datetime
from typing import Optional
import uuid

import boto3
from botocore.client import Config

from app.settings import settings


def s3_enabled() -> bool:
    return all([settings.S3_ENDPOINT, settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY, settings.S3_BUCKET])


def s3_client():
    # Works for MinIO + S3
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
        config=Config(signature_version="s3v4"),
    )


def put_evidence_from_b64(evidence_b64: str, prefix: str = "evidence") -> Optional[str]:
    if not s3_enabled():
        return None

    raw = base64.b64decode(evidence_b64)
    key = f"{prefix}/{datetime.utcnow().strftime('%Y/%m/%d')}/{uuid.uuid4().hex}.jpg"

    cli = s3_client()
    cli.put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=raw,
        ContentType="image/jpeg",
    )
    return key