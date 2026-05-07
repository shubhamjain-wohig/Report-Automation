# Cost Analysis: Report Automation Tool

This document provides detailed cost breakdown for generating reports using the Report Automation Tool pipelines.

---

## Pricing Source

**Gemini 2.5 Flash** - [Google Cloud Pricing](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing#gemini-models-2.5)

| Type | Price (≤200K tokens) |
|------|----------------|
| Input (text, image, video) | $0.30 per million tokens |
| Cached input | $0.03 per million tokens |
| Audio input | $1.00 per million tokens |
| **Text output** | **$2.50 per million tokens** |

---

## Pipeline 1: SOW Report Agent (Task Tracker)

**Purpose:** Generate a Google Sheets Task Tracker from SOW document (PDF/DOCX).

### LLM Calls Breakdown

| Step | Agent/Function | Input Tokens | Output Tokens | Total Tokens |
|------|--------------|------------|--------------|-----------|
| 1 | SOWParserAgent | ~2,000 | ~200 | 2,200 |
| 2 | PlannerAgent | ~2,200 | ~500 | 2,700 |
| 3 | ExcelBuilderAgent | ~300 | ~200 | 500 |
| 4 | ReportSummaryAgent | ~500 | ~400 | 900 |
| **TOTAL** | **4 calls** | **~5,000** | **~1,300** | **~6,300** |

### Cost Breakdown

```
Input:  5,000 tokens × $0.30/million   = $0.00150
Output: 1,300 tokens × $2.50/million  = $0.00325
────────────────────────────────────────
TOTAL:                            = $0.00475
```

**Cost per Task Tracker: ~$0.0048 (~0.48 cents)**

---

## Pipeline 2: Report Generator (Weekly Report)

**Purpose:** Generate Google Slides weekly report from Excel file with timeline screenshot.

### LLM Calls Breakdown

| Step | Agent/Function | Input Tokens | Output Tokens | Total Tokens |
|------|--------------|------------|--------------|-----------|
| 1 | Executive Summary (LLM) | ~300 | ~100 | 400 |
| 2 | Slide Fields Populate | ~500 | ~400 | 900 |
| 3 | Slide 2 Fill | ~800 | ~600 | 1,400 |
| 4 | Heading Generation | ~400 | ~300 | 700 |
| 5 | ExcelReaderAgent | ~1,500 | ~200 | 1,700 |
| 6 | ScreenshotAgent | ~200 | ~100 | 300 |
| 7 | SlidesBuilderAgent | ~800 | ~300 | 1,100 |
| 8 | CleanupAgent | ~300 | ~200 | 500 |
| **TOTAL** | **8 calls** | **~5,800** | **~2,200** | **~8,000** |

### Cost Breakdown

```
Input:  5,800 tokens × $0.30/million   = $0.00174
Output: 2,200 tokens × $2.50/million = $0.00550
─────────────────────────────────────────
TOTAL:                             = $0.00724
```

**Cost per Weekly Report: ~$0.0072 (~0.72 cents)**

---

## Google APIs Cost

### Per Sheet Generation

| Operation | API Calls | Google's Free Tier |
|-----------|----------|------------------|
| Create spreadsheet | 1 | 1,000/day (Drive) |
| Get metadata | 1 | 100/day (Sheets) |
| Write data | 1 | 100/day (Sheets) |
| Format sheet | 1 | 100/day (Sheets) |
| Share (optional) | 1 | 1,000/day (Drive) |
| **Total** | **~6 calls** | |

**Google APIs cost: $0** (within free tier)

---

## Summary Comparison

| Pipeline | LLM Calls | Total Tokens | LLM Cost | APIs Cost | Total Cost |
|----------|----------|--------------|----------|----------|-----------|
| Task Tracker | 4 | 6,300 | $0.0048 | $0 | $0.0048 |
| Weekly Report | 8 | 8,000 | $0.0072 | $0 | $0.0072 |

### Cost per Dollar

| Pipeline | Reports per $1 |
|----------|---------------|
| Task Tracker | ~208 |
| Weekly Report | ~139 |

---

## Notes

- Token counts are **estimates** based on typical SOW/report sizes
- Actual token usage may vary based on:
  - SOW document length
  - Number of tasks extracted
  - Timeline size
  - Placeholder count
- Prices are for **Gemini 2.5 Flash** (default model)
- For Gemini 2.5 Pro: multiply costs by ~5x
- Google Sheets/Drive APIs are free within standard quotas

---

*Last updated: May 2026*