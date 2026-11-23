"""声明式基类。

调用时机：模型定义与 Alembic 自动生成迁移时引用同一份 metadata。
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
