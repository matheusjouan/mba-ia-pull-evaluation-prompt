"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_V2_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_v2():
    """Carrega o prompt otimizado v2."""
    return load_prompts(str(PROMPT_V2_PATH))


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_v2):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_v2, "Campo 'system_prompt' não encontrado no YAML"
        system_prompt = prompt_v2["system_prompt"]
        assert isinstance(system_prompt, str)
        assert system_prompt.strip(), "'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, prompt_v2):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt_v2.get("system_prompt", "")
        assert re.search(r"voc[êe]\s+[ée]\s+(um|uma)\b", system_prompt, re.IGNORECASE), \
            "O prompt não define uma persona (ex.: 'Você é um Product Manager')"

    def test_prompt_mentions_format(self, prompt_v2):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        full_text = " ".join(
            str(prompt_v2.get(field, ""))
            for field in ("system_prompt", "user_prompt")
        ).lower()
        assert (
            "markdown" in full_text
            or "user story" in full_text
            or "critérios de aceitação" in full_text
            or "como um" in full_text
        ), "O prompt não menciona formato Markdown ou padrão de User Story"

    def test_prompt_has_few_shot_examples(self, prompt_v2):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_v2.get("system_prompt", "").lower()
        assert system_prompt.count("exemplo") >= 2, \
            "O prompt deve conter ao menos 2 exemplos (Few-shot)"
        assert system_prompt.count("como um") >= 2, \
            "Os exemplos Few-shot devem demonstrar saídas no formato de User Story"

    def test_prompt_no_todos(self, prompt_v2):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        full_text = " ".join(str(value) for value in prompt_v2.values())
        assert "[TODO]" not in full_text, "Há um [TODO] pendente no prompt"
        assert "TODO" not in full_text, "Há um TODO pendente no prompt"

    def test_minimum_techniques(self, prompt_v2):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_v2.get("techniques_applied", [])
        assert isinstance(techniques, list), "'techniques_applied' deve ser uma lista"
        assert len(techniques) >= 2, \
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}"

    def test_prompt_structure_is_valid(self, prompt_v2):
        """Valida a estrutura completa do prompt via utilitário compartilhado."""
        is_valid, errors = validate_prompt_structure(prompt_v2)
        assert is_valid, f"Estrutura do prompt inválida: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
