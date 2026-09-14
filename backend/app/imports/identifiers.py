import uuid


IMPORT_NAMESPACE = uuid.UUID("eea55220-e67a-4d92-bbe5-983ac9c69010")


def deterministic_id(entity_type: str, source_id: str) -> uuid.UUID:
    value = f"{entity_type}:{source_id.strip()}"
    return uuid.uuid5(IMPORT_NAMESPACE, value)
