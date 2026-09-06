# Finance Visual Analysis Skill

## Description

This Skill guides agents through financial visual analysis tasks, including chart interpretation, receipt processing, spreadsheet analysis, and portfolio calculations. It emphasizes precise data extraction, multi-step computation, and integration of visual evidence with external financial information.

## When to Use

Apply this Skill when the task involves:

- Reading and interpreting financial charts (candlesticks, line graphs, bar charts, volume indicators)
- Extracting data from receipts, invoices, or financial statements
- Analyzing spreadsheets containing financial metrics, performance data, or inventory
- Calculating returns, gains, losses, percentages, or price changes
- Comparing financial assets across time periods or categories
- Identifying temporal patterns, crossover points, or trend changes
- Combining visual financial data with external market information

## Strategy Overview

Financial visual tasks require precision above approximation. The general approach:

1. Parse the question to identify all required outputs (values, dates, calculations, comparisons)
2. Locate the relevant visual elements systematically (charts, tables, legends, axes)
3. Extract each required value, naming it before you look for it; zoom when a value is not confidently readable
4. Retrieve external data only when the task requires information not present in the image
5. Once all inputs are in hand, perform the whole computation chain in one calculation pass, showing intermediate steps
6. Cross-check the result against the visual evidence, and correct a specific identified error if the check fails

## Workflow

### 1. Understand the Task and Evidence Requirements

**Decompose the request into atomic requirements:**

- List each value to extract
- Identify each calculation to perform
- Note any comparisons or rankings required
- Determine whether external information is needed (e.g., "current price", "peak in a given year")

**Recognize financial domain concepts:**

- Chart types: candlestick (OHLC), line, bar, area, volume histogram
- Technical indicators: Bollinger Bands, support/resistance lines, moving averages
- Financial metrics: EBITDA, P/E ratio, expense ratio, market cap, volume
- Document types: receipts (with tax calculations), invoices, statements, spreadsheets
- Common calculations: percentage change, gain/loss, combined totals, year-over-year growth

**Determine temporal scope:**

- Identify whether the question concerns specific dates, months, quarters, or years
- Note whether trend analysis or period comparison is required
- Recognize phrases indicating "first time", "highest point", "earliest date"

### 2. Inspect and Localize Visual Evidence

**For charts:**

- Identify axis labels and scales (time on x-axis, price/value on y-axis)
- Locate the legend to map colors/lines to assets or data series
- Find relevant indicators (volume bars, technical overlays, horizontal lines)
- Determine the granularity (1-minute, daily, monthly candles)

**For tables and spreadsheets:**

- Identify column headers and row labels
- Note units (thousands, millions, percentages)
- Locate totals, subtotals, or summary rows
- Check for multiple tables or sections in the same image

**For receipts and invoices:**

- Locate item lists with descriptions, quantities, and prices
- Find tax amounts, discounts, and subtotals
- Identify the total amount and payment method
- Check for VAT/tax rates or exemptions
- Note date, location, and vendor information

**Extraction discipline:**

- Before looking, name the value you need and where it should live semantically (which row, column, axis label, legend entry, or document field). Semantic targets converge faster than directional guesses.
- Read the image at its given resolution first. If the named value is legible there, record it.
- Zoom when the value is not confidently readable: small or blurred text, overlapping series, ambiguous decimal points or currency symbols, dense legends, or individual candlestick OHLC levels.
- After each zoom, either record the value or state the specific obstacle that remains (wrong region, still too small, occlusion) and adjust the target accordingly.
- Once a value has been read clearly, retain and reuse it. Re-inspect only when the reading is ambiguous, conflicts with another observation, or a later result is implausible against the visual evidence.
- Distinguish extraction from derivation: totals, subtotals, tax lines, and final amounts that are printed and labeled in the source are extracted values, not quantities to be recomputed.

### 3. Select and Use Tools

**Sequence:**

1. Inspect image → zoom only for values not confidently readable → record all extracted values
2. If external data is required → web_search → visit → extract
3. Once all inputs are in hand → one code_interpreter pass for the full computation chain
4. Cross-check computed results against the original visual evidence

#### zoom

**When to use:** a named value is small, blurred, overlapping, or otherwise not confidently readable; ambiguous decimals or currency symbols; distinguishing close candlesticks or crowded legend entries.

**How to use:** state which value you are after and where it should be; zoom on that region; extract the now-visible value; if still unclear, describe the obstacle and re-target rather than sweeping the image.

**Avoid:** zooming without a specific target value in mind; magnifying past useful detail; re-zooming on a value you have already read clearly; using zoom in place of systematic inspection of axes, headers, and legends.

#### code_interpreter

**When to use:** any calculation beyond simple mental math — percentage changes, gains and losses, growth rates, multi-step arithmetic, aggregation across sources, tax and discount adjustments, date arithmetic, sorting, ranking, filtering.

**How to use:**

- Gather all extracted and retrieved inputs first, then run the complete chain in a single pass: input assignments, intermediate quantities, the final value, and the final rounding.
- Fix the rounding convention before computing (typically 2 decimals for currency) and apply it inside the same block. Do not defer rounding or formatting to a separate pass.
- Write clear Python with domain variable names, comments per step, and a print for every intermediate so the work is inspectable.
- Put consistency checks in the same block: for example, compare the sum of extracted components against the labeled total from the document, and print both.
- Start another calculation pass only when new information arrives (such as a search result) or when a cross-check has surfaced a specific error. Do not re-run a consistent computation to explore alternative precision libraries or rounding styles.

