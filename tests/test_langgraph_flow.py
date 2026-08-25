from app.core.langgraph_flow import (
    classify_intent,
    route_after_classify,
    route_after_dynamic_rag,
)


def test_classify_intent_uses_explicit_patient_id():
    state = {"question": "Alguma pergunta genérica", "patient_id": "SIM-0001"}
    assert classify_intent(state) == {"intent": "paciente"}


def test_classify_intent_detects_patient_keyword_without_id():
    state = {"question": "O que o paciente tem?", "patient_id": None}
    assert classify_intent(state) == {"intent": "paciente"}


def test_classify_intent_defaults_to_geral():
    state = {"question": "Qual o protocolo de sepse?", "patient_id": None}
    assert classify_intent(state) == {"intent": "geral"}


def test_route_after_classify_matches_intent():
    assert route_after_classify({"intent": "geral"}) == "static_rag"
    assert route_after_classify({"intent": "paciente"}) == "dynamic_rag"


def test_route_after_dynamic_rag_goes_to_guardrail_when_patient_not_found():
    state = {"patient_summary": None}
    assert route_after_dynamic_rag(state) == "guardrail"


def test_route_after_dynamic_rag_emits_alert_when_exam_pending():
    state = {"patient_summary": "resumo", "exame_pendente": True}
    assert route_after_dynamic_rag(state) == "emit_alert"


def test_route_after_dynamic_rag_suggests_conduct_when_no_exam_pending():
    state = {"patient_summary": "resumo", "exame_pendente": False}
    assert route_after_dynamic_rag(state) == "suggest_conduct"
