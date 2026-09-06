#!/usr/bin/env python3

"""
Generate the frozen initial Skill S0 from an already-prepared
category-specific VisualToolBench split.

Example:

    python experiment_scripts/generate_initial_skill.py \
        --category finance

The optimizer model is configured through .env:

    OPTIMIZER_MODEL=...
    OPTIMIZER_API_MODE=responses

The script supports both Responses and Chat Completions so that
the optimizer model is not coupled to one API interface.
"""

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# Paths
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent


# ============================================================
# Initial Skill prompt
# ============================================================

SKILL_INSTRUCTIONS = """
You are constructing an INITIAL category-specific Skill for a multimodal
tool-using agent on VisualToolBench.

This Skill will serve as a neutral baseline for later experiments.

You are given representative tasks from one VisualToolBench category,
together with their golden answers.

Your goal is NOT to memorize, reproduce, or solve these particular
examples.

Instead, infer reusable procedural guidance and task-solving patterns
that would help an agent solve NEW unseen tasks from the same category.

The execution environment may provide these tools:

- zoom:
  Inspect or enlarge relevant regions of an image.

- code_interpreter:
  Perform computation, numerical reasoning, programmatic image analysis,
  or other analysis better handled with code.

- web_search:
  Search for external information on the web.

- visit:
  Open and inspect web pages or search results.

- image_search:
  Search for external visual references when useful.


Construct ONE reusable Markdown Skill document.


The Skill should provide practical guidance for:

1. understanding the task and identifying the evidence required;
2. inspecting and localizing relevant visual information;
3. deciding when different tools are appropriate;
4. extracting textual, numerical, spatial, or semantic information;
5. performing computation when needed;
6. retrieving external information when needed;
7. combining visual, computational, and external evidence;
8. validating important intermediate and final conclusions;
9. producing the requested final answer.


IMPORTANT CONSTRAINTS:

- Do NOT mention specific examples supplied below.

- Do NOT reproduce example-specific answers, companies, people,
  numbers, locations, dates, or other instance-specific details.

- The Skill should generalize to unseen tasks from the same category.

- Do NOT assume every task requires every tool.

- Do NOT prescribe one rigid tool sequence for all tasks.

- Tool use should be conditional on the task and available evidence.

- Do NOT discuss this research experiment.

- Do NOT optimize the Skill for token usage, execution cost, latency,
  or number of tool calls.

- Do NOT instruct the agent to minimize reasoning or verification.

- The objective of this INITIAL Skill is normal task performance,
  correctness, and reliability.

Prefer concrete, actionable procedural rules over long explanatory prose.

The document should be detailed enough to guide agent behavior, but
should not become an encyclopedic description of every possible task.


A suitable structure is:

# <Skill Name>

## Description

## When to Use

## Strategy Overview

## Workflow

### 1. Understand the Task and Evidence Requirements

### 2. Inspect and Localize Visual Evidence

### 3. Select and Use Tools

### 4. Integrate Evidence

### 5. Validate the Result

### 6. Produce the Final Answer

## Tool Guidance

### zoom

### code_interpreter

### web_search and visit

### image_search

## Common Failure Modes / Watch Outs

## Output Principles


Return ONLY the final Markdown Skill document.

Do not wrap it inside a Markdown code fence.
""".strip()


# ============================================================
# Helpers
# ============================================================

def clean_problem(text):
    return str(text).replace("<image>", "").strip()


def format_examples(samples, category):
    blocks = []

    for i, sample in enumerate(samples, 1):
        problem = clean_problem(sample.get("problem", ""))
        answer = str(sample.get("solution", "")).strip()

        block = f"""
============================================================
EXAMPLE {i}
============================================================

Category:
{category}

Task:
{problem}

Golden Answer:
{answer}
""".strip()

        blocks.append(block)

    return "\n\n".join(blocks)


