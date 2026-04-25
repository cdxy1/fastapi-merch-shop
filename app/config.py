import os


class PostgresConfig:
    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST")
        self.port = os.getenv("POSTGRES_PORT")
        self.user = os.getenv("POSTGRES_USER")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.database = os.getenv("POSTGRES_DB")

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisConfig:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST")
        self.port = os.getenv("REDIS_PORT")

    @property
    def connection_string(self) -> str:
        return f"redis://{self.host}:{self.port}"

class SecurityConfig:
    def __init__(self):
        self.jwt_secret_key = os.getenv("SECRET_KEY")
        self.jwt_algorithm = os.getenv("ALGORITHM")
        self.jwt_expiration_seconds = int(os.getenv("EXPIRATION_SECONDS", "3600"))
        

class Config:
    def __init__(self):
        self.postgres = PostgresConfig()
        self.redis = RedisConfig()
        self.security = SecurityConfig()
        
config = Config()
