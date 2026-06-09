"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_TO_PULL = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = "prompts/bug_to_user_story_v1.yml"


def extract_messages_from_prompt(prompt) -> dict:
    """
    Extrai system_prompt e user_prompt de um ChatPromptTemplate retornado pelo Hub.

    Args:
        prompt: Objeto retornado por hub.pull (geralmente ChatPromptTemplate)

    Returns:
        Dicionário com os campos serializados do prompt
    """
    system_prompt = ""
    user_prompt = ""

    messages = getattr(prompt, "messages", None)

    if messages:
        for message in messages:
            template = ""
            inner = getattr(message, "prompt", None)
            if inner is not None and hasattr(inner, "template"):
                template = inner.template
            elif hasattr(message, "content"):
                template = message.content

            message_type = message.__class__.__name__.lower()

            if "system" in message_type:
                system_prompt = template
            elif "human" in message_type or "user" in message_type:
                user_prompt = template
            elif not system_prompt:
                system_prompt = template
    elif hasattr(prompt, "template"):
        system_prompt = prompt.template

    return {
        "bug_to_user_story_v1": {
            "description": "Prompt de baixa qualidade puxado do LangSmith Hub para servir de base de otimização.",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": "v1",
            "source": PROMPT_TO_PULL,
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }


def pull_prompts_from_langsmith() -> bool:
    """
    Faz pull do prompt inicial do LangSmith Hub e salva localmente em YAML.

    Returns:
        True se sucesso, False caso contrário
    """
    print(f"Puxando prompt do LangSmith Hub: {PROMPT_TO_PULL}")

    try:
        prompt = hub.pull(PROMPT_TO_PULL)
        print("   \u2713 Prompt carregado com sucesso")

        prompt_data = extract_messages_from_prompt(prompt)

        if save_yaml(prompt_data, OUTPUT_PATH):
            print(f"   \u2713 Prompt salvo localmente em: {OUTPUT_PATH}")
            return True

        print("   \u274c Falha ao salvar o prompt localmente")
        return False

    except Exception as e:
        print(f"\n\u274c Erro ao puxar o prompt '{PROMPT_TO_PULL}': {e}")
        print("\nVerifique:")
        print("- LANGSMITH_API_KEY est\u00e1 configurada corretamente no .env")
        print("- Voc\u00ea possui conex\u00e3o com a internet")
        print(f"- O prompt '{PROMPT_TO_PULL}' existe e est\u00e1 p\u00fablico no Hub")
        return False


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    Path("prompts").mkdir(parents=True, exist_ok=True)

    if pull_prompts_from_langsmith():
        print("\n\u2705 Pull conclu\u00eddo com sucesso.")
        print("\nPr\u00f3ximos passos:")
        print("1. Analise o prompt em prompts/bug_to_user_story_v1.yml")
        print("2. Otimize criando prompts/bug_to_user_story_v2.yml")
        print("3. Fa\u00e7a push: python src/push_prompts.py")
        return 0

    print("\n\u274c Pull n\u00e3o foi conclu\u00eddo. Revise as mensagens acima.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
