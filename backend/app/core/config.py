"""应用配置。

调用时机：进程启动后首次调用 get_settings 时读取环境变量与 .env，并缓存结果。
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """运行期配置，全部可用 NWBD_SKILLS_ 前缀的环境变量覆盖。"""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="NWBD_SKILLS_", extra="ignore")

    database_url: str = "postgresql+psycopg://skills:skills@127.0.0.1:5432/skills"
    jwt_secret: str = "dev-secret-change-me"
    token_ttl_minutes: int = 720
    data_dir: Path = Path("./data")

    # 包校验限制
    max_package_bytes: int = 50 * 1024 * 1024
    max_file_bytes: int = 10 * 1024 * 1024
    max_entries: int = 500
    max_compression_ratio: int = 100

    # 单文件预览上限，超过则拒绝预览而不是截断
    max_text_preview_bytes: int = 1024 * 1024

    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = "admin12345"

    cors_origins: str = ""

    # 钉钉扫码登录（企业内部应用）
    dingtalk_client_id: str = ""
    dingtalk_client_secret: str = ""
    dingtalk_redirect_uri: str = ""
    dingtalk_api_base: str = "https://api.dingtalk.com"
    dingtalk_oapi_base: str = "https://oapi.dingtalk.com"
    # 额外的管理员：逗号分隔，可填钉钉 userId、unionId 或显示名（如「汪卫平」）
    dingtalk_extra_admins: str = ""

    @property
    def dingtalk_enabled(self) -> bool:
        """三项凭据齐备才启用扫码登录。"""
        return bool(self.dingtalk_client_id and self.dingtalk_client_secret and self.dingtalk_redirect_uri)

    @property
    def packages_dir(self) -> Path:
        """原始包的存放目录，文件名即内容摘要。"""
        return self.data_dir / "packages"

    @property
    def extracted_dir(self) -> Path:
        """解压副本目录，用于文件树与预览。"""
        return self.data_dir / "extracted"

    def ensure_dirs(self) -> None:
        """调用时机：应用启动时创建数据目录，已存在则跳过。"""
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """返回缓存的配置单例。"""
    return Settings()
