"""Bar + Dataset models (Data Contract: dataset_id, symbol, timeframe, time range, timezone, source, hash, quality)."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Bar:
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    extras: dict = field(default_factory=dict)


@dataclass
class Dataset:
    dataset_id: str
    symbol: str
    timeframe: str
    bars: list
    timezone: str = "UTC"
    source: str = "csv"
    schema_version: str = "1.0"
    content_hash: str = ""
    fields: set = field(default_factory=set)
    quality_status: str = "UNKNOWN"
    quality: dict = field(default_factory=dict)

    def meta(self):
        return {"dataset_id": self.dataset_id, "symbol": self.symbol, "timeframe": self.timeframe,
                "start_time": self.bars[0].ts if self.bars else "", "end_time": self.bars[-1].ts if self.bars else "",
                "timezone": self.timezone, "source": self.source, "schema_version": self.schema_version,
                "content_hash": self.content_hash, "quality_status": self.quality_status}

    def slice(self, start, end, suffix):
        return Dataset(f"{self.dataset_id}:{suffix}", self.symbol, self.timeframe, self.bars[start:end],
                       self.timezone, self.source, self.schema_version, self.content_hash,
                       set(self.fields), self.quality_status, dict(self.quality))
