from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    repr_cols_num: int = 3  # сколько колонок вывести на печать

    # для вывода дополнительных колонок, их названия
    repr_cols: tuple[str, ...] = ()

    def __repr__(self) -> str:
        """Показывает значения нужных полей при печати модели."""
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")
        return f"<{self.__class__.__name__} {','.join(cols)}>"