def strip_markdown_fence(text):
    text = text.strip()

    match = re.match(
        r"^```(?:markdown|md)?\s*(.*?)\s*```$",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match:
        return match.group(1).strip()

    return text


def sha256_text(text):
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            obj,
            f,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--category",
        required=True,
        help="Example: finance",
    )

    parser.add_argument(
        "--n-init",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=3000,
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
    )

    args = parser.parse_args()

    category = args.category.strip().lower()


    # --------------------------------------------------------
    # Load .env
    # --------------------------------------------------------

    load_dotenv(REPO_ROOT / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")

    optimizer_model = os.getenv("OPTIMIZER_MODEL")
    optimizer_api_mode = os.getenv(
        "OPTIMIZER_API_MODE",
        "responses"
    ).strip().lower()

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not found in .env"
        )

    if not optimizer_model:
        raise RuntimeError(
            "OPTIMIZER_MODEL not found in .env"
        )

    if optimizer_api_mode not in {
        "responses",
        "chat_completions",
    }:
        raise RuntimeError(
            "OPTIMIZER_API_MODE must be either "
            "'responses' or 'chat_completions'."
        )


    # --------------------------------------------------------
    # Input / output paths
    # --------------------------------------------------------

    split_dir = (
        REPO_ROOT
        / "benchmark"
        / "VisualToolBench"
        / "pilot_split"
        / category
    )

    input_path = (
        split_dir
        / f"skill_init_{args.n_init}.json"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Initial-skill split not found:\n{input_path}"
        )

    output_dir = (
        REPO_ROOT
        / "experiment_assets"
        / "skills"
        / category
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / "S0_initial.md"
    )

    request_path = (
        output_dir
        / "S0_initial.request.txt"
    )

    metadata_path = (
        output_dir
        / "S0_initial.meta.json"
    )


    # --------------------------------------------------------
    # Protect frozen baseline
    # --------------------------------------------------------

    if output_path.exists() and not args.overwrite:
        raise FileExistsError(
            f"\nS0 already exists:\n{output_path}\n\n"
            "The initial baseline should normally remain frozen.\n"
            "Use --overwrite only for an infrastructure failure "
            "or an intentional experimental reset."
        )


    # --------------------------------------------------------
    # Load frozen examples
    # --------------------------------------------------------

    with open(
        input_path,
        "r",
        encoding="utf-8",
    ) as f:
        samples = json.load(f)

    if len(samples) != args.n_init:
        raise RuntimeError(
            f"Expected {args.n_init} examples, "
            f"but found {len(samples)}."
        )


    # --------------------------------------------------------
    # Construct exact model input
    # --------------------------------------------------------

    examples_text = format_examples(
        samples,
        category,
    )

    model_input = f"""
The target VisualToolBench category is:

{category}

Below are representative tasks from this category.

Use these examples only to infer reusable task-solving procedures.

================ REPRESENTATIVE TASKS ================

{examples_text}

================ END OF TASKS =========================
""".strip()


    # --------------------------------------------------------
    # Save exact request snapshot
    # --------------------------------------------------------

    with open(
        request_path,
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            "========== INSTRUCTIONS ==========\n\n"
        )

        f.write(SKILL_INSTRUCTIONS)

        f.write(
            "\n\n========== INPUT ==========\n\n"
        )

        f.write(model_input)


    # --------------------------------------------------------
    # Client
    # --------------------------------------------------------

    client_kwargs = {
        "api_key": api_key,
        "timeout": 300.0,
        "max_retries": 0,
    }

    if base_url:
        client_kwargs["base_url"] = base_url

    client = OpenAI(
        **client_kwargs
    )


    # --------------------------------------------------------
    # Show experiment configuration
    # --------------------------------------------------------

    print("=" * 72)
    print("INITIAL SKILL GENERATION")
    print("=" * 72)

    print("Category:       ", category)
    print("Examples:       ", len(samples))
    print("Optimizer model:", optimizer_model)
    print("API mode:       ", optimizer_api_mode)
    print("Input:          ", input_path)
    print("Output:         ", output_path)

    print("\nSending request...", flush=True)


    # --------------------------------------------------------
    # Optimizer call
    # --------------------------------------------------------

    if optimizer_api_mode == "responses":

        response = client.responses.create(
            model=optimizer_model,
            instructions=SKILL_INSTRUCTIONS,
            input=model_input,
            reasoning={
                "effort": "low"
            },
            max_output_tokens=args.max_output_tokens,
            store=False,
        )

        skill = response.output_text

    else:

        response = client.chat.completions.create(
            model=optimizer_model,
            messages=[
                {
                    "role": "system",
                    "content": SKILL_INSTRUCTIONS,
                },
                {
                    "role": "user",
                    "content": model_input,
                },
            ],
            max_tokens=args.max_output_tokens,
        )

        skill = response.choices[0].message.content


    if not skill:
        raise RuntimeError(
            "Optimizer returned no Skill text."
        )

    skill = strip_markdown_fence(skill)


    # --------------------------------------------------------
    # Save S0
    # --------------------------------------------------------

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:

        f.write(skill)
        f.write("\n")


    # --------------------------------------------------------
    # Usage
    # --------------------------------------------------------

    usage = None

    if getattr(response, "usage", None) is not None:

        try:
            usage = response.usage.model_dump()

        except Exception:
            usage = str(response.usage)


    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    skill_hash = sha256_text(skill)

    metadata = {
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),

        "category": category,

        "input_split": str(input_path),

        "number_of_examples": len(samples),

        "example_doc_ids": [
            str(x.get("doc_id"))
            for x in samples
        ],

        "optimizer_model": optimizer_model,

        "optimizer_gateway": base_url,

        "optimizer_api_mode": optimizer_api_mode,

        "returned_model": getattr(
            response,
            "model",
            None,
        ),

        "response_id": getattr(
            response,
            "id",
            None,
        ),

        "usage": usage,

        "skill_sha256": skill_hash,

        "request_snapshot": str(request_path),

        "output_file": str(output_path),
    }

    save_json(
        metadata_path,
        metadata,
    )


    # --------------------------------------------------------
    # Done
    # --------------------------------------------------------

    print("\n" + "=" * 72)
    print("SUCCESS")
    print("=" * 72)

    print("\nGenerated:")
    print(output_path)

    print("\nMetadata:")
    print(metadata_path)

    print("\nRequest snapshot:")
    print(request_path)

    print("\nSHA256:")
    print(skill_hash)

    if usage is not None:
        print("\nAPI usage:")
        print(json.dumps(
            usage,
            indent=2,
            ensure_ascii=False,
        ))

    print(
        "\nS0 is now frozen. Inspect it for obvious errors, "
        "but do not manually optimize its wording."
    )


if __name__ == "__main__":
    main()
