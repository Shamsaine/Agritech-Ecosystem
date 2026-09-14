from app.imports.identifiers import deterministic_id


def test_deterministic_id_is_stable():
    first = deterministic_id("application", "APP-0001")
    second = deterministic_id("application", "APP-0001")

    assert first == second


def test_entity_types_produce_different_ids():
    application_id = deterministic_id("application", "APP-0001")
    organisation_id = deterministic_id("organisation", "APP-0001")

    assert application_id != organisation_id
