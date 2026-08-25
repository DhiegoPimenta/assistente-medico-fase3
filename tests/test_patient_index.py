from app.core import ingestion, patient_index


def test_get_patient_returns_demo_patient():
    patient = patient_index.get_patient("SIM-0001")
    assert patient is not None
    assert patient["exame_pendente"] is True


def test_get_patient_returns_none_for_unknown_id():
    assert patient_index.get_patient("SIM-9999") is None


def test_register_and_retrieve_uploaded_patient(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion, "DYNAMIC_STORE_DIR", tmp_path / "dynamic")

    patient_index.register_patient(
        patient_id="UP-0001",
        nome="Paciente Enviado via Upload",
        prontuario="Paciente com dor abdominal em quadrante inferior direito.",
        exame_pendente=True,
        exame_pendente_desc="Tomografia de abdome solicitada.",
    )

    patient = patient_index.get_patient("UP-0001")
    assert patient is not None
    assert patient["nome"] == "Paciente Enviado via Upload"
    assert patient["exame_pendente"] is True
    assert patient["exame_pendente_desc"] == "Tomografia de abdome solicitada."
    assert "dor abdominal" in patient["prontuario"]


def test_demo_patient_takes_precedence_over_dynamic_store(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion, "DYNAMIC_STORE_DIR", tmp_path / "dynamic")
    # mesmo que alguém registre um prontuário com o id de um paciente demo,
    # o paciente demo (fixo, usado nos testes/vídeo) deve prevalecer
    patient_index.register_patient(
        patient_id="SIM-0001",
        nome="Duplicata",
        prontuario="Não deveria aparecer",
        exame_pendente=False,
    )
    patient = patient_index.get_patient("SIM-0001")
    assert patient["nome"] == "Paciente Simulado 1"
