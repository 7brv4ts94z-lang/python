from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    data_path: Path = Path("data/sales_raw.csv")
    output_dir: Path = Path("output")
    title: str = "일일 매출 리포트"
    top_n: int = 10


CONFIG = Config()