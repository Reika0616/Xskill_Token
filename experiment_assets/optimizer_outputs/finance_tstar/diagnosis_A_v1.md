# Trajectory Cost Diagnosis

## 1. Trajectory Comparison

### Trajectory A1
- **Outcome**: Correct ($913.34)
- **Token cost**: 51,484 total (46,317 input + 5,167 output)
- **Model calls**: 6
- **Tool calls**: 5 (4 zoom, 1 code_interpreter)
- **Strategy**: Systematic zoom progression into invoice → target item rows and numeric columns → read frame ($149.00) and lenses (2 × $476.40 = $952.80) → single calculation pass computing insurance contributions, financed amount, interest, and total

### Trajectory A2
- **Outcome**: Correct ($913.35, 1-cent rounding difference)
- **Token cost**: 108,822 total (101,074 input + 7,748 output)
- **Model calls**: 11
- **Tool calls**: 10 (9 zoom, 2 code_interpreter)
- **Strategy**: Extended zoom sequence with multiple repositioning attempts → eventually extracted same values → first calculation pass → second calculation pass using Python Decimal library for "proper rounding" → slight variation in final cent

### Trajectory A3
- **Outcome**: Correct ($913.34)
- **Token cost**: 70,112 total (64,000 input + 6,112 output)
- **Model calls**: 8
- **Tool calls**: 7 (6 zoom, 1 code_interpreter)
- **Strategy**: Similar to A1 but with two additional zoom iterations → extracted same values → single calculation pass

## 2. Evidence-Supported Behavioral Contrasts

### Contrast 1: Zoom iteration count
- **Behavior**: Number of zoom calls to read invoice line items
- **Lower-cost evidence**: A1 used 4 zoom calls and successfully extracted all required values (frame: 149.00, lenses: 2×476.40)
- **Higher-cost evidence**: A2 used 9 zoom calls on the same image, with repeated repositioning ("zoom further into," "zoom tightly on," "zoom slightly to the left," "zoom further to the left," "zoom out slightly downward," "zoom further down and left")
- **Relationship to cost**: Each additional zoom call adds ~10k tokens (input context + output + reasoning)
- **Correctness implications**: All trajectories extracted identical values; additional zooms did not improve accuracy
- **Confidence**: HIGH

### Contrast 2: Calculation verification passes
- **Behavior**: Number of code_interpreter calls for the same multi-step calculation
- **Lower-cost evidence**: A1 and A3 performed one calculation pass, computed all intermediate values explicitly, and arrived at the final answer
- **Higher-cost evidence**: A2 performed calculation twice: first with standard Python float arithmetic (result: 913.3446299999998), then a second pass using Decimal library for "proper rounding" (result: 913.35)
- **Relationship to cost**: Second calculation added ~1 model call and extended output reasoning
- **Correctness implications**: The Decimal recalculation changed the final cent from .34 to .35; both are within reasonable rounding variance for a finance calculation
- **Confidence**: MEDIUM (only one trajectory exhibited this; less statistical support)

### Contrast 3: Spatial search strategy during zoom
- **Behavior**: Directional repositioning vs. convergent targeting
- **Lower-cost evidence**: A1 zoomed progressively toward target region (central invoice → item rows → numeric columns → final tight view), with each zoom narrowing focus
- **Higher-cost evidence**: A2 exhibited backtracking and lateral exploration (zoomed right, then left, then right again, then downward, then left again), suggesting trial-and-error rather than direct convergence
- **Relationship to cost**: Non-convergent zoom paths require more iterations to locate the same information
- **Correctness implications**: No correctness benefit observed; same values extracted
- **Confidence**: MEDIUM

## 3. Skill Grounding

### Issue 1: Unbounded zoom iteration
- **Observed behavior**: A2 zoomed 9 times; A3 zoomed 6 times; A1 zoomed 4 times—all to extract the same three values from a static invoice
- **S0 anchor**: 
  - "Re-zoom if the first magnification is insufficient" (line under zoom/When to use)
  - "Use to verify critical values before calculations" (Workflow §2)
  - No stopping rule or sufficiency criterion provided
- **Why this permits the behavior**: The Skill emphasizes precision and verification ("Financial visual tasks require precision above approximation," "Take time to extract precise values") but does not define when a value has been successfully extracted or when re-zooming should stop. "Insufficient" is subjective.
- **Skill-addressable**: YES
- **Alternative explanation**: Stochastic model perception differences (some runs may find text less legible), but the repeated repositioning in A2 suggests search/navigation uncertainty rather than perceptual difficulty

### Issue 2: Verification through recalculation
- **Observed behavior**: A2 performed two calculation passes, stating the second was for "proper rounding"
- **S0 anchor**:
  - "Recalculate using a different method if possible" (Workflow §5, Validate the Result)
  - "Double-check calculations" (Output Principles)
  - No guidance on when validation is complete or when recalculation is redundant
- **Why this permits the behavior**: The Skill encourages validation but does not distinguish between necessary verification (catching errors) and redundant recalculation (refining already-correct results). The phrase "if possible" is permissive rather than conditional on detecting an error.
- **Skill-addressable**: YES
- **Alternative explanation**: The Decimal recalculation in A2 may reflect a model preference for arbitrary-precision arithmetic in finance contexts, but S0 does not guide when such precision is required vs. when standard float is acceptable

### Issue 3: Vague zoom targeting
- **Observed behavior**: A2 used directional navigation ("further to the left," "slightly downward") rather than semantic targets ("the Total column," "the row showing lenses")
- **S0 anchor**:
  - "Identify the region containing the target information" (zoom/How to use)
  - "Target the specific region containing the required data point" (Workflow §3)
  - No instruction to name semantic targets before zooming or to describe what value is being sought
