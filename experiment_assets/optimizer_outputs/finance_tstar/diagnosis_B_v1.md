## 1. Trajectory Comparison

### B1
- **Outcome:** Correct
- **Total tokens:** 63,027
- **Model calls:** 7
- **Tool calls:** 6 (4 zoom, 2 code_interpreter)
- **Strategy:** Systematic zoom sequence to extract invoice values → first code_interpreter call computing only invoice total → second code_interpreter call computing insurance, financing, and final payment → answer

### B2
- **Outcome:** Correct
- **Total tokens:** 52,167
- **Model calls:** 6
- **Tool calls:** 5 (4 zoom, 1 code_interpreter)
- **Strategy:** Systematic zoom sequence to extract invoice values → single code_interpreter call computing all values (insurance, financing, final payment) → answer

### B3
- **Outcome:** Correct
- **Total tokens:** 47,479
- **Model calls:** 6
- **Tool calls:** 5 (4 zoom, 1 code_interpreter)
- **Strategy:** Systematic zoom sequence to extract invoice values → single code_interpreter call computing all values (insurance, financing, final payment) → answer

**Cost ranking:** B3 (most efficient) < B2 < B1 (least efficient)  
**Difference:** 15,548 tokens between B3 and B1 (32.7% overhead)

---

## 2. Evidence-Supported Behavioral Contrasts

### Contrast 1: Code Interpreter Call Frequency

**Behavior:** Using code_interpreter multiple times for sequential calculations vs. consolidating all calculations into a single call.

**Evidence from lower-cost trajectories (B2, B3):**
- Both made exactly 1 code_interpreter call
- The single call computed all required values: lenses total, insurance payments, financing amount, interest, and final cost
- Output was a structured dictionary or tuple with all intermediate and final results

**Evidence from higher-cost trajectory (B1):**
- Made 2 code_interpreter calls
- First call computed only `1101.8` (the invoice total)
- Second call computed all insurance, financing, and final payment values
- The invoice total (1101.8) was already visible in the zoomed images and explicitly labeled "Total to be paid"

**Relationship to execution cost:**
- Extra model call: +1 call (7 vs 6)
- Extra tool invocation overhead
- Additional reasoning tokens to frame the second call
- The computed invoice total in call 1 was redundant with visible invoice data

**Correctness implications:** None. Both approaches produce correct results.

**Confidence:** High. The behavioral difference is concrete and the cost impact is measurable.

---

### Contrast 2: Calculation Scope Planning

**Behavior:** Computing intermediate values that are already visible in the source document vs. extracting all visible values and computing only what is not visible.

**Evidence from lower-cost trajectories (B2, B3):**
- After zoom sequence, extracted all visible values (frame: 149.00, lenses: 476.40 × 2, total: 1101.80)
- Used code_interpreter only for values requiring calculation (insurance percentages, financing remainder, interest)
- No redundant computation of visible totals

**Evidence from higher-cost trajectory (B1):**
- First code_interpreter call summed frame + lenses to verify invoice total
- This total was already visible as "Total to be paid: $1,101.80" in the zoomed invoice
- Essentially computed `149.00 + 952.80 = 1101.8` despite the value being on screen

**Relationship to execution cost:**
- Unnecessary tool call to compute an already-extracted value
- Additional model turn to process the redundant result
- Increases trajectory length without adding information

**Correctness implications:** None. Validation is appropriate, but computing an already-visible total is redundant rather than validating extraction accuracy.

**Confidence:** High. The invoice total is clearly visible in both B1's zoom results and B2/B3's results; computing it adds no new information.

---

## 3. Skill Grounding

### Issue 1: Redundant Computation of Visible Values

**Observed behavior:** B1 used code_interpreter to compute the invoice total (frame + lenses) that was already clearly visible and labeled in the document.

**Exact S0 anchor:**

From **Section 3: Select and Use Tools → code_interpreter**:
> "Use for all multi-step arithmetic (percentage calculations, gains/losses, totals)"

From **Tool sequencing**:
> "1. Inspect image → zoom if needed → extract values  
> 2. If external data required → web_search → visit → extract  
> 3. Once all values obtained → code_interpreter for calculations"

**Why this may permit the behavior:**

The phrase "use for... totals" and "multi-step arithmetic" does not distinguish between:
- Computing a total that is **not visible** (requires calculation)
- Computing a total that **is visible and labeled** in the document (redundant)