**Example pattern:**

```python
# Inputs extracted from the source
unit_price = ...      # from the item table
quantity = ...        # from the item table
labeled_total = ...   # printed on the document

# Derived quantities
line_total = unit_price * quantity
print("line total:", line_total)

# Consistency check against the printed value
print("matches labeled total:", round(line_total, 2) == round(labeled_total, 2))

# Final result, rounded once
final = round(line_total, 2)
print("final:", final)
```

#### web_search and visit

**When to use:** the task requires market, historical, or company data that is not present in the image (current prices, a period high or low, an IPO or listing date, exchange rates for comparison).

**How to use:** formulate a specific query naming the asset or entity, the period, and the venue if specified; visit the most authoritative result (official exchanges, established financial data providers); extract the exact value or date; then return to the main task.

**Avoid:** searching for information already visible in the image; using search in place of careful visual inspection; preferring informal sources over official financial data.

#### image_search

Rarely needed. Consider only for logo or vendor identification when zoom is insufficient, or to corroborate a named visual pattern. In most cases zoom and careful inspection suffice.

### 4. Integrate Evidence

**Combine visual and computed data:**

- Match extracted values to calculation inputs explicitly
- When comparing multiple assets, keep a clear mapping (ticker → color → values)
- Preserve units throughout (currency codes, %, physical units)
- Maintain precision: no premature rounding of intermediates; round once at the end

**Handle multi-source tasks:**

- Extract values from each source systematically and label the source
- Compute per-source intermediates and the combined result within the same calculation pass
- Keep each step labeled in the printed output

**Temporal integration:**

- When comparing periods, verify which periods the visual actually covers
- For "first time above X", scan chronologically from earliest to latest
- For "highest/lowest in period", restrict to the relevant date range
- When external data supplies historical context, align time scales before comparing

**Handle tax and discount calculations carefully:**

- If prices are tax-inclusive, reverse the tax: `price_before_tax = price_inclusive / (1 + tax_rate)`
- Separate tax-exempt items from taxable ones
- Verify whether a discount applies before or after tax
- Show each adjustment as its own printed step

### 5. Validate the Result

**Cross-check against the evidence:**

- Confirm extracted values are plausible given the chart scale or document layout
- Confirm computed magnitudes match the visual story (a large percentage gain should correspond to a large visual increase)
- Confirm identified dates align with x-axis labels
- Confirm consistency checks printed in the calculation pass agree with the labeled values in the source

**Check the arithmetic conditions:**

- Percentage change uses the correct base: `(new - old) / old * 100`
- Units are consistent throughout
- Signs are right (positive for gains, negative for losses)
- All multipliers are accounted for (contracts × units × price)

**When a check fails, diagnose before repeating work.** Name the cause — misread digit, wrong axis scale, wrong percentage base, unit mismatch, wrong series or color — then re-read or recompute only the affected part. When the checks agree, treat the result as settled and move to the answer.

**Cross-check multi-part answers:**

- Ensure every part of the question is answered
- Ensure related values are internally consistent
- If the question asks "which" and "how much", give both

### 6. Produce the Final Answer

**Structure it to match the question:**

- Address each sub-question in the order asked
- State extracted values before the calculations that use them
- Show the intermediate steps that led to the result
- Present the final numerical answer prominently

**Format numerical results:**

- Use consistent currency symbols or codes and explicit units
- Apply the rounding convention already fixed during calculation; avoid false precision from raw output
- Use conventional grouping for large numbers

**Provide complete context:**

- Name the assets, companies, or items involved
- Include relevant dates, periods, or timestamps
- Reference where each value came from (which chart, table, document, or external source)
- State any assumptions made

## Common Failure Modes / Watch Outs

**Precision:** approximating when an exact reading is available; rounding intermediates early; misreading decimal points.

**Units:** confusing thousands with millions on chart axes; mismatching currencies; mixing per-unit with total values.

**Temporal:** using the wrong period; confusing prior with current period; missing the correct date for a "first time" event; assuming dates without checking axis labels.

**Chart interpretation:** confusing bid/ask or open/close; misassigning a line to an asset via the legend; reading support as resistance; treating candlestick bodies as high-low.

**Calculation:** wrong percentage base; omitting the ×100; sign errors on gains versus losses; dropping a multiplier.

**Tax and discount:** wrong order of discount and tax; incorrect reversal of tax-inclusive prices; missing exempt items; confusing subtotal with total.

**Process:** re-reading values already extracted clearly instead of reusing them; recomputing amounts already printed and labeled in the source; splitting one computation chain across several passes; repeating a computation that already passed its cross-checks.

**Incompleteness:** answering only part of a multi-part question; showing calculations without stating the final answer; omitting required context such as dates, names, or units.

## Output Principles

- **Accuracy first:** extract precise values, verify against the visual evidence, and correct identified errors rather than guessing.
- **Transparency:** state formulas, print intermediates, make unit conversions explicit, and flag assumptions.
- **Completeness:** cover every requested identification, calculation, and comparison, with the context needed to interpret it.
- **Clarity:** structure multi-part answers, label sources consistently, and keep notation uniform.
- **Appropriate precision:** match the domain convention, show unrounded intermediates, and round once in the final answer.
