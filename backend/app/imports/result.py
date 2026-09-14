from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ImportResult:
    batch_id: str | None = None
    checksum_sha256: str = ""
    total_rows: int = 0
    processed_rows: int = 0
    successful_rows: int = 0
    quarantined_rows: int = 0
    failed_rows: int = 0
    created: dict[str, int] = field(default_factory=dict)
    reused: dict[str, int] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def increment_created(self, entity: str) -> None:
        self.created[entity] = self.created.get(entity, 0) + 1

    def increment_reused(self, entity: str) -> None:
        self.reused[entity] = self.reused.get(entity, 0) + 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