The tool sequencing says "once all values obtained → code_interpreter for calculations," but it does not clarify whether "obtained" means "read from the document" or "computed." An agent might interpret this as "compute all totals even if they are visible, for validation."

**Skill-addressable:** YES

A clarification could specify that code_interpreter should be used for calculations **not visible in the image**, and that visible totals, subtotals, and labeled final amounts should be extracted rather than recomputed.

**Plausible alternative explanation:**

The agent may have intended validation. However, if that were the goal, a more efficient approach would be to extract the visible total and verify it matches the sum, rather than computing first and comparing later. The Skill does not provide explicit guidance on when to validate extraction vs. when to trust clearly labeled values.

---

### Issue 2: Lack of Guidance on Consolidating Calculations

**Observed behavior:** B1 made two separate code_interpreter calls when all calculations could have been performed in one.

**Exact S0 anchor:**

From **Section 3: Select and Use Tools → Tool sequencing**:
> "3. Once all values obtained → code_interpreter for calculations"

From **code_interpreter → How to use**:
> "Use for all multi-step arithmetic"  
> "Show work explicitly: state the formula, substitute values, compute result"

**Why this may permit the behavior:**

The Skill emphasizes using code_interpreter for multi-step arithmetic and showing work explicitly, but it does not provide guidance on:
- Whether to make one consolidated call or multiple sequential calls
- When intermediate results justify a separate tool invocation
- How to batch calculations to minimize tool-call overhead

The phrase "once all values obtained" suggests waiting, but it does not prohibit multiple calls afterward. An agent reading this might reasonably decide to:
1. Compute visible totals first (even if redundant)
2. Then compute derived values separately

**Skill-addressable:** YES

The Skill could add a consolidation principle: when multiple related calculations are required and all inputs are available, perform them in a single code_interpreter call to minimize tool invocations and improve transparency.

**Plausible alternative explanation:**

The agent may have been cautious, computing one step at a time to ensure intermediate correctness. However, B2 and B3 demonstrate that computing everything together is both safe and more efficient.

---

## 4. Candidate Skill-Edit Hypotheses

### Hypothesis 1: Avoid Computing Visible Values

**Trajectory evidence:**
- B1 computed invoice total (1,101.80) despite it being clearly visible and labeled "Total to be paid"
- B2 and B3 extracted the visible total directly and used code_interpreter only for non-visible calculations (insurance percentages, financing, interest)
- Cost difference: 10,860 tokens between B1 and B2 (20.8% overhead)

**S0 anchor:**
- "Use for all multi-step arithmetic (percentage calculations, gains/losses, totals)" does not distinguish visible from non-visible totals
- Tool sequencing says "once all values obtained → code_interpreter for calculations" but does not clarify whether labeled totals count as "obtained"

**Proposed behavioral policy:**
Add to code_interpreter guidance:

> "Use code_interpreter for calculations **that are not directly visible in the image**. When a total, subtotal, or final amount is clearly labeled and visible in the document, extract it directly rather than computing it. Reserve calculation for:
> - Percentages of extracted values (e.g., insurance coverage)
> - Derived amounts not shown in the image (e.g., remainder after deduction, interest on loans)
> - Aggregations across multiple unlabeled items"

**Expected behavioral effect:**
- Agents will distinguish between extraction (reading visible values) and computation (deriving new values)
- Reduces unnecessary code_interpreter calls for validation or redundant summation
- Maintains correctness while eliminating redundant tool invocations

**Correctness risk:**
Low. The policy still allows validation if the agent is uncertain, but discourages computing values that are unambiguous in the source. The examples (insurance percentage, loan interest) are genuinely non-visible and require calculation.

**Confidence:** High. The distinction is clear from B1's zoom results: "Total to be paid: $1,101.80" is explicitly labeled and readable.

---

### Hypothesis 2: Consolidate Related Calculations

**Trajectory evidence:**
- B1 made 2 code_interpreter calls; B2 and B3 made 1
- All three trajectories computed the same set of values (insurance payment, financing amount, interest, final cost)
- B2 and B3 computed all values in a single Python block
- Eliminating the second call saved approximately 10,000-15,000 tokens

