## 1. Trajectory Comparison

**Trajectory C1:**
- **Outcome:** Semantically correct (913.34)
- **Token cost:** 23,336 total tokens
- **Model calls:** 3
- **Tool calls:** 2 (code_interpreter × 2)
- **Strategy:** Extracted values from receipt, performed calculations in first code_interpreter call, then made a second code_interpreter call solely to round the final result to two decimal places. Presented detailed breakdown with intermediate steps.

**Trajectory C2:**
- **Outcome:** Semantically correct (913.34)
- **Token cost:** 15,309 total tokens (34% lower than C1)
- **Model calls:** 2
- **Tool calls:** 1 (code_interpreter × 1)
- **Strategy:** Extracted values from receipt without zoom, performed all calculations including final rounding in a single code_interpreter call. Presented detailed breakdown with intermediate steps.

**Trajectory C3:**
- **Outcome:** Semantically correct (913.34)
- **Token cost:** 29,911 total tokens (95% higher than C2)
- **Model calls:** 4
- **Tool calls:** 3 (zoom × 2, code_interpreter × 1)
- **Strategy:** Called zoom twice to inspect receipt regions before extracting values, then performed all calculations in a single code_interpreter call. Presented detailed breakdown with intermediate steps.

---

## 2. Evidence-Supported Behavioral Contrasts

### Contrast A: Zoom Usage for Receipt Reading

**Behavior:** Using zoom tool to magnify receipt regions before value extraction.

**Evidence from lower-cost trajectory:**
- C2 extracted all required values (frame: $149.00, lenses: $476.40 each) directly from the receipt image without any zoom calls
- Achieved correct extraction with 15,309 tokens

**Evidence from higher-cost trajectory:**
- C3 called zoom twice before extraction
- C1 trajectory text mentions extracting values but tool call log shows no explicit zoom (ambiguous)
- C3 required 29,911 tokens (nearly double C2)

**Relationship to execution cost:**
- Each zoom call adds one model call/response cycle
- C3's two zoom calls contributed to 4 total model calls vs C2's 2
- The zoom operations themselves and their results consume tokens

**Correctness implications:**
- All three trajectories extracted identical values correctly
- Zoom provided no accuracy advantage for this receipt

**Confidence:** High. The receipt values were sufficiently readable without magnification, as demonstrated by C2's successful extraction.

---

### Contrast B: Code Interpreter Call Consolidation

**Behavior:** Splitting calculations across multiple code_interpreter calls versus consolidating into one.

**Evidence from lower-cost trajectory:**
- C2 performed all calculations including final rounding in a single code_interpreter call
- Printed complete results in one execution: intermediate values and final rounded answer

**Evidence from higher-cost trajectory:**
- C1 made two separate code_interpreter calls:
  - First call: calculated all intermediate values and unrounded final amount
  - Second call: solely to round the final value to 2 decimal places
- Both calls required separate model invocations

**Relationship to execution cost:**
- Each code_interpreter call requires a model call to generate the code and another to process results
- C1's second call only performed `round(913.3446299999998, 2)` → redundant invocation overhead

**Correctness implications:**
- Both approaches produce identical correct results
- Rounding could have been included in the first calculation block

**Confidence:** High. The calculation logic is identical; only the batching differs.

---

## 3. Skill Grounding

### Issue A: Unclear Zoom Necessity Criteria

**Observed behavior:** Executors call zoom on receipts even when values are already readable.

**Exact S0 anchor:**
> "**Use zoom strategically:**  
> - When exact numerical values are small or unclear  
> - To read specific candlestick OHLC values  
> - To distinguish overlapping lines on busy charts  
> - To verify decimal places or currency symbols  
> - To read legends or labels in dense visualizations"

**Why this permits the behavior:**
The Skill lists conditions for when zoom is useful but does not instruct the executor to first attempt reading without zoom or to assess whether the image is already sufficiently clear. "Small or unclear" is subjective and may be conservatively interpreted as "might be small" rather than "is demonstrably unreadable."

**Skill-addressable:** YES

**Plausible alternative explanation:**
Model stochasticity could lead to different initial assessments of image clarity. However, C2 demonstrates that a systematic "attempt to read first" strategy is viable.

---

### Issue B: No Explicit Calculation Batching Guidance

**Observed behavior:** Splitting a multi-step calculation into separate code_interpreter calls.

**Exact S0 anchor:**
> "**code_interpreter:**  
> - Use for all multi-step arithmetic (percentage calculations, gains/losses, totals)  
> - Show work explicitly: state the formula, substitute values, compute result"

And:
> "**Tool sequencing:**  
> 1. Inspect image → zoom if needed → extract values  
> 2. If external data required → web_search → visit → extract  
> 3. Once all values obtained → code_interpreter for calculations  
> 4. Validate computed results against original visual evidence"

**Why this permits the behavior:**
The Skill says "use for all multi-step arithmetic" and "once all values obtained → code_interpreter" (singular) but does not explicitly state "consolidate all calculations into a single code_interpreter call" or warn against multiple calls for successive refinement steps like rounding. The example shows one calculation but doesn't prohibit multiple calls for multi-stage workflows.

