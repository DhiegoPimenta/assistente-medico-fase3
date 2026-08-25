from app.core.guardrails import (
    VALIDATION_DISCLAIMER,
    apply_guardrail,
    contains_direct_prescription,
    mentions_validation,
)


def test_contains_direct_prescription_true_for_dosage_plus_verb():
    text = "Administrar AAS 200mg mastigável imediatamente."
    assert contains_direct_prescription(text) is True


def test_contains_direct_prescription_false_without_verb():
    text = "A dose usual descrita no protocolo é de 200mg."
    assert contains_direct_prescription(text) is False


def test_contains_direct_prescription_false_without_dosage():
    text = "Administrar o medicamento conforme avaliação clínica."
    assert contains_direct_prescription(text) is False


def test_mentions_validation_detects_common_phrasings():
    assert mentions_validation("sujeito a validação médica") is True
    assert mentions_validation("depende do médico responsável") is True
    assert mentions_validation("conduta sugerida sem ressalvas") is False


def test_apply_guardrail_appends_disclaimer_when_missing():
    text = "Administrar AAS 200mg mastigável."
    result = apply_guardrail(text)
    assert result.triggered is True
    assert VALIDATION_DISCLAIMER.strip() in result.text
    assert text in result.text


def test_apply_guardrail_leaves_text_untouched_when_already_validated():
    text = (
        "Administrar AAS 200mg mastigável, mediante validação médica formal "
        "por um médico responsável."
    )
    result = apply_guardrail(text)
    assert result.text == text
    assert result.triggered is True  # ainda sinaliza: tinha padrão de prescrição direta
    assert result.reason is not None


def test_apply_guardrail_triggers_even_without_dosage_if_no_validation_mentioned():
    text = "O paciente deve manter repouso relativo pelos próximos dias."
    result = apply_guardrail(text)
    assert result.triggered is True
    assert VALIDATION_DISCLAIMER.strip() in result.text


def test_apply_guardrail_does_not_duplicate_disclaimer():
    text = "Alguma resposta." + VALIDATION_DISCLAIMER
    result = apply_guardrail(text)
    assert result.text.count(VALIDATION_DISCLAIMER.strip()) == 1