**S0 anchor:**
- Tool sequencing: "Once all values obtained → code_interpreter for calculations" (singular "for calculations" does not clarify one call vs. many)
- code_interpreter guidance emphasizes showing work and intermediate steps, but does not address batching

**Proposed behavioral policy:**
Add to code_interpreter guidance:

> "When a task requires multiple related calculations and all input values have been extracted, consolidate them into a single code_interpreter call. Use intermediate variables and print statements to show each step transparently within one execution. Only make separate calls when:
> - New information must be obtained between calculations (e.g., a web search after an initial computation)
> - The task explicitly requests staged computation with user input between steps"

**Expected behavioral effect:**
- Agents will batch all calculations that depend on the same extracted inputs
- Reduces model calls and tool invocation overhead
- Maintains transparency through intermediate variables and print statements within the single call

**Correctness risk:**
Low. The policy preserves the requirement to show work explicitly; it simply consolidates multiple steps into one execution rather than multiple tool calls. B2 and B3 demonstrate that this approach maintains correctness and readability.

**Confidence:** High. The behavioral difference is unambiguous and the cost impact is substantial.

---

### Hypothesis 3: Prioritize Direct Extraction Over Validation Computation

**Trajectory evidence:**
- B1's first code_interpreter call appears to validate the invoice total by recomputing it
- B2 and B3 extracted the visible total and proceeded directly to non-visible calculations
- The invoice shows a clearly labeled "Total to be paid" field, making validation-by-recomputation unnecessary

**S0 anchor:**
- Section 5: "Validate the Result" → "Check against visual evidence" encourages verification
- However, it does not clarify whether validation should happen before or after calculation, or whether it requires tool use
- code_interpreter guidance does not address validation vs. computation trade-offs

**Proposed behavioral policy:**
Add to Section 5: Validate the Result:

> "**Validation timing:** When the document contains clearly labeled totals or final amounts, extract them directly and use them in subsequent calculations. If verification is needed, check calculated results against extracted values after computation, rather than recomputing visible values for validation. Reserve code_interpreter for calculations that produce new information, not for confirming values already visible in the image."

**Expected behavioral effect:**
- Agents will trust clearly labeled values in professional documents (invoices, statements)
- Validation will occur by comparing computed results to extracted values, not by redundant computation
- Reduces unnecessary tool calls for validation

**Correctness risk:**
Medium. There is a small risk that an agent might trust a misread value. However, the policy still allows validation after calculation; it simply discourages pre-computation validation. The trade-off is efficiency vs. defense against extraction errors. Given that all three trajectories extracted values correctly, this risk appears low in practice.

**Confidence:** Medium. The behavioral pattern is clear in B1, but the interpretation as "validation" is inferred rather than explicit. It's possible B1 simply misunderstood the task sequencing rather than intentionally validating.

---

## 5. Rejected / Unsupported Ideas

### Rejected: "Use fewer zoom calls"

**Why rejected:** All three trajectories used exactly 4 zoom calls. The zoom behavior is consistent across high-cost and low-cost executions. The Skill already provides appropriate zoom guidance, and the evidence does not support that zoom frequency contributes to cost variation.

---

### Rejected: "Shorten reasoning length"

**Why rejected:** While B1 has higher reasoning token counts, the primary cost driver is the extra model call and tool invocation, not reasoning verbosity per turn. The Skill should not discourage thorough reasoning; the issue is structural (number of calls) rather than reasoning depth.

---

### Rejected: "Extract values in a specific order"

**Why rejected:** All three trajectories extracted values in similar sequences (frame, lenses, totals). There is no evidence that extraction order affects cost. The cost difference arises from how the extracted values are used in calculation, not from the extraction process itself.

---

### Rejected: "Avoid code_interpreter for simple arithmetic"

**Why rejected:** The insurance percentages (23%, 5.8%) and loan interest (4.5%) require precise decimal arithmetic. The Skill correctly requires code_interpreter for financial calculations. The issue is not using the tool, but using it redundantly. B2 and B3 demonstrate that one well-structured call is appropriate.

---

### Rejected: "Always validate extracted values by recomputation"

**Why rejected:** This would prescribe the B1 behavior and increase cost. The evidence suggests that B2 and B3 are correct without recomputing visible totals. Validation is valuable when extraction is ambiguous, but professional invoices with clearly labeled totals do not require computational validation.