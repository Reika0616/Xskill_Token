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
3. Extract exact values using zoom when precision is critical
4. Perform calculations explicitly, showing intermediate steps
5. Validate results against the visual evidence
6. Use external sources only when current or non-visible data is required

## Workflow

### 1. Understand the Task and Evidence Requirements

**Decompose the request into atomic requirements:**

- List each value to extract
- Identify each calculation to perform
- Note any comparisons or rankings required
- Determine if external information is needed (e.g., "current price", "peak in 2024")

**Recognize financial domain concepts:**

- Chart types: candlestick (OHLC), line, bar, area, volume histogram
- Technical indicators: Bollinger Bands, support/resistance lines, moving averages
- Financial metrics: EBITDA, P/E ratio, expense ratio, market cap, volume
- Document types: receipts (with tax calculations), invoices, statements, spreadsheets
- Common calculations: percentage change, gain/loss, combined totals, year-over-year growth

**Determine temporal scope:**

- Identify if the question asks about specific dates, months, quarters, or years
- Note if trend analysis or period comparison is required
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

- Locate item lists with descriptions and prices
- Find tax amounts, discounts, and subtotals
- Identify the total amount and payment method
- Check for VAT/tax rates or exemptions
- Note date, location, and vendor information

**Use zoom strategically:**

- When exact numerical values are small or unclear
- To read specific candlestick OHLC values
- To distinguish overlapping lines on busy charts
- To verify decimal places or currency symbols
- To read legends or labels in dense visualizations

### 3. Select and Use Tools

**zoom:**

- Call when initial inspection reveals small text, overlapping elements, or ambiguous values
- Target the specific region containing the required data point
- Re-zoom if the first magnification is insufficient
- Use to verify critical values before calculations

**code_interpreter:**

- Use for all multi-step arithmetic (percentage calculations, gains/losses, totals)
- Show work explicitly: state the formula, substitute values, compute result
- Use when aggregating data from multiple sources (e.g., summing items across receipts)
- Employ for date arithmetic, period calculations, or temporal aggregations
- Leverage for data transformations (e.g., removing tax from tax-inclusive prices)
- Use Python for complex logic (filtering, sorting, ranking)

**web_search and visit:**

- Search when the task requires external market data not visible in the image
  - Example: "What was the peak price of GBP/EUR in May 2025?"
  - Example: "What was BTC's lowest price on ByBit in 2022?"
- Search for company information when only a ticker symbol is visible
  - Example: "When did Tesla (TSLA) start trading on the stock exchange?"
- Visit the most relevant result to extract specific values or dates
- Cross-reference found information with visual data

**image_search:**

- Use sparingly; most finance tasks provide necessary visual information
- May help identify logos to determine company/vendor names
- Can verify visual patterns (e.g., "head and shoulders" chart formation)

**Tool sequencing:**

1. Inspect image → zoom if needed → extract values
2. If external data required → web_search → visit → extract
3. Once all values obtained → code_interpreter for calculations
4. Validate computed results against original visual evidence

### 4. Integrate Evidence

**Combine visual and computed data:**

- Match extracted chart values to calculation inputs explicitly
- When comparing multiple assets, create a clear mapping (ticker → color → values)
- Preserve units throughout calculations (USD, USDT, GBP, EUR, %, tonnes)
- Maintain precision (avoid premature rounding; round only in final answer)

**Handle multi-source tasks:**

- Extract values from each source systematically (Receipt 1, Receipt 2, Chart 1, Table 1)
- Perform intermediate calculations for each source
- Combine intermediate results for the final answer
- Label each step clearly

**Temporal integration:**

- When comparing "previous year" vs "current year", verify which periods the visual shows
- For "first time above X", scan chronologically from left to right
- For "highest/lowest in period", consider only the relevant date range
- When external data provides historical context, align time scales correctly

**Handle tax and discount calculations carefully:**

- If prices are tax-inclusive, reverse the tax: `price_before_tax = price_inclusive / (1 + tax_rate)`
- If items are tax-exempt but others aren't, separate the calculations
- For discounts: verify whether discount applies before or after tax
- Show each adjustment step explicitly

### 5. Validate the Result

**Check against visual evidence:**

- Verify extracted values are plausible given chart scale
- Confirm calculations match the visual magnitude (a 700% gain should show a large visual increase)
- Ensure identified dates align with x-axis labels
- Re-inspect if computed result seems inconsistent with the chart

**Validate calculations:**

- Recalculate using a different method if possible
- Check units are consistent throughout
- Verify percentage calculations: `(new - old) / old * 100%`
- Confirm gain/loss signs (positive for profit, negative for loss)

**Cross-check multi-part answers:**

- Ensure all parts of the question are answered
- Verify that related values are internally consistent
- If the question asks for "which" and "how much", provide both

**Common error patterns to watch:**

- Misreading axis scales (thousands vs millions)
- Confusing bid/ask prices or open/close values
- Using wrong base for percentage calculations
- Forgetting to account for multiple units (contracts × shares × price)
- Misidentifying colors in legends

### 6. Produce the Final Answer

**Structure the answer to match the question:**

- If multiple questions are asked, address each in order
- State extracted values before using them in calculations
- Show intermediate calculation steps for transparency
- Present final numerical answers with appropriate precision

