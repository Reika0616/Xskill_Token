#!/usr/bin/env python3

"""
Prepare a category-specific VisualToolBench pilot.

Pipeline:

    val_single.json
          |
          | filter by one category, e.g. finance
          v
    category task pool
          |
          +---- N_INIT tasks --------> initial Skill construction
          |
          +---- N_CANDIDATE tasks ---> candidate task screening
          |
          +---- remaining -----------> reserve

Optionally, the script can directly call an OpenAI model to generate
the initial category-specific Skill S0.

Example:

    python experiment_scripts/prepare_category_pilot.py \
        --category finance \
        --generate-skill
"""

import argparse
import hashlib
import json
import os
import random
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# Repository paths
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

DEFAULT_SOURCE = (
    REPO_ROOT
    / "benchmark"
    / "VisualToolBench"
    / "val_single.json"
)


# ============================================================
# Initial-Skill prompt
# ============================================================

SKILL_INSTRUCTIONS = """
You are constructing an INITIAL category-specific Skill for a multimodal
tool-using agent on VisualToolBench.

The Skill should support NEW tasks belonging to the SAME broad task
category as the representative examples provided below.

This Skill will serve as a neutral baseline for later experiments.

You are given representative task descriptions and golden answers.

Your goal is NOT to memorize, reproduce, or solve these particular
examples.

Instead, infer reusable procedural guidance and task-solving patterns
that would help an agent solve NEW tasks from the same category.

The execution environment may provide the following tools:

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

The Skill should provide concrete procedural guidance for:

1. understanding the task and the evidence required;
2. inspecting and localizing relevant visual information;
3. deciding when different tools are appropriate;
4. extracting textual, numerical, spatial, or semantic information;
5. performing calculations when needed;
6. retrieving external information when needed;
7. combining visual, computational, and external evidence;
8. validating important conclusions;
9. producing the requested final answer.

IMPORTANT CONSTRAINTS:

- Do NOT mention specific examples supplied below.

- Do NOT copy or memorize example-specific answers, companies, people,
  numbers, locations, dates, or other instance-specific details.

- The resulting Skill should generalize to unseen tasks from the same
  category.

- Do NOT assume that every task requires every tool.

- Do NOT prescribe one fixed tool sequence for every task.

- Tool use should remain conditional on the task and available evidence.

- Do NOT mention this research experiment.

- Do NOT mention token usage or token reduction.

- Do NOT mention execution cost or cost reduction.

- Do NOT mention latency.

- Do NOT instruct the agent to minimize tool calls.

- Do NOT instruct the agent to minimize reasoning.

- Do NOT instruct the agent to minimize verification.

- Do NOT optimize for efficiency or cost.

The objective of this INITIAL Skill is NORMAL TASK PERFORMANCE.

Prefer concrete, actionable procedural rules over long explanatory prose.

The document should be reasonably detailed, but should not become an
encyclopedic description of every possible task.

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

Do not wrap the output in a Markdown code fence.
""".strip()


# ============================================================
# Helper functions
# ============================================================

def get_category(sample):
    """
    Our converted data stores original VisualToolBench prompt_category
    as data_source.
    """
    return str(
        sample.get("data_source")
        or sample.get("prompt_category")
        or "__UNKNOWN__"
    )


def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            obj,
            f,
            ensure_ascii=False,
            indent=2,
        )


def clean_problem(problem):
    """
    Remove XSkill <image> placeholders because the initial Skill generator
    only sees textual task descriptions and golden answers.
    """
    return str(problem).replace("<image>", "").strip()


def format_examples(samples, category):
    blocks = []

    for i, sample in enumerate(samples, start=1):

        problem = clean_problem(
            sample.get("problem", "")
        )

        answer = str(
            sample.get("solution", "")
        ).strip()

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


