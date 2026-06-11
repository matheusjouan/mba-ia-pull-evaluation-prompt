"""
Diagnostic helper (read-only): generates the User Stories produced by the LOCAL
optimized prompt for every example in the dataset and writes them next to the
expected reference, so the prompt can be debugged precisely.

This script DOES NOT:
- modify the dataset
- push anything to LangSmith
- call the evaluator LLM
- change any of the "ready" files

It only reads prompts/bug_to_user_story_v2.yml + datasets/bug_to_user_story.jsonl,
runs the responder model (gpt-4o-mini) and saves outputs_debug.txt locally.
"""

import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, get_llm

load_dotenv()

PROMPT_FILE = "prompts/bug_to_user_story_v2.yml"
DATASET_FILE = "datasets/bug_to_user_story.jsonl"
OUTPUT_FILE = "outputs_debug.txt"


def build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """Builds the same ChatPromptTemplate used when pushing the prompt."""
    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data.get("user_prompt", "{bug_report}")

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )


def load_dataset(jsonl_path: str) -> list:
    examples = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def main() -> int:
    prompt_data = load_yaml(PROMPT_FILE)
    if not prompt_data:
        print(f"Could not load prompt file: {PROMPT_FILE}")
        return 1

    if not Path(DATASET_FILE).exists():
        print(f"Dataset not found: {DATASET_FILE}")
        return 1

    chat_prompt = build_chat_prompt(prompt_data)
    llm = get_llm(temperature=0)
    chain = chat_prompt | llm

    examples = load_dataset(DATASET_FILE)
    print(f"Generating outputs for {len(examples)} examples...")

    lines = []
    for i, example in enumerate(examples, 1):
        bug_report = example["inputs"]["bug_report"]
        reference = example["outputs"]["reference"]
        complexity = example.get("metadata", {}).get("complexity", "n/a")

        try:
            response = chain.invoke({"bug_report": bug_report})
            generated = response.content
        except Exception as e:
            generated = f"[ERROR generating output: {e}]"

        print(f"   [{i}/{len(examples)}] complexity={complexity} done")

        lines.append("=" * 80)
        lines.append(f"EXAMPLE {i}/{len(examples)} | complexity: {complexity}")
        lines.append("=" * 80)
        lines.append("\n--- BUG REPORT ---")
        lines.append(bug_report)
        lines.append("\n--- GENERATED (gpt-4o-mini) ---")
        lines.append(generated)
        lines.append("\n--- EXPECTED REFERENCE ---")
        lines.append(reference)
        lines.append("\n")

    Path(OUTPUT_FILE).write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSaved {OUTPUT_FILE} ({len(examples)} examples).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
