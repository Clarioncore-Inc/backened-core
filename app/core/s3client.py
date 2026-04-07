from typing import Dict, Any, Optional
import logging
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from app import settings
from io import BytesIO
import urllib.parse


def get_s3_client():
    return boto3.client(
        service_name="s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_CLIENT_BUCKET_REGION,
        config=Config(s3={"addressing_style": "path"},
                      signature_version="s3v4"),
    )


def get_s3_resource():
    return boto3.resource(
        service_name="s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_CLIENT_BUCKET_REGION,
    )


class S3Service:
    def __init__(self, base_path: str = "", bucket_name=settings.AWS_STORAGE_BUCKET_NAME):
        self.client = get_s3_client()
        self.bucket_name = bucket_name
        self.base_path = base_path.rstrip('/') + '/' if base_path else ""
        self.expiry = 3600
        self.max_size = settings.FILE_UPLOAD_MAX_MEMORY_SIZE

    def _path(self, key: str) -> str:
        """Add base path if provided"""
        if not self.base_path or key.startswith(self.base_path):
            return key
        return f"{self.base_path}{key}"

    def _remove_base_path(self, key: str) -> str:
        """Remove base path from key for external use"""
        if self.base_path and key.startswith(self.base_path):

            return key[len(self.base_path):]
        return key

    def generate_presigned_post(self,  file_path: str, file_type: str) -> Dict[str, Any]:
        try:
            presigned_data = self.client.generate_presigned_post(
                self.bucket_name,
                self._path(file_path),
                Fields={"Content-Type": file_type},
                Conditions=[
                    {"Content-Type": file_type},
                    ["content-length-range", 1, self.max_size],
                ],
                ExpiresIn=self.expiry,
            )
            return presigned_data
        except ClientError as e:
            logging.error(f"Failed to generate presigned POST URL: {e}")
            raise

    def generate_presigned_put(self, *, file_path: str, file_type: str,
                               expires_in: Optional[int] = None) -> Optional[str]:

        if expires_in is None:
            expires_in = self.expiry

        try:
            presigned_url = self.client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': self._path(file_path),
                    'ContentType': file_type
                },
                ExpiresIn=expires_in
            )
            return presigned_url
        except ClientError as e:
            logging.error(f"Failed to generate presigned PUT URL: {e}")
            return None

    def create_presigned_url(self, object_name: str, expires_in: Optional[int] = None) -> Optional[str]:
        if expires_in is None:
            expires_in = self.expiry

        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name,
                        "Key": self._path(object_name)},
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            logging.error(f"Failed to generate presigned URL: {e}")
            return None

    def get_file(self, object_name: str, download_path: Optional[str] = None) -> Optional[bytes]:
        key = self._path(object_name)
        try:
            if download_path:
                self.client.download_file(self.bucket_name, key, download_path)
                logging.info(f"File downloaded to {download_path}")
                return None
            else:
                obj = self.client.get_object(Bucket=self.bucket_name, Key=key)
                return obj["Body"].read()
        except ClientError as e:
            logging.error(
                "Failed to retrieve file %s from S3: %s",
                key, e.response["Error"]["Message"],
            )
            return None

    def copy_file(self, source_object_name: str, destination_object_name: str) -> bool:
        source_key = self._path(source_object_name)
        dest_key = self._path(destination_object_name)

        copy_source = {"Bucket": self.bucket_name, "Key": source_key}
        try:
            self.client.copy(copy_source, self.bucket_name, dest_key)
            return True
        except ClientError as e:
            logging.error("Failed to copy file {} to {}: {}".format(
                source_key, dest_key, e))
            return False

    def delete_file(self, file_path: str) -> bool:
        try:

            self.client.delete_object(
                Bucket=self.bucket_name, Key=self._path(file_path))
            return True
        except ClientError as e:
            logging.error(f"Failed to delete file from S3: {e}")
            return False

    def file_exists(self, key: str) -> bool:
        try:

            self.client.head_object(
                Bucket=self.bucket_name, Key=self._path(key))
            return True
        except self.client.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    def get_file_size(self, key: str) -> int:
        if not self.file_exists(key):
            return 0

        try:
            response = self.client.head_object(
                Bucket=self.bucket_name, Key=self._path(key))
            return response["ContentLength"]
        except self.client.exceptions.ClientError:
            raise

    def get_file_path(self, object_name: str):
        key = self._path(object_name)
        if self.file_exists(object_name):
            return f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
        return None

    def get_file_url(self, object_name: str) -> Optional[str]:
        try:
            encoded_name = urllib.parse.quote(self._path(object_name))
            return f"https://{self.bucket_name}.s3.amazonaws.com/{encoded_name}"

        except Exception as e:
            logging.error(f"Failed to generate URL for {object_name}: {e}")
            return None

    def get_file_content(self, object_name: str) -> Optional[bytes]:
        key = self._path(object_name)
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()
        except ClientError as e:
            logging.error("Failed to fetch file %s: %s", key,
                          e.response["Error"]["Message"])
            return None

    def upload_file(self, file_path: str, object_name: str) -> bool:
        key = self._path(object_name)
        try:
            self.client.upload_file(file_path, self.bucket_name, key)
            return True
        except ClientError as e:
            logging.error(f"Failed to upload {file_path} to {key}: {e}")
            return False

    def get_file_extension(self, object_name: str) -> str:
        if '.' not in object_name:
            return 'other'
        ext = object_name.split('.')[-1].lower()
        types = {'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image',
                 'mp4': 'video', 'avi': 'video', 'pdf': 'pdf', 'txt': 'document', 'doc': 'document', 'docx': 'document'}
        return types.get(ext, 'other')

    def upload_fileobj(self, fileobj: BytesIO, object_name: str, content_type: str, acl: Optional[str] = None) -> str:
        key = self._path(object_name)
        try:
            self.client.upload_fileobj(
                fileobj,
                self.bucket_name,
                key,
                ExtraArgs={"ContentType": content_type},
            )
            return f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
        except ClientError as e:
            logging.error("Failed to upload file-like object to %s: %s",
                          key, e.response["Error"]["Message"])
            return "Failed to upload file."

    def get_file_metadata(self, object_name: str):
        key = self._path(object_name)
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name, Key=key)
            metadata = {
                "Size": response["ContentLength"],
                "LastModified": response["LastModified"],
                "ContentType": response["ContentType"],
                "ETag": response["ETag"],
            }
            return metadata
        except ClientError as e:
            logging.error(f"Failed to get metadata for {key}: {e}")
            return None

    def _get_simple_file_type(self, content_type: str) -> str:
        if not content_type:
            return "file"

        content_type = content_type.lower().split('/')[0]

        type_map = {
            'image': 'image',
            'video': 'video',
            'audio': 'audio',
            'text': 'text'
        }

        return type_map.get(content_type, 'file')
