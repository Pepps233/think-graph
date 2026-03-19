from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = Field("", alias="NEXT_PUBLIC_SUPABASE_URL")
    supabase_anon_key: str = Field("", alias="NEXT_PUBLIC_SUPABASE_ANON_KEY")
    supabase_service_role_key: str = ""

    # R2
    r2_account_id: str = ""
    r2_s3_endpoint: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "thinkgraph-papers"

    # Redis / Celery
    celery_broker_url: str = ""

    @property
    def celery_broker_url_with_ssl(self) -> str:
        """Append ssl_cert_reqs=CERT_NONE for Upstash rediss:// URLs."""
        url = self.celery_broker_url
        if url.startswith("rediss://") and "ssl_cert_reqs" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}ssl_cert_reqs=CERT_NONE"
        return url
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    # OpenAI
    openai_api_key: str = ""

    model_config = {
        "env_file": "../.env",
        "extra": "ignore",
        "populate_by_name": True,
    }


settings = Settings()
