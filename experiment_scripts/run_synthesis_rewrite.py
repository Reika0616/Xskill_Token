#!/usr/bin/env python3

import json
import os
import re
import time
from pathlib import Path

from openai import OpenAI


INPUT_PATH = Path(
    "experiment_assets/optimizer_inputs/finance_tstar/synthesis_v1_input.md"
)

OUTPUT_DIR = Path(
    "experiment_assets/optimizer_outputs/finance_tstar"
)

FULL_OUTPUT_PATH = OUTPUT_DIR / "synthesis_v1.md"
SKILL_OUTPUT_PATH = OUTPUT_DIR / "S1_v1.md"
META_OUTPUT_PATH = OUTPUT_DIR / "synthesis_v1.meta.json"

TEMPERATURE = 0.1
MAX_TOKENS = 16000
MAX_RETRIES = 3


def main():

    model = os.environ.get("OPTIMIZER_MODEL_NAME")
    api_key = os.environ.get("OPTIMIZER_API_KEY")
    base_url = os.environ.get("OPTIMIZER_BASE_URL")

    if not model:
        raise RuntimeError(
            "OPTIMIZER_MODEL_NAME is not set."
        )

    if not api_key:
        raise RuntimeError(
            "OPTIMIZER_API_KEY is not set."
        )

    if not base_url:
        raise RuntimeError(
            "OPTIMIZER_BASE_URL is not set."
        )

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Synthesis input not found: {INPUT_PATH}\n"
            "Run build_synthesis_input.py first."
        )

    # OpenAI SDK expects the API base URL here, e.g.
    # https://api.uniapi.io/v1
    # NOT .../v1/chat/completions
    base_url = base_url.rstrip("/")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    prompt = INPUT_PATH.read_text(
        encoding="utf-8"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 80)
    print("Synthesis + Skill Rewrite v1")
    print("=" * 80)
    print("Optimizer model:", model)
    print("Base URL:", base_url)
    print("Temperature:", TEMPERATURE)
    print("Max tokens:", MAX_TOKENS)
    print("Input characters:", f"{len(prompt):,}")
    print()

    response = None
    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):
        try:

            print(
                f"Calling optimizer "
                f"(attempt {attempt}/{MAX_RETRIES})..."
            )

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )

            break

        except Exception as e:

            last_error = repr(e)

            print(
                f"[ERROR] {last_error}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(3 * attempt)

    if response is None:
        raise RuntimeError(
            f"Synthesis failed after "
            f"{MAX_RETRIES} attempts: "
            f"{last_error}"
        )

    if (
        not response.choices
        or not response.choices[0].message
    ):
        raise RuntimeError(
            "Optimizer returned no usable message."
        )

    content = (
        response.choices[0].message.content
        or ""
    )

    # Save the complete synthesis report.
    FULL_OUTPUT_PATH.write_text(
        content,
        encoding="utf-8",
    )

    # Extract only the rewritten Skill.
    match = re.search(
        r"<REVISED_SKILL>\s*(.*?)\s*</REVISED_SKILL>",
        content,
        flags=re.DOTALL,
    )

    if not match:
        raise RuntimeError(
            "Could not find "
            "<REVISED_SKILL>...</REVISED_SKILL> "
            "in optimizer output.\n"
            f"The full response was still saved to: "
            f"{FULL_OUTPUT_PATH}"
        )

    revised_skill = match.group(1).strip()

    SKILL_OUTPUT_PATH.write_text(
        revised_skill + "\n",
        encoding="utf-8",
    )

    usage = getattr(
        response,
        "usage",
        None,
    )

    if (
        usage is not None
        and hasattr(usage, "model_dump")
    ):
        usage_dict = usage.model_dump()

    else:
        usage_dict = {
            "prompt_tokens": (
                getattr(
                    usage,
                    "prompt_tokens",
                    None,
                )
                if usage
                else None
            ),
            "completion_tokens": (
                getattr(
                    usage,
                    "completion_tokens",
                    None,
                )
                if usage
                else None
            ),
            "total_tokens": (
                getattr(
                    usage,
                    "total_tokens",
                    None,
                )
                if usage
                else None
            ),
        }

    meta = {
        "optimizer_model": model,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "input_path": str(INPUT_PATH),
        "full_output_path": str(
            FULL_OUTPUT_PATH
        ),
        "skill_output_path": str(
            SKILL_OUTPUT_PATH
        ),
        "input_characters": len(prompt),
        "output_characters": len(content),
        "skill_characters": len(
            revised_skill
        ),
        "usage": usage_dict,
    }

    META_OUTPUT_PATH.write_text(
        json.dumps(
            meta,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("Synthesis completed.")
    print()
    print("Full synthesis:")
    print(FULL_OUTPUT_PATH)
    print()
    print("Revised Skill:")
    print(SKILL_OUTPUT_PATH)
    print()
    print(
        "Revised Skill characters:",
        f"{len(revised_skill):,}",
    )

    if usage_dict:
        print()
        print("Optimizer usage:")
        print(
            json.dumps(
                usage_dict,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
