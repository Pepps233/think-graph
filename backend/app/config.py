from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # R2
    r2_account_id: str = ""
    r2_s3_endpoint: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "thinkgraph-papers"

    # Redis / Celery
    celery_broker_url: str = ""
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    # OpenAI
    openai_api_key: str = ""

    class Config:
        env_file = "../.env"
        extra = "ignore"


settings = Settings()
