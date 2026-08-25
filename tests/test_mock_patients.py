from app.core.mock_patients import get_patient


def test_get_patient_returns_known_patient():
    patient = get_patient("SIM-0001")
    assert patient is not None
    assert patient["exame_pendente"] is True


def test_get_patient_returns_none_for_unknown_id():
    assert get_patient("SIM-9999") is None
