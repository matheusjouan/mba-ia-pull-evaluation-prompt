"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_FILE = "prompts/bug_to_user_story_v2.yml"
PROMPT_BASENAME = "bug_to_user_story_v2"


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    return validate_prompt_structure(prompt_data)


def build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """
    Constrói um ChatPromptTemplate a partir dos dados do YAML.

    Usa System Prompt para instruções/persona/exemplos e User Prompt para a
    entrada dinâmica ({bug_report}).
    """
    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data.get("user_prompt", "{bug_report}")

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt (ex.: "username/bug_to_user_story_v2")
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    print(f"\nFazendo push do prompt: {prompt_name}")

    try:
        chat_prompt = build_chat_prompt(prompt_data)

        techniques = prompt_data.get("techniques_applied", [])
        description = prompt_data.get("description", "")
        tags = prompt_data.get("tags", [])

        readme = (
            f"# {PROMPT_BASENAME}\n\n"
            f"{description}\n\n"
            f"## Técnicas Aplicadas\n"
            + "\n".join(f"- {technique}" for technique in techniques)
        )

        commit_url = hub.push(
            prompt_name,
            chat_prompt,
            new_repo_is_public=True,
            new_repo_description=description,
            readme=readme,
            tags=tags,
        )

        print("   \u2713 Push realizado com sucesso (prompt PÚBLICO)")
        print(f"   \u2713 Commit: {commit_url}")
        print(f"   \u2713 Técnicas registradas: {', '.join(techniques)}")
        return True

    except Exception as e:
        print(f"   \u274c Erro ao fazer push do prompt: {e}")
        print("\nVerifique:")
        print("- LANGSMITH_API_KEY est\u00e1 configurada corretamente no .env")
        print("- USERNAME_LANGSMITH_HUB corresponde ao seu handle do Hub")
        print("- Voc\u00ea possui conex\u00e3o com a internet")
        return False


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS PARA O LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()

    print(f"Lendo prompt otimizado de: {PROMPT_FILE}")
    prompt_data = load_yaml(PROMPT_FILE)

    if not prompt_data:
        print(f"\u274c N\u00e3o foi poss\u00edvel carregar o arquivo: {PROMPT_FILE}")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("\u274c Prompt inv\u00e1lido. Corrija os erros abaixo antes do push:")
        for error in errors:
            print(f"   - {error}")
        return 1

    print("   \u2713 Prompt validado com sucesso")

    prompt_name = f"{username}/{PROMPT_BASENAME}"

    if push_prompt_to_langsmith(prompt_name, prompt_data):
        print("\n\u2705 Push conclu\u00eddo com sucesso.")
        print("\nPr\u00f3ximos passos:")
        print(f"1. Confirme a publica\u00e7\u00e3o em: https://smith.langchain.com/prompts")
        print("2. Garanta que o prompt esteja P\u00daBLICO")
        print("3. Execute a avalia\u00e7\u00e3o: python src/evaluate.py")
        return 0

    print("\n\u274c Push n\u00e3o foi conclu\u00eddo. Revise as mensagens acima.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