def strip_outer_markdown_fence(text):
    text = text.strip()

    match = re.match(
        r"^```(?:markdown|md)?\\s*(.*?)\\s*```$",
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


def objective_leakage_check(skill):
    suspicious = [
        r"reduce\\s+(?:the\\s+)?tokens?",
        r"save\\s+tokens?",
        r"token\\s+(?:usage|cost|budget)",
        r"minimi[sz]e\\s+(?:the\\s+)?cost",
        r"reduce\\s+(?:the\\s+)?cost",
        r"minimi[sz]e\\s+(?:the\\s+)?tool\\s+calls?",
        r"reduce\\s+(?:the\\s+)?tool\\s+calls?",
        r"cost[- ]aware",
        r"reduce\\s+latency",
    ]

    findings = []

    for pattern in suspicious:
        if re.search(
            pattern,
            skill,
            flags=re.IGNORECASE,
        ):
            findings.append(pattern)

    return findings


# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Prepare a category-specific VisualToolBench pilot "
            "and optionally generate initial Skill S0."
        )
    )

    parser.add_argument(
        "--category",
        required=True,
        help=(
            "VisualToolBench category, e.g. "
            "finance, medical, sports, generalist"
        ),
    )

    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
    )

    parser.add_argument(
        "--n-init",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--n-candidate",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=20260901,
    )

    parser.add_argument(
        "--generate-skill",
        action="store_true",
        help="Call the OpenAI API after preparing the split.",
    )

    parser.add_argument(
        "--model",
        default=None,
        help="Override OPENAI_MODEL from .env",
    )

    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=8000,
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Allow overwriting an already generated pilot split "
            "and Skill."
        ),
    )

    args = parser.parse_args()

    category = args.category.strip().lower()

    # --------------------------------------------------------
    # Load source dataset
    # --------------------------------------------------------

    if not args.source.exists():
        raise FileNotFoundError(
            f"Source dataset not found: {args.source}"
        )

    with open(
        args.source,
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)

    print("=" * 72)
    print("CATEGORY-SPECIFIC VISUALTOOLBENCH PILOT")
    print("=" * 72)
    print("Source:", args.source)
    print("Total single-turn samples:", len(data))

    # --------------------------------------------------------
    # Show all available categories
    # --------------------------------------------------------

    category_counts = Counter(
        get_category(x).lower()
        for x in data
    )

    print("\nAvailable categories:")

    for name, count in category_counts.most_common():
        print(f"  {name:20s} {count}")

    # --------------------------------------------------------
    # Filter selected category
    # --------------------------------------------------------

    category_pool = [
        x
        for x in data
        if get_category(x).lower() == category
    ]

    print(
        f"\nSelected category: {category}"
    )
    print(
        f"Available samples: {len(category_pool)}"
    )

    required = (
        args.n_init
        + args.n_candidate
    )

    if len(category_pool) < required:
        raise ValueError(
            f"\nCategory '{category}' contains only "
            f"{len(category_pool)} samples, but "
            f"{required} are required "
            f"({args.n_init} init + "
            f"{args.n_candidate} candidate).\n"
            f"Reduce --n-init / --n-candidate or choose "
            f"a larger category."
        )

    # --------------------------------------------------------
    # Check IDs
    # --------------------------------------------------------

    doc_ids = [
        str(x["doc_id"])
        for x in category_pool
    ]

    if len(doc_ids) != len(set(doc_ids)):
        raise RuntimeError(
            "Duplicate doc_id detected inside category pool."
        )

    # --------------------------------------------------------
    # Fixed random sampling
    # --------------------------------------------------------

    rng = random.Random(args.seed)

    shuffled = category_pool.copy()
    rng.shuffle(shuffled)

    init_tasks = shuffled[:args.n_init]

    candidate_tasks = shuffled[
        args.n_init:
        args.n_init + args.n_candidate
    ]

    reserve_tasks = shuffled[
        args.n_init + args.n_candidate:
    ]

    # --------------------------------------------------------
    # Leakage check
    # --------------------------------------------------------

    init_ids = {
        str(x["doc_id"])
        for x in init_tasks
    }

    candidate_ids = {
        str(x["doc_id"])
        for x in candidate_tasks
    }

    if not init_ids.isdisjoint(candidate_ids):
        raise RuntimeError(
            "Init and candidate splits overlap."
        )

    # --------------------------------------------------------
    # Output paths
    # --------------------------------------------------------

    split_dir = (
        REPO_ROOT
        / "benchmark"
        / "VisualToolBench"
        / "pilot_split"
        / category
    )

    skill_dir = (
        REPO_ROOT
        / "experiment_assets"
        / "skills"
        / category
    )

    manifest_path = (
        split_dir
        / "pilot_manifest.json"
    )

    if manifest_path.exists() and not args.overwrite:
        raise FileExistsError(
            f"\nPilot already exists:\n"
            f"{manifest_path}\n\n"
            "This is intentional: once a pilot split has been "
            "created, it should normally remain frozen.\n"
            "Use --overwrite only if you intentionally want "
            "to recreate it."
        )

    split_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    skill_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Save split files
    # --------------------------------------------------------

    init_path = (
        split_dir
        / f"skill_init_{args.n_init}.json"
    )

    candidate_path = (
        split_dir
        / f"candidate_{args.n_candidate}.json"
    )

    reserve_path = (
        split_dir
        / "reserve.json"
    )

    save_json(
        init_path,
        init_tasks,
    )

    save_json(
        candidate_path,
        candidate_tasks,
    )

    save_json(
        reserve_path,
        reserve_tasks,
    )

    # --------------------------------------------------------
    # Build skill-generation material
    # --------------------------------------------------------

    examples_text = format_examples(
        init_tasks,
        category,
    )

    material_path = (
        split_dir
        / "skill_init_material.md"
    )

    with open(
        material_path,
        "w",
        encoding="utf-8",
    ) as f:
        f.write(
            f"# VisualToolBench Initial Skill Examples\n\n"
        )
        f.write(
            f"Category: {category}\n\n"
        )
        f.write(examples_text)
        f.write("\n")

    # --------------------------------------------------------
    # Save manifest
    # --------------------------------------------------------

    manifest = {
        "source_file": str(args.source),
        "source_single_turn_size": len(data),
        "category": category,
        "category_pool_size": len(category_pool),
        "seed": args.seed,

        "skill_init": {
            "size": len(init_tasks),
            "doc_ids": [
                str(x["doc_id"])
                for x in init_tasks
            ],
        },

        "candidate": {
            "size": len(candidate_tasks),
            "doc_ids": [
                str(x["doc_id"])
                for x in candidate_tasks
            ],
        },

        "reserve_size": len(reserve_tasks),
    }

    save_json(
        manifest_path,
        manifest,
    )

    # --------------------------------------------------------
    # Print selected tasks
    # --------------------------------------------------------

    print("\n" + "=" * 72)
    print("SPLIT CREATED")
    print("=" * 72)

    print(
        f"Skill-init:  {len(init_tasks)}"
    )
    print(
        f"Candidate:   {len(candidate_tasks)}"
    )
    print(
        f"Reserve:     {len(reserve_tasks)}"
    )

    print("\nCandidate tasks:")

    for i, sample in enumerate(
        candidate_tasks,
        start=1,
    ):
        problem = clean_problem(
            sample["problem"]
        )

        print("\n" + "-" * 72)
        print(
            f"[{i}] doc_id={sample['doc_id']}"
        )
        print(problem[:800])

    print("\nSaved:")
    print(init_path)
    print(candidate_path)
    print(reserve_path)
    print(material_path)
    print(manifest_path)

    # --------------------------------------------------------
    # Stop here if user only wants split preparation
    # --------------------------------------------------------

    if not args.generate_skill:

        print("\nSplit preparation complete.")
        print(
            "Run again with --generate-skill only after "
            "you are satisfied with the frozen split."
        )
        return

    # --------------------------------------------------------
    # Load OpenAI configuration
    # --------------------------------------------------------

    from openai import OpenAI

    load_dotenv(
        REPO_ROOT / ".env"
    )

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not found in XSkill/.env"
        )

    model = (
        args.model
        or os.getenv("OPENAI_MODEL")
    )

    if not model:
        raise RuntimeError(
            "No model specified.\n"
            "Set OPENAI_MODEL in .env or use --model."
        )

    base_url = os.getenv(
        "OPENAI_BASE_URL"
    )

    # --------------------------------------------------------
    # Build exact model input
    # --------------------------------------------------------

    model_input = f"""
The target VisualToolBench task category is:

{category}

Below are representative tasks from this category.

Use them only to infer reusable task-solving procedures.

================ REPRESENTATIVE TASKS ================

{examples_text}

================ END OF TASKS =========================
""".strip()

    request_path = (
        skill_dir
        / "S0_initial.request.txt"
    )

    output_path = (
        skill_dir
        / "S0_initial.md"
    )

    metadata_path = (
        skill_dir
        / "S0_initial.meta.json"
    )

    if output_path.exists() and not args.overwrite:
        raise FileExistsError(
            f"Initial Skill already exists:\n"
            f"{output_path}"
        )

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
        "timeout": 600.0,
    }

    if base_url:
        client_kwargs["base_url"] = base_url

    client = OpenAI(
        **client_kwargs
    )

    # --------------------------------------------------------
    # Generate Skill
    # --------------------------------------------------------

    print("\n" + "=" * 72)
    print("GENERATING INITIAL SKILL")
    print("=" * 72)
    print("Model:", model)

    response = client.responses.create(
        model=model,
        instructions=SKILL_INSTRUCTIONS,
        input=model_input,
        max_output_tokens=args.max_output_tokens,
        store=False,
    )

    skill = getattr(
        response,
        "output_text",
        None,
    )

    if not skill:
        raise RuntimeError(
            "Model returned no output_text."
        )

    skill = strip_outer_markdown_fence(
        skill
    )

    # --------------------------------------------------------
    # Save Skill
    # --------------------------------------------------------

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:
        f.write(skill)
        f.write("\n")

    skill_hash = sha256_text(
        skill
    )

    # --------------------------------------------------------
    # Usage metadata
    # --------------------------------------------------------

    usage = None

    if getattr(
        response,
        "usage",
        None,
    ) is not None:

        try:
            usage = (
                response
                .usage
                .model_dump()
            )
        except Exception:
            usage = str(
                response.usage
            )

    metadata = {
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),

        "category": category,

        "input_split": str(
            init_path
        ),

        "number_of_examples": len(
            init_tasks
        ),

        "example_doc_ids": [
            str(x["doc_id"])
            for x in init_tasks
        ],

        "requested_model": model,

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

        "request_snapshot": str(
            request_path
        ),

        "output_file": str(
            output_path
        ),
    }

    save_json(
        metadata_path,
        metadata,
    )

    # --------------------------------------------------------
    # Simple objective-leakage check
    # --------------------------------------------------------

    findings = objective_leakage_check(
        skill
    )

    print("\n" + "=" * 72)
    print("INITIAL SKILL GENERATED")
    print("=" * 72)

    print("Skill:")
    print(output_path)

    print("\nMetadata:")
    print(metadata_path)

    print("\nRequest snapshot:")
    print(request_path)

    print("\nSHA256:")
    print(skill_hash)

    if findings:

        print(
            "\nWARNING: possible cost-objective leakage detected:"
        )

        for finding in findings:
            print(
                "  ",
                finding,
            )

    else:
        print(
            "\nNo obvious cost-objective leakage detected."
        )

    print(
        "\nDo not regenerate this Skill merely because "
        "you dislike its style."
    )


if __name__ == "__main__":
    main()
