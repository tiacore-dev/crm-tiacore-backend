import io
import re
from loguru import logger
import aioboto3
from botocore.exceptions import ClientError
from app.config import Settings

settings = Settings()


class AsyncS3Manager:
    endpoint_url = settings.ENDPOINT_URL
    region_name = settings.REGION_NAME
    aws_access_key_id = settings.AWS_ACCESS_KEY_ID
    aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
    bucket_name = settings.BUCKET_NAME
    bucket_folder = "crm"

    def _get_session(self):
        return aioboto3.Session()

    def _build_path(self, company_id: int, filename: str, entity: str) -> str:
        return f"{self.bucket_folder}/{entity}/{company_id}/{filename}"

    async def upload_bytes(self, file_bytes: bytes, company_id: str, filename: str, entity: str):
        # 🔧 Нормализуем имя файла
        normalized_filename = self._normalize_filename(filename)
        key = self._build_path(company_id, normalized_filename, entity)

        session = self._get_session()
        async with session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3:
            try:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=io.BytesIO(file_bytes),
                    ACL="private",
                    ContentLength=len(file_bytes),
                    Metadata={"x-amz-content-sha256": "UNSIGNED-PAYLOAD"},
                )

                logger.info(f"✅ Файл загружен: {key}")
                return key
            except ClientError as e:
                logger.error(f"Ошибка загрузки: {e}")
                raise

    def _normalize_filename(self, filename: str) -> str:
        # Убираем опасные символы, заменяем пробелы и двойные точки
        filename = filename.strip()
        filename = filename.replace(" ", "_")
        # можно строже, если нужно
        filename = re.sub(r"[^\w.\-]", "", filename)
        return filename

    async def generate_presigned_url(self, key, expiration=3600):
        session = self._get_session()
        async with session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3:
            try:
                return await s3.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={"Bucket": self.bucket_name, "Key": key},
                    ExpiresIn=expiration
                )
            except ClientError as e:
                logger.error(f"Ошибка при генерации ссылки: {e}")
                return None

    # async def list_user_files(self, company_id: int) -> list[str]:
    #     prefix = f"{self.bucket_folder}/{company_id}/"
    #     session = self._get_session()
    #     async with session.client(
    #         "s3",
    #         endpoint_url=self.endpoint_url,
    #         region_name=self.region_name,
    #         aws_access_key_id=self.aws_access_key_id,
    #         aws_secret_access_key=self.aws_secret_access_key,
    #     ) as s3:
    #         try:
    #             response = await s3.list_objects_v2(
    #                 Bucket=self.bucket_name,
    #                 Prefix=prefix
    #             )
    #             return [obj["Key"] for obj in response.get("Contents", [])]
    #         except ClientError as e:
    #             logger.error(f"Ошибка при получении списка файлов: {e}")
    #             return []

    async def delete_file(self, key):
        session = self._get_session()
        async with session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3:
            try:
                await s3.delete_object(Bucket=self.bucket_name, Key=key)
                logger.info(f"🗑️ Файл удалён: {key}")
            except ClientError as e:
                logger.error(f"Ошибка при удалении файла: {e}")
                raise

    # async def file_exists(self, company_id: int, filename: str) -> bool:
    #     key = self._build_path(company_id, filename)
    #     session = self._get_session()
    #     async with session.client(
    #         "s3",
    #         endpoint_url=self.endpoint_url,
    #         region_name=self.region_name,
    #         aws_access_key_id=self.aws_access_key_id,
    #         aws_secret_access_key=self.aws_secret_access_key,
    #     ) as s3:
    #         try:
    #             await s3.head_object(Bucket=self.bucket_name, Key=key)
    #             return True
    #         except ClientError as e:
    #             if e.response["Error"]["Code"] == "404":
    #                 return False
    #             logger.error(f"Ошибка при проверке существования файла: {e}")
    #             raise

    async def download_bytes(self, s3_key: str) -> bytes:
        session = self._get_session()
        async with session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        ) as s3:
            try:
                response = await s3.get_object(Bucket=self.bucket_name, Key=s3_key)
                file_bytes = await response["Body"].read()
                logger.info(
                    f"📥 Файл загружен с S3: {s3_key}, размер: {len(file_bytes)} байт")
                return file_bytes
            except ClientError as e:
                logger.error(f"❌ Ошибка при загрузке файла: {e}")
                raise