**Skill-addressable:** YES

**Plausible alternative explanation:**
An executor might view rounding as a separate "validation" or "formatting" step conceptually distinct from core calculation. However, C2 demonstrates that combining them is straightforward and equally correct.

---

## 4. Candidate Skill-Edit Hypotheses

### Hypothesis H1: Add Initial Direct-Read Instruction for Receipts

**Trajectory evidence:**
- C2 successfully extracted all receipt values without zoom (15,309 tokens)
- C3 used zoom twice before extraction (29,911 tokens)
- Both achieved identical correct extraction

**S0 anchor:**
Section 2 "Inspect and Localize Visual Evidence" → "For receipts and invoices" and Section 3 "zoom" guidance.

**Proposed behavioral policy:**
Before calling zoom on receipts or invoices, attempt to read item prices, tax amounts, and totals directly from the image. Call zoom only if specific values cannot be confidently extracted due to small font size, blur, or occlusion visible in the initial inspection.

**Expected behavioral effect:**
- Executors will first attempt direct extraction
- Zoom will be called only when genuinely needed
- Reduces unnecessary zoom calls when receipt text is sufficiently clear
- Expected reduction: 0-2 tool calls per task (depending on receipt clarity)

**Correctness risk:**
Low. If direct extraction fails or is uncertain, the executor can still call zoom as a fallback. The policy preserves the option to zoom while discouraging premature use.

**Confidence:** High

---

### Hypothesis H2: Require Single-Call Calculation Consolidation

**Trajectory evidence:**
- C1 used two code_interpreter calls: main calculation + rounding (23,336 tokens)
- C2 used one code_interpreter call for all calculations (15,309 tokens)
- Both achieved identical correct results

**S0 anchor:**
Section 3 "code_interpreter" guidance and "Tool sequencing" step 3.

**Proposed behavioral policy:**
Once all input values have been extracted, perform all required calculations—including intermediate steps, final computation, and rounding—in a single code_interpreter call. Structure the code with comments to show each stage, but execute all stages in one invocation. Do not make separate calls for rounding, formatting, or minor refinements unless new information requires recalculation.

**Expected behavioral effect:**
- Executors will batch all arithmetic into one code block
- Eliminates redundant model invocations for post-processing steps like rounding
- Expected reduction: 1 model call + 1 tool call when multiple calculation stages exist

**Correctness risk:**
Very low. Consolidation requires only organizational change, not algorithmic change. All steps remain explicit via comments and print statements.

**Confidence:** High

---

### Hypothesis H3: Add Stopping Rule After Sufficient Precision

**Trajectory evidence:**
- All three trajectories calculated to full floating-point precision, then rounded
- C1 made an extra call specifically for rounding
- Final answers differ by at most one cent due to rounding

**S0 anchor:**
Section 6 "Produce the Final Answer" → "Round to reasonable precision (typically 2 decimal places for money...)"

**Proposed behavioral policy:**
When performing financial calculations, round currency values to 2 decimal places within the same calculation block that produces the raw result. Do not defer rounding to a separate step or tool call. For final output, present the rounded value directly.

**Expected behavioral effect:**
- Rounding becomes an integrated final line in the calculation code
- Eliminates the pattern of calculate → verify precision → recalculate
- Expected reduction: up to 1 tool call and 1 model call in cases like C1

**Correctness risk:**
Very low. Rounding to 2 decimals for currency is already prescribed by S0; this only changes when it occurs.

**Confidence:** Medium (overlaps significantly with H2; may be redundant if H2 is adopted)

---

## 5. Rejected / Unsupported Ideas

### R1: "Reduce verification or re-inspection"
**Why rejected:** All three trajectories performed similar validation steps. There is no evidence that verification contributed to cost differences. The Finance Skill explicitly requires validation ("Validate results against visual evidence"), and none of the trajectories over-validated.

---

### R2: "Simplify explanation or reduce output verbosity"
**Why rejected:** All three trajectories produced similar-length explanations with comparable structure (extract → calculate → present). Output verbosity appears roughly constant across trajectories. The cost differences stem from tool/model call counts, not explanation length.

---

### R3: "Skip intermediate calculation steps"
**Why rejected:** All trajectories showed intermediate steps as prescribed by S0 ("Show work explicitly: state the formula, substitute values, compute result"). There is no evidence that showing work caused cost variation, and removing it would harm transparency.

---

### R4: "Avoid tool use entirely and calculate mentally"
**Why rejected:** S0 explicitly requires code_interpreter for "any calculation beyond simple mental math" and "multi-step arithmetic." The task involves percentage calculations, subtraction, multiplication, and interest application—clearly multi-step. All three trajectories correctly followed this guidance.

---

### R5: "Always use zoom for precision"
**Why rejected:** C2 demonstrates that zoom is not always necessary. Adding a blanket "always zoom" rule would increase cost without improving correctness. The issue is the opposite: zoom is being overused relative to need.