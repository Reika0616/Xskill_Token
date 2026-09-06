#!/usr/bin/env python3

import json
import os
import time
from pathlib import Path

from openai import OpenAI


INPUT_DIR = Path(
    "experiment_assets/optimizer_inputs/finance_tstar"
)

OUTPUT_DIR = Path(
    "experiment_assets/optimizer_outputs/finance_tstar"
)

EXECUTORS = ["A", "B", "C"]

TEMPERATURE = 0.1
MAX_TOKENS = 12000
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

    # OpenAI-compatible SDK expects the BASE URL here,
    # e.g. https://api.uniapi.io/v1
    base_url = base_url.rstrip("/")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 80)
    print("Cost-aware diagnosis")
    print("=" * 80)
    print("Optimizer model:", model)
    print("Base URL:", base_url)
    print("Temperature:", TEMPERATURE)
    print("Max tokens:", MAX_TOKENS)
    print()

    for executor in EXECUTORS:
        input_path = (
            INPUT_DIR
            / f"diagnosis_{executor}_input.md"
        )

        output_path = (
            OUTPUT_DIR
            / f"diagnosis_{executor}_v1.md"
        )

        meta_path = (
            OUTPUT_DIR
            / f"diagnosis_{executor}_v1.meta.json"
        )

        if not input_path.exists():
            raise FileNotFoundError(input_path)

        prompt = input_path.read_text(
            encoding="utf-8"
        )

        print("=" * 80)
        print(f"Executor {executor}")
        print("=" * 80)
        print(
            f"Input characters: {len(prompt):,}"
        )

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

                response = (
                    client.chat.completions.create(
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
                )

                break

            except Exception as e:
                last_error = repr(e)

                print(
                    f"[ERROR] Executor {executor}: "
                    f"{last_error}"
                )

                if attempt < MAX_RETRIES:
                    time.sleep(3 * attempt)

        if response is None:
            raise RuntimeError(
                f"Executor {executor} failed "
                f"after {MAX_RETRIES} attempts: "
                f"{last_error}"
            )

        if (
            not response.choices
            or not response.choices[0].message
        ):
            raise RuntimeError(
                f"Executor {executor}: "
                "optimizer returned no usable message."
            )

        content = (
            response.choices[0]
            .message
            .content
            or ""
        )

        output_path.write_text(
            content,
            encoding="utf-8",
        )

        usage = getattr(
            response,
            "usage",
            None,
        )

        usage_dict = {}

        if usage is not None:
            # pydantic models in recent OpenAI SDKs
            if hasattr(usage, "model_dump"):
                usage_dict = usage.model_dump()
            else:
                usage_dict = {
                    "prompt_tokens": getattr(
                        usage,
                        "prompt_tokens",
                        None,
                    ),
                    "completion_tokens": getattr(
                        usage,
                        "completion_tokens",
                        None,
                    ),
                    "total_tokens": getattr(
                        usage,
                        "total_tokens",
                        None,
                    ),
                }

        meta = {
            "executor_id": executor,
            "optimizer_model": model,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "input_path": str(input_path),
            "output_path": str(output_path),
            "input_characters": len(prompt),
            "output_characters": len(content),
            "usage": usage_dict,
        }

        meta_path.write_text(
            json.dumps(
                meta,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            f"Saved diagnosis -> {output_path}"
        )
        print(
            f"Output characters: {len(content):,}"
        )

        if usage_dict:
            print("Usage:", usage_dict)

        print()

    print("=" * 80)
    print("All three diagnoses completed.")
    print("=" * 80)


if __name__ == "__main__":
    main()
