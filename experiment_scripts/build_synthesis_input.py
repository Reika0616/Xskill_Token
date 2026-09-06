#!/usr/bin/env python3

from pathlib import Path

PROMPT = Path(
    "experiment_assets/prompts/diagnosis_synthesis_rewrite_v1.txt"
)

S0 = Path(
    "experiment_assets/skills/finance/S0_initial.md"
)

OUT_DIR = Path(
    "experiment_assets/optimizer_outputs/finance_tstar"
)

DIAGNOSES = {
    "A": OUT_DIR / "diagnosis_A_v1.md",
    "B": OUT_DIR / "diagnosis_B_v1.md",
    "C": OUT_DIR / "diagnosis_C_v1.md",
}

DEST = Path(
    "experiment_assets/optimizer_inputs/finance_tstar/"
    "synthesis_v1_input.md"
)

parts = []

parts.append(
    PROMPT.read_text(encoding="utf-8").strip()
)

parts.append(
    "\n\n# ORIGINAL BASELINE SKILL S0\n\n"
    "<BASELINE_SKILL>\n"
    + S0.read_text(encoding="utf-8").strip()
    + "\n</BASELINE_SKILL>\n"
)

for name, path in DIAGNOSES.items():
    parts.append(
        f"\n\n# DIAGNOSIS {name}\n\n"
        f"<DIAGNOSIS_{name}>\n"
        + path.read_text(encoding="utf-8").strip()
        + f"\n</DIAGNOSIS_{name}>\n"
    )

DEST.parent.mkdir(parents=True, exist_ok=True)

content = "\n".join(parts)

DEST.write_text(
    content,
    encoding="utf-8",
)

print("Saved:", DEST)
print("Characters:", f"{len(content):,}")