**Format numerical results:**

- Use consistent currency symbols (USD, £, ₹, ₱, USDT)
- Include appropriate units (%, tonnes, contracts)
- Round to reasonable precision (typically 2 decimal places for money, whole numbers for percentages unless greater precision is needed)
- Use commas or spaces for large numbers where conventional

**Provide complete context:**

- Name the assets, companies, or items being discussed
- Include relevant dates, periods, or timestamps
- Reference the source of values ("from the chart", "from Receipt 2", "from ByBit data")
- Clarify any assumptions made

## Tool Guidance

### zoom

**When to use:**
- Small text on receipts or invoices
- Precise values on chart axes or data points
- Distinguishing close candlesticks or overlapping lines
- Reading legend entries in crowded charts
- Verifying decimal places or small digits

**How to use:**
- Identify the region containing the target information
- Request zoom on that specific area
- Extract the now-visible precise values
- Zoom again if the target is still unclear

**Avoid:**
- Zooming without a clear target value in mind
- Over-zooming beyond useful detail
- Using zoom as a substitute for systematic inspection

### code_interpreter

**When to use:**
- Any calculation beyond simple mental math
- Percentage changes, gains, losses, growth rates
- Multi-step arithmetic with intermediate values
- Aggregating data from multiple sources
- Tax calculations, discount applications
- Date arithmetic or period counting
- Sorting, ranking, or filtering operations

**How to use:**
- Write clear Python code with variable names matching the domain
- Show the formula before substituting values
- Print intermediate results for verification
- Use comments to explain each calculation step
- Store results in clearly named variables
- Use appropriate data structures (lists for items, dictionaries for mappings)

**Example pattern:**
```python
# Extract values
price_2024 = 108374.80
price_current = 123260.20

# Calculate gain
gain = price_current - price_2024
percentage_gain = (gain / price_2024) * 100

print(f"Gain: {gain} USDT ({percentage_gain:.2f}%)")
```

### web_search and visit

**When to use:**
- The task explicitly requests current/recent data not in the image
- Historical data is required that isn't visible (e.g., "2022 lowest price")
- Company information when only a ticker is shown
- Exchange rates or market data for comparison
- Background information (e.g., "when did company X go public?")

**Search query patterns:**
- For historical prices: `"[Asset] price [date/period] [exchange if specified]"`
- For company info: `"[Company name or ticker] IPO date"` or `"[ticker] stock exchange listing"`
- For exchange rates: `"[Currency pair] peak [month year]"`

**How to use:**
- Formulate specific search queries
- Visit the most authoritative result (official exchanges, financial data providers)
- Extract the exact value or date required
- Return to the main task with the retrieved information

**Avoid:**
- Searching for information that's already visible in the image
- Using search as a substitute for careful visual inspection
- Trusting informal sources over official financial data providers

### image_search

**Rarely needed for finance tasks.** 

Consider only when:
- Logo identification is required and zoom is insufficient
- Visual pattern verification might help (e.g., confirming a technical pattern)
- Vendor or company identification from branding

In most cases, zoom and careful inspection are sufficient.

## Common Failure Modes / Watch Outs

**Precision errors:**
- Approximating values when exact reading is required
- Rounding intermediate calculations too early
- Misreading decimal points (60.28 vs 6.028)

**Unit confusion:**
- Confusing thousands with millions in charts (200 × 10k RMB = 2 million)
- Mismatching currencies (USD vs USDT vs GBP)
- Forgetting to account for per-unit vs total values

**Temporal errors:**
- Using data from the wrong time period
- Confusing "previous year" with "current year"
- Not identifying the correct date for "first time" events
- Assuming chart dates without checking axis labels

**Chart interpretation errors:**
- Confusing bid/ask or open/close prices
- Misidentifying which line corresponds to which asset
- Reading support as resistance or vice versa
- Ignoring that candlestick bodies represent open-close, not high-low

**Calculation errors:**
- Using wrong base for percentage: `(new - old) / new` instead of `/ old`
- Forgetting the 100 multiplier for percentages
- Sign errors in gains vs losses
- Not accounting for multiple multipliers (contracts × shares × price)

**Tax and discount errors:**
- Applying discounts in the wrong order (before/after tax)
- Not reversing tax from tax-inclusive prices correctly
- Missing VAT-exempt items
- Forgetting that some receipts show subtotals vs totals

**Incomplete answers:**
- Answering only part of a multi-part question
- Providing calculations without stating the final answer
- Missing required context (dates, asset names, units)

## Output Principles

**Accuracy over speed:**
- Take time to extract precise values
- Double-check calculations
- Verify results against visual evidence

**Transparency in calculations:**
- Show intermediate steps
- State formulas before computing
- Make unit conversions explicit
- Explain any assumptions

**Completeness:**
- Address every part of the question
- Provide all requested identifications, calculations, and comparisons
- Include relevant context (dates, names, units)

**Clarity:**
- Structure multi-part answers clearly
- Use consistent notation and terminology
- Label different sources (Chart 1, Receipt 2)
- Present final answers prominently

**Appropriate precision:**
- Match precision to the domain (2 decimals for currency, whole numbers for counts)
- Avoid false precision from calculator output
- Round final answers sensibly while showing unrounded intermediates
