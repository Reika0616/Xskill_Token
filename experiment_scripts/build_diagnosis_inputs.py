#!/usr/bin/env python3

import json
import re
from pathlib import Path

TSTAR_ID = "6870357d15624e798bfc83af"

S0_PATH = Path(
    "experiment_assets/skills/finance/S0_initial.md"
)

PROMPT_PATH = Path(
    "experiment_assets/prompts/cost_diagnosis_v1.txt"
)

OUT_DIR = Path(
    "experiment_assets/optimizer_inputs/finance_tstar"
)

# Actual model identities are used only here to locate files.
# They are NOT written into optimizer inputs.
SOURCES = {
    "A": [
        (
            Path(
                "outputs/pilot_finance_candidate_screen_gpt5/results.jsonl"
            ),
            True,
        ),
    ],

    "B": [
        (
            Path(
                "outputs/tstar_baseline_claude/results.jsonl"
            ),
            False,
        ),
    ],

    "C": [
        (
            Path(
                "outputs/tstar_gemini31_smoke/results.jsonl"
            ),
            False,
        ),
        (
            Path(
                "outputs/tstar_baseline_gemini31_extra/results.jsonl"
            ),
            False,
        ),
    ],
}


def sanitize_trajectory(text):
    """
    Preserve behavioral trajectory content while mechanically removing
    transport-level image payloads if any are present.
    """
    if not text:
        return ""

    text = re.sub(
        r"data:image/[^;]+;base64,[A-Za-z0-9+/=\s]+",
        "[IMAGE_DATA_OMITTED]",
        text,
    )

    return text.strip()


def load_rows(paths):
    rows = []

    for path, filter_tstar in paths:
        if not path.exists():
            raise FileNotFoundError(path)

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                x = json.loads(line)

                if (
                    filter_tstar
                    and x.get("question_id") != TSTAR_ID
                ):
                    continue

                # Exclude infrastructure failures.
                final_answer = str(
                    x.get("final_answer", "")
                )

                if (
                    "All API attempts failed" in final_answer
                    or "Reached max turns" in final_answer
                    or "Reached max image limit" in final_answer
                ):
                    continue

                rows.append(x)

    return rows


def build_input(executor_id, rows, instructions, s0):

    if len(rows) != 3:
        raise ValueError(
            f"Executor {executor_id}: expected 3 valid "
            f"trajectories, found {len(rows)}"
        )

    # Sort only for presentation so trajectory numbering is fixed.
    # Do NOT reorder by cost: optimizer receives the raw costs and
    # should reason about them itself.
    parts = []

    parts.append(instructions)

    parts.append(
        "\n\n# EXPERIMENT INPUT\n"
        f"\nAnonymous executor: Executor {executor_id}\n"
        "\nIMPORTANT: Do not infer or speculate about the identity "
        "of this executor.\n"
    )

    parts.append(
        "\n# BASELINE SKILL S0\n\n"
        "```markdown\n"
        + s0.strip()
        + "\n```\n"
    )

    task_prompt = rows[0].get("prompt", "")

    parts.append(
        "\n# TASK\n\n"
        + str(task_prompt).strip()
        + "\n"
    )

    parts.append(
        "\n# CORRECTNESS NOTE\n\n"
        "All three executions below are treated as semantically "
        "correct for this diagnosis. Minor one-cent rounding "
        "differences in the final numeric answer should not be "
        "interpreted as correctness differences.\n"
    )

    for idx, x in enumerate(rows, 1):

        usage = x.get("usage") or {}
        behavior = x.get("behavior") or {}

        inp = usage.get(
            "total_input_tokens", 0
        ) or 0

        out = usage.get(
            "total_output_tokens", 0
        ) or 0

        total = inp + out

        trajectory = sanitize_trajectory(
            x.get("trajectory_text", "")
        )

        final_answer = str(
            x.get("final_answer", "")
        ).strip()

        parts.append(
            f"\n\n# TRAJECTORY {executor_id}{idx}\n\n"
            "## Execution Metadata\n\n"
            f"- Native input tokens: {inp}\n"
            f"- Native output tokens: {out}\n"
            f"- Native total tokens: {total}\n"
            f"- Reasoning tokens: "
            f"{usage.get('total_reasoning_tokens', 0) or 0}\n"
            f"- Cached tokens: "
            f"{usage.get('total_cached_tokens', 0) or 0}\n"
            f"- Model calls: "
            f"{behavior.get('model_calls', usage.get('num_model_calls', 0))}\n"
            f"- Tool calls: "
            f"{behavior.get('tool_calls', usage.get('num_tool_calls', 0))}\n"
            f"- Retries: "
            f"{behavior.get('retries', usage.get('num_retries', 0))}\n"
            "- Outcome: semantically correct\n"
            "\n## Final Answer\n\n"
            + final_answer
            + "\n\n## Full Behavioral Trajectory\n\n"
            "```text\n"
            + trajectory
            + "\n```\n"
        )

    return "\n".join(parts)


def main():

    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    instructions = PROMPT_PATH.read_text(
        encoding="utf-8"
    )

    s0 = S0_PATH.read_text(
        encoding="utf-8"
    )

    for executor_id, paths in SOURCES.items():

        rows = load_rows(paths)

        content = build_input(
            executor_id,
            rows,
            instructions,
            s0,
        )

        out = OUT_DIR / (
            f"diagnosis_{executor_id}_input.md"
        )

        out.write_text(
            content,
            encoding="utf-8",
        )

        print(
            f"Executor {executor_id}: "
            f"{len(rows)} trajectories -> {out}"
        )

        print(
            f"  input characters: {len(content):,}"
        )


if __name__ == "__main__":
    main()