- **Why this permits the behavior**: The Skill instructs agents to "identify" and "target" regions but does not require them to articulate *what value* they are extracting or *which column/row* they need, leading to spatial trial-and-error
- **Skill-addressable**: YES
- **Alternative explanation**: Invoice layout complexity, but all three trajectories worked with the same image

## 4. Candidate Skill-Edit Hypotheses

### Hypothesis 1: Add explicit zoom-sufficiency rule
- **Trajectory evidence**: A1 extracted all required values in 4 zooms; A2 used 9 zooms and extracted the same values; A3 used 6 zooms for the same outcome
- **S0 anchor**: "Re-zoom if the first magnification is insufficient" with no definition of sufficiency; "Avoid over-zooming beyond useful detail" with no operationalization
- **Proposed behavioral policy**: 
  - Before each zoom, state which specific value or text you need to read (e.g., "I need to read the Total (tax incl.) for the lenses row").
  - After each zoom, explicitly confirm whether that value was successfully extracted or state why it remains unclear.
  - If a required numeric value has been read and recorded, do not re-zoom to verify it unless you have specific evidence (e.g., ambiguous digit, partial occlusion) that the reading may be incorrect.
- **Expected behavioral effect**: Reduce redundant zoom iterations by establishing clear extraction milestones; prevent backtracking to already-extracted values
- **Correctness risk**: LOW—value extraction is binary (either the number is readable or it is not); additional zooms on already-extracted values provided no correctness benefit in any trajectory
- **Confidence**: HIGH

### Hypothesis 2: Constrain validation recalculation to error cases
- **Trajectory evidence**: A1 and A3 calculated once and produced correct answers; A2 calculated twice, with the second pass changing the final cent due to Decimal precision
- **S0 anchor**: "Recalculate using a different method if possible" under Validate the Result; "Double-check calculations" under Output Principles
- **Proposed behavioral policy**:
  - Perform all multi-step calculations in a single code_interpreter pass, showing intermediate values.
  - After calculation, visually cross-check the magnitude of computed results against the original evidence (e.g., "The computed insurance total of $227.78 is plausible given the invoice total of $1,101.80").
  - Recalculate only if you detect a specific error (wrong formula, inconsistent units, magnitude mismatch with visual evidence). Do not recalculate to explore alternative rounding or precision libraries unless the task explicitly requires it.
- **Expected behavioral effect**: Eliminate redundant calculation passes when initial results are correct and consistent with visual evidence
- **Correctness risk**: LOW—the one-cent difference between A1/A3 ($913.34) and A2 ($913.35) falls within acceptable rounding variance for currency; tasks requiring exact decimal precision can still request it explicitly
- **Confidence**: MEDIUM (single-trajectory evidence; may not generalize)

### Hypothesis 3: Require semantic zoom targets before spatial navigation
- **Trajectory evidence**: A1 used convergent zoom path; A2 used trial-and-error with multiple repositionings; A3 intermediate
- **S0 anchor**: "Identify the region containing the target information" and "Target the specific region" without requiring agents to name what they are targeting
- **Proposed behavioral policy**:
  - Before calling zoom, state in plain language which piece of information you need (e.g., "I need to read the unit price for the frame" or "I need to verify the subtotal before tax").
  - Describe the expected location by semantic reference (e.g., "the third column in the item table") rather than only spatial direction.
  - After zooming, confirm whether the target information is now visible and readable; if not, describe what obstacle remains (text too small, wrong region captured, occlusion).
- **Expected behavioral effect**: Improve zoom path convergence by forcing explicit goal-setting; reduce directionless repositioning
- **Correctness risk**: VERY LOW—does not change what is extracted, only how navigation is planned
- **Confidence**: MEDIUM

## 5. Rejected / Unsupported Ideas

### ❌ "Limit zoom to maximum N calls"
- **Why rejected**: No evidence that a fixed limit is appropriate—image complexity varies; A1 used 4, A3 used 6, both were correct; a hard cap could prevent necessary extraction in genuinely difficult images

### ❌ "Always use Decimal for currency calculations"
- **Why rejected**: A1 and A3 used float and produced correct answers; the one-cent difference in A2 did not improve correctness and is within normal rounding variance; enforcing Decimal would add cost without consistent benefit across these trajectories

### ❌ "Read entire invoice in one pass before zooming"
- **Why rejected**: No trajectory attempted this; S0 already recommends zoom for small text; cannot assess impact without evidence

### ❌ "Stop after first successful value extraction"
- **Why rejected**: Multiple values were required (frame, lenses, totals); the issue is not stopping after *first* value but recognizing when *each* value has been successfully extracted

### ❌ "Forbid directional language in zoom reasoning"
- **Why rejected**: Too restrictive; spatial navigation language is sometimes appropriate; the issue is lack of semantic targets, not presence of directional terms

### ❌ "Always validate by recalculating"
- **Why rejected**: This would increase cost; A2's recalculation did not catch an error (the initial calculation was correct); the hypothesis is the opposite—constrain rather than mandate recalculation

---

**Summary**: The most promising Skill-addressable cause of cost variation is unbounded zoom iteration (Hypothesis 1), supported by a 2.25× difference in zoom calls between A2 and A1 with no correctness benefit. The Skill currently emphasizes precision and verification but lacks operational stopping rules for value extraction and validation, permitting redundant tool use in pursuit of marginal or illusory improvements.