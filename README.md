# Enterprise Risk Command Center - Complete Technical Documentation

## From PDF Upload to Risk Intelligence: End-to-End Pipeline Guide

---

# Table of Contents

1. [Project Overview & Scope](#1-project-overview--scope)
2. [Use Cases](#2-use-cases)
3. [Architecture Overview - Medallion Pattern](#3-architecture-overview---medallion-pattern)
4. [Stage 1: PDF Upload to Snowflake Internal Stage](#4-stage-1-pdf-upload-to-snowflake-internal-stage)
5. [Stage 2: Document Registration (Bronze Layer)](#5-stage-2-document-registration-bronze-layer)
6. [Stage 3: Document Parsing with AI_PARSE_DOCUMENT](#6-stage-3-document-parsing-with-ai_parse_document)
7. [Stage 4: Chunking - How a PDF is Divided into Chunks](#7-stage-4-chunking---how-a-pdf-is-divided-into-chunks)
8. [Stage 5: Vector Embedding Generation](#8-stage-5-vector-embedding-generation)
9. [Stage 6: Knowledge Graph Extraction with AI_COMPLETE](#9-stage-6-knowledge-graph-extraction-with-ai_complete)
10. [Stage 7: Gold Layer - Business Intelligence Tables](#10-stage-7-gold-layer---business-intelligence-tables)
11. [Complete Pipeline Orchestration](#11-complete-pipeline-orchestration)
12. [Real-World Example: Walking Through a PDF](#12-real-world-example-walking-through-a-pdf)
13. [SQL Reference - Key Queries](#13-sql-reference---key-queries)
14. [Streamlit Application](#14-streamlit-application)
15. [Troubleshooting & Maintenance](#15-troubleshooting--maintenance)

---

# 1. Project Overview & Scope

## What is the Enterprise Risk Command Center?

The **Enterprise Risk Command Center** is a Snowflake-native intelligent document processing platform that transforms unstructured documents (PDFs, contracts, invoices, safety reports, emails) into structured, queryable risk intelligence using Snowflake's Cortex AI capabilities.

## Project Scope

| Attribute | Detail |
|-----------|--------|
| **Database** | `RISK_COMMAND_CENTER` |
| **Platform** | Snowflake (Snowsight + Cortex AI) |
| **Architecture** | Medallion (Bronze → Silver → Gold) |
| **AI Engine** | Snowflake Cortex (PARSE_DOCUMENT, AI_COMPLETE, EMBED_TEXT) |
| **Presentation** | Streamlit in Snowflake |
| **Automation** | Stored Procedures + Snowflake Tasks (5-min cadence) |
| **Domain** | Construction Risk Management (extensible to Healthcare, Finance) |

## Schemas in the Database

```
RISK_COMMAND_CENTER
├── BRONZE      -- Raw ingestion (stage, document registry, parse results)
├── SILVER      -- Processed data (chunks, vectors, graph nodes/edges, domain tables)
├── GOLD        -- Analytics-ready (risk matrix, financial summary, vendor scorecard)
├── AI          -- AI model configurations
├── KNOWLEDGE   -- Cortex Search / knowledge base
├── OPS         -- Stored procedures, tasks, pipeline orchestration
├── GOVERNANCE  -- Data quality, lineage tracking
└── STREAMLIT   -- App deployment stage
```

## Key Technologies Used

- **SNOWFLAKE.CORTEX.PARSE_DOCUMENT** - Converts PDF/images to structured text (OCR + layout detection)
- **SNOWFLAKE.CORTEX.AI_COMPLETE** - LLM-powered entity extraction & relationship mapping
- **SNOWFLAKE.CORTEX.EMBED_TEXT_1024** - Generates 1024-dimension vector embeddings for semantic search
- **LATERAL FLATTEN + SPLIT** - Splits parsed text into logical chunks
- **CEIL()** - Calculates page number assignment for chunks
- **Dynamic Tables** - Auto-refreshing Gold layer views

---

# 2. Use Cases

## Primary Use Cases

### 2.1 Construction Project Risk Management
- Upload monthly status reports, change orders, contracts, invoices
- Automatically extract risks, financial exposures, schedule impacts
- Generate unified risk matrices across multiple projects

### 2.2 Vendor Performance Monitoring
- Parse vendor contracts and invoices
- Build composite vendor scorecards (insurance status, risk rating, billing)
- Identify high-risk vendors with expired insurance or poor performance

### 2.3 Safety Compliance & Incident Tracking
- Extract safety incidents from site reports
- Correlate incidents with project locations and superintendents
- Monitor OSHA compliance metrics

### 2.4 Financial Forecasting
- Parse invoices, billing records, change orders
- Track budget utilization vs. forecast cost at completion
- Identify cost overruns early through pattern detection

### 2.5 Knowledge Graph-Powered Q&A (CoCo Assistant)
- Build a knowledge graph of entities (Projects, Vendors, Risks, People)
- Enable natural language questions over unstructured documents
- Vector-similarity search for context retrieval (RAG pattern)

### 2.6 Multi-Domain Extensibility
- Switch between Construction, Healthcare, Finance domains
- Domain-specific extraction prompts and entity types
- Configurable through `SILVER.DOMAIN_CONFIG` table

---

# 3. Architecture Overview - Medallion Pattern

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENTERPRISE RISK COMMAND CENTER                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────┐     ┌───────────────┐     ┌────────────────────────────┐    │
│  │  UPLOAD   │────▶│  BRONZE LAYER │────▶│        SILVER LAYER        │    │
│  │           │     │               │     │                            │    │
│  │ • PDF     │     │ • Stage       │     │ • CHUNKS (text segments)   │    │
│  │ • DOCX    │     │ • Doc Registry│     │ • VECTORS (embeddings)     │    │
│  │ • CSV     │     │ • Parse Result│     │ • GRAPH_NODES (entities)   │    │
│  │ • Email   │     │               │     │ • GRAPH_EDGES (relations)  │    │
│  │ • TXT     │     │               │     │ • PROJECTS, RISKS, etc.    │    │
│  └───────────┘     └───────────────┘     └────────────┬───────────────┘    │
│                                                        │                    │
│                                                        ▼                    │
│                    ┌──────────────────────────────────────────────────┐     │
│                    │                 GOLD LAYER                        │     │
│                    │                                                   │     │
│                    │  • PROJECT_RISK_SUMMARY    • VENDOR_SCORECARD     │     │
│                    │  • UNIFIED_RISK_MATRIX     • SAFETY_DASHBOARD     │     │
│                    │  • FINANCIAL_SUMMARY       • VW_GRAPH_EXPLORER    │     │
│                    │  • VW_RISK_HEATMAP (Dynamic Tables)               │     │
│                    └──────────────────────┬───────────────────────────┘     │
│                                           │                                 │
│                                           ▼                                 │
│                    ┌──────────────────────────────────────────────────┐     │
│                    │           STREAMLIT APPLICATION                   │     │
│                    │                                                   │     │
│                    │  • Executive Dashboard   • CoCo AI Assistant      │     │
│                    │  • Risk Heatmap          • Report Generator       │     │
│                    │  • Financial Calculator  • Evidence Viewer        │     │
│                    └──────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Summary

```
PDF File  →  Internal Stage  →  DOCUMENT_REGISTRY  →  PARSE_DOCUMENT()
                                                              │
                                                              ▼
                                                      DOC_PARSE_RESULTS
                                                              │
                                                   SPLIT + CEIL (chunking)
                                                              │
                                                              ▼
                                                          CHUNKS
                                                         /       \
                                                        /         \
                                               VECTORS           GRAPH_NODES
                                           (embeddings)         GRAPH_EDGES
                                                        \         /
                                                         \       /
                                                     GOLD LAYER TABLES
```

---

# 4. Stage 1: PDF Upload to Snowflake Internal Stage

## What Happens

The first step is uploading your PDF (or any document) to a Snowflake **Internal Stage**. This is where Snowflake stores the raw file bytes before any processing begins.

## The Internal Stage

```sql
-- This stage was created with directory listing enabled
CREATE OR REPLACE STAGE RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE
    DIRECTORY = (ENABLE = TRUE);
```

The `DIRECTORY = (ENABLE = TRUE)` option allows Snowflake to list files and their metadata (size, last modified date).

## How to Upload

### Method 1: Snowsight UI
Navigate to Data → Databases → RISK_COMMAND_CENTER → BRONZE → Stages → RAW_INTERNAL_STAGE → Upload files via the UI.

### Method 2: PUT Command (SnowSQL / Worksheet)
```sql
PUT file:///local/path/to/Monthly_Status_Report_PRJ-001_June2026.pdf
    @RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE/upload/
    AUTO_COMPRESS = FALSE
    OVERWRITE = TRUE;
```

### Method 3: Streamlit App (Built-in Upload)
The Risk Command Center Streamlit app has an Admin Panel with a file upload widget that handles the PUT + registration automatically.

## What the Stage Looks Like After Upload

```sql
LIST @RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE;
```

**Result:**

| name | size | md5 | last_modified |
|------|------|-----|---------------|
| raw_internal_stage/upload/Monthly_Status_Report_PRJ-001_June2026.pdf | 12,788 | 560343970d70c58e... | Mon, 3 Aug 2026 |
| raw_internal_stage/upload/construction_risk_anomaly_test.pdf | 6,754 | fcae6c87636d6560... | Wed, 12 Aug 2026 |
| raw_internal_stage/upload/Change_Order_Request_CO-PRJ001-003.pdf | 2,834 | 89d5f344df25da50... | Sun, 2 Aug 2026 |
| raw_internal_stage/upload/Invoice_Package_INV-PRJ001-STEEL-006.pdf | 3,019 | 1e5fb42015f014f4... | Sun, 2 Aug 2026 |
| raw_internal_stage/upload/vendors.csv | 3,978 | 745067ef38d73093... | Sun, 2 Aug 2026 |
| raw_internal_stage/upload/mv_cable_chain_01.eml | 1,314 | 3322f52551b2724a... | Sun, 2 Aug 2026 |

At this point, the file is just binary data sitting in cloud storage. No parsing has happened yet.

---

# 5. Stage 2: Document Registration (Bronze Layer)

## What Happens

When a file is uploaded (either via Streamlit or manually), a record is inserted into the **DOCUMENT_REGISTRY** table. This table is the "intake desk" — it knows what files exist and tracks their processing status.

## Table Schema

```sql
CREATE OR REPLACE TABLE RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY (
    DOCUMENT_ID   VARCHAR NOT NULL,     -- Unique ID (e.g., 'DOC-4304273BEB484582')
    FILE_NAME     VARCHAR,              -- Original filename
    FILE_PATH     VARCHAR,              -- Path within the stage
    FILE_SIZE     NUMBER(38,0),         -- File size in bytes
    FILE_TYPE     VARCHAR,              -- Extension (pdf, csv, eml, txt)
    STATUS        VARCHAR DEFAULT 'UPLOADED',  -- UPLOADED → PARSED → FAILED
    UPLOADED_AT   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (DOCUMENT_ID)
);
```

## Status Lifecycle

```
UPLOADED  →  PARSED       (successfully processed)
UPLOADED  →  FAILED       (error during parsing, will be retried)
UPLOADED  →  UNSUPPORTED  (file type not supported)
```

## Real Data Example

After uploading `Monthly_Status_Report_PRJ-001_June2026.pdf`, the registry looks like:

| DOCUMENT_ID | FILE_NAME | FILE_PATH | FILE_SIZE | FILE_TYPE | STATUS | UPLOADED_AT |
|-------------|-----------|-----------|-----------|-----------|--------|-------------|
| DOC-4304273BEB484582 | Monthly_Status_Report_PRJ-001_June2026.pdf | upload/Monthly_Status_Report_PRJ-001_June2026.pdf | 12,788 | pdf | PARSED | 2026-08-03 06:19:27 |
| DOC-46891B3FE25B4915 | construction_risk_anomaly_test.pdf | upload/construction_risk_anomaly_test.pdf | 6,754 | pdf | PARSED | 2026-08-12 00:33:17 |

## SQL to Check Registration Status

```sql
SELECT DOCUMENT_ID, FILE_NAME, FILE_PATH, STATUS
FROM RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY
ORDER BY UPLOADED_AT DESC;
```

---

# 6. Stage 3: Document Parsing with AI_PARSE_DOCUMENT

## What Happens

This is where the magic begins. The stored procedure `SP_PROCESS_BRONZE_TO_SILVER` picks up all documents with `STATUS = 'UPLOADED'` and calls **SNOWFLAKE.CORTEX.PARSE_DOCUMENT** to convert the raw PDF binary into structured text.

## How PARSE_DOCUMENT Works

`PARSE_DOCUMENT` is Snowflake's built-in Cortex AI function that:
1. Takes a file reference from a stage
2. Applies OCR (Optical Character Recognition) and layout detection
3. Returns a JSON string containing the full text content with structure preserved (headers, tables as markdown, paragraphs)

## The Core SQL Call

```sql
SELECT SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
    '@RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE',   -- Stage reference
    'upload/Monthly_Status_Report_PRJ-001_June2026.pdf', -- File path within stage
    {'mode': 'LAYOUT'}                                   -- Mode: LAYOUT preserves structure
) AS parsed_output;
```

### Parameters Explained

| Parameter | Value | Meaning |
|-----------|-------|---------|
| Stage path | `@RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE` | Where the file lives |
| File path | `upload/Monthly_Status_Report_PRJ-001_June2026.pdf` | Relative path inside the stage |
| Mode | `'LAYOUT'` | Preserves document layout (headings, tables as markdown, paragraphs). Alternative: `'OCR'` for pure text extraction |

## What PARSE_DOCUMENT Returns

The function returns a JSON string. Here is what the output looks like for our sample PDF:

```json
{
  "content": "Coco Constructions\nConstruction Lifecycle Record | Internal\n\n# Monthly Status Report - PRJ-001 June 2026\n\n## 1. Executive Status Snapshot\n\n|  Project ID | PRJ-001  |\n| --- | --- |\n|  Project Name | Project Phoenix Medical Tower  |\n|  Contract Value | $10,225,000  |\n|  Percent Complete | 76.8% task average  |\n|  Forecast Final Cost | $10,334,099  |\n...",
  "pages": 2
}
```

**Key insight:** The PDF has been converted from an unstructured binary blob into structured markdown-like text. Tables become pipe-delimited markdown tables. Headers become `#` and `##` markers.

## Where the Result is Stored

The parsed output goes into the `DOC_PARSE_RESULTS` table:

```sql
CREATE OR REPLACE TABLE RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS (
    PARSE_ID      VARCHAR DEFAULT UUID_STRING(),  -- Auto-generated UUID
    DOCUMENT_ID   VARCHAR,                        -- Links to DOCUMENT_REGISTRY
    RAW_TEXT      VARCHAR,                        -- The full parsed text (up to 50,000 chars)
    PARSED_JSON   VARIANT,                        -- The full JSON response from PARSE_DOCUMENT
    STATUS        VARCHAR,                        -- SUCCESS or FAILED
    CREATED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

## Real Data - DOC_PARSE_RESULTS After Parsing

| PARSE_ID | DOCUMENT_ID | RAW_TEXT (first 150 chars) | STATUS | CREATED_AT |
|----------|-------------|---------------------------|--------|------------|
| 7885437c-7b49-... | DOC-4304273BEB484582 | `{"content":"Coco Constructions\nConstruction Lifecycle Record \| Internal\n\n# Monthly Status Report - PRJ-001 June 2026\n\n## 1. Executive Status Snap...` | SUCCESS | 2026-08-03 06:19:43 |
| 548367d7-6c78-... | DOC-46891B3FE25B4915 | `{"content":"# Construction Risk Intelligence - Test Document\n\nSynthetic project record designed to test PDF extraction, risk scoring, anomaly detect...` | SUCCESS | 2026-08-16 23:11:51 |

## Supported File Types

The procedure handles multiple file types:

| File Type | Method | Notes |
|-----------|--------|-------|
| **pdf, docx, pptx, txt, html, png, jpg, tiff** | `PARSE_DOCUMENT()` | Full AI parsing with layout detection |
| **csv** | Direct byte read | Reads as text, chunks by row batches |
| **eml, msg** | Python `email` library | Extracts headers + body from emails |
| **json, xml, log** | Direct byte read | Reads as plain text |

---

# 7. Stage 4: Chunking - How a PDF is Divided into Chunks

## Why Chunking?

A single PDF can be thousands of words long. LLMs have token limits, and vector embeddings work best on focused, semantically coherent text segments. **Chunking** splits the parsed document into smaller, meaningful pieces.

## The Chunking Strategy

This project uses **section-based chunking**: the parsed text is split at heading markers (`# `) to create logically coherent chunks. Each chunk represents one section of the document.

## The Core Chunking SQL

```sql
INSERT INTO RISK_COMMAND_CENTER.SILVER.CHUNKS
    (CHUNK_ID, DOCUMENT_ID, CHUNK_INDEX, CHUNK_TEXT, PAGE_NUMBER, DOMAIN)
SELECT
    'CHK-' || UPPER(SUBSTR(MD5('{doc_id}' || '-' || f.INDEX::STRING), 1, 12)),
    '{doc_id}',
    f.INDEX,
    TRIM(f.VALUE::STRING),
    GREATEST(1, CEIL(f.INDEX / 3.0)),   -- ◄── Page number estimation using CEIL
    '{domain}'
FROM RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS d,
LATERAL FLATTEN(input => SPLIT(
    COALESCE(d.PARSED_JSON:content::STRING, d.RAW_TEXT),
    CHR(10) || '# '   -- Split on newline followed by markdown heading marker
)) f
WHERE d.DOCUMENT_ID = '{doc_id}'
  AND LENGTH(TRIM(f.VALUE::STRING)) > 50;  -- Filter out tiny fragments
```

## Breaking Down the Chunking Logic

### Step 1: SPLIT - Divide text at section boundaries

```sql
SPLIT(d.PARSED_JSON:content::STRING, CHR(10) || '# ')
```

This splits the full document text every time it encounters a line break followed by `# ` (a markdown heading). Each resulting segment is one logical section.

**Example:** If the parsed text is:
```
# Monthly Status Report - PRJ-001 June 2026
## 1. Executive Status Snapshot
| Project ID | PRJ-001 |
...
# 5. Manpower, Safety and Quality Evidence
| work_date | trade | worker_count |
...
# 6. Top Risk Events and Actions
| risk_id | risk_category |
...
```

After SPLIT on `\n# `, you get 3 chunks.

### Step 2: LATERAL FLATTEN - Convert array to rows

```sql
LATERAL FLATTEN(input => SPLIT(...)) f
```

`FLATTEN` converts the array of text segments into individual rows. Each row gets an `INDEX` (0, 1, 2, 3...) and a `VALUE` (the text content).

### Step 3: CEIL - Calculate page number

```sql
GREATEST(1, CEIL(f.INDEX / 3.0))
```

Since PARSE_DOCUMENT in LAYOUT mode doesn't always give per-chunk page numbers, we **estimate** which page a chunk belongs to by assuming roughly 3 sections per page:

| Chunk Index | CEIL(INDEX / 3.0) | Estimated Page |
|-------------|-------------------|----------------|
| 0 | CEIL(0/3) = 0 → GREATEST(1,0) = **1** | Page 1 |
| 1 | CEIL(1/3) = 1 → **1** | Page 1 |
| 2 | CEIL(2/3) = 1 → **1** | Page 1 |
| 3 | CEIL(3/3) = 1 → **1** | Page 1 |
| 4 | CEIL(4/3) = 2 → **2** | Page 2 |
| 5 | CEIL(5/3) = 2 → **2** | Page 2 |

**The CEIL function rounds UP to the nearest integer**, ensuring every chunk gets assigned to at least page 1.

### Step 4: MD5 Hash - Generate unique CHUNK_ID

```sql
'CHK-' || UPPER(SUBSTR(MD5('{doc_id}' || '-' || f.INDEX::STRING), 1, 12))
```

Creates a deterministic, unique ID per chunk by hashing the document ID + chunk index. Example result: `CHK-E69D41FDD4E3`

### Step 5: Filter small fragments

```sql
WHERE LENGTH(TRIM(f.VALUE::STRING)) > 50
```

Chunks with fewer than 50 characters are noise (empty sections, page breaks) and are filtered out.

## CSV Chunking (Different Strategy)

For CSV files, chunking is done by **row batches** instead of section headers:

```sql
-- Chunk by 20-row batches
BATCH = 20
for idx in range(0, len(data_rows), BATCH):
    batch = data_rows[idx:idx + BATCH]
    chunk_txt = header + '\n' + '\n'.join(batch)  -- Header + 20 rows
```

Each CSV chunk = the header row + 20 data rows. This ensures each chunk has column context.

## CHUNKS Table Schema

```sql
CREATE OR REPLACE TABLE RISK_COMMAND_CENTER.SILVER.CHUNKS (
    CHUNK_ID     VARCHAR NOT NULL,       -- 'CHK-E69D41FDD4E3'
    DOCUMENT_ID  VARCHAR,                -- Links to DOCUMENT_REGISTRY
    CHUNK_INDEX  NUMBER(38,0),           -- 0, 1, 2, 3... (order within document)
    CHUNK_TEXT   VARCHAR,                -- The actual text content
    PAGE_NUMBER  NUMBER(38,0),           -- Estimated page (via CEIL)
    CREATED_AT   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (CHUNK_ID)
);
```

## Real Data - CHUNKS Table After Processing

**Document:** `Monthly_Status_Report_PRJ-001_June2026.pdf` (DOC-4304273BEB484582)

This 12KB PDF was split into **4 chunks**:

| CHUNK_ID | CHUNK_INDEX | PAGE_NUMBER | CHUNK_TEXT (first 200 chars) |
|----------|-------------|-------------|------------------------------|
| (auto) | 0 | 1 | `Coco Constructions\nConstruction Lifecycle Record \| Internal\n` |
| (auto) | 1 | 1 | `Monthly Status Report - PRJ-001 June 2026\n\n## 1. Executive Status Snapshot\n\n\| Project ID \| PRJ-001 \|\n\| --- \| --- \|\n\| Project Name \| Project Phoenix Medical Tower \|\n\| Contract Value \| $10,225,000 \|...` |
| (auto) | 2 | 1 | `5. Manpower, Safety and Quality Evidence\n\n\| work_date \| trade \| worker_count \| total_labor_hours \| overtime_hours \|\n\| --- \| --- \| --- \| --- \| --- \|\n\| 2026-06-01 \| Electrical \| 14 \| 147 \| 35 \|...` |
| (auto) | 3 | 1 | `6. Top Risk Events and Actions\n\n\| risk_id \| risk_category \| risk_title \| severity \| risk_score \| schedule_impact_days \| direct_cost_exposure \| recommended_action \|\n...` |

**Document:** `construction_risk_anomaly_test.pdf` (DOC-46891B3FE25B4915)

This 6.7KB PDF was split into **5 chunks**:

| CHUNK_ID | CHUNK_INDEX | PAGE | CHUNK_TEXT (first 150 chars) |
|----------|-------------|------|------------------------------|
| CHK-FFDD1D3F588B | 0 | 1 | `# Construction Risk Intelligence - Test Document\n\nSynthetic project record designed to test PDF extraction, risk scoring...` |
| CHK-7F14AE8586D8 | 1 | 1 | `1. Weekly Site Risk & Performance Records\n\n\| Date \| Zone \| Work Item \| Progress % \| Planned % \| Delay Days...` |
| CHK-58625C7F1336 | 2 | 1 | `2. Material, Equipment & Safety Observations\n\n\| Record ID \| Date \| Category \| Observation \| Expected/Normal Range...` |
| CHK-E69D41FDD4E3 | 3 | 1 | `3. Risk Register\n\n\| Risk ID \| Risk \| Probability \| Impact \| Risk Score \| Owner \| Mitigation Status \|...` |
| CHK-EF02AD983E35 | 4 | 2 | `4. Incident Notes\n\n\| INC-101 \| 10-Aug \| Tower C \| Worker slipped near wet slab area; no lost-time injury...` |

## Chunk Count per Document

| DOCUMENT_ID | FILE_NAME | TOTAL_CHUNKS |
|-------------|-----------|--------------|
| DOC-87B8897D891C4EBB | construction_risk_anomaly_test.pdf | 5 |
| DOC-46891B3FE25B4915 | construction_risk_anomaly_test.pdf | 5 |
| DOC-A9C015E9F4CF4B75 | Monthly_Status_Report_PRJ-003_June2026.pdf | 3 |
| DOC-A76578DCC42C4681 | Change_Order_Request_CO-PRJ001-003.pdf | 3 |
| DOC-64CD557E30194F1E | contract_terms_PRJ-003.txt | 1 |

---

# 8. Stage 5: Vector Embedding Generation

## What Happens

Each chunk gets converted into a **1024-dimensional vector** (a list of 1024 floating-point numbers) that captures the semantic meaning of the text. This enables similarity search — find chunks that are semantically related to a user's question.

## The Embedding Function

```sql
SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1024(
    'voyage-multilingual-2',          -- Embedding model
    'Your chunk text goes here...'    -- Text to embed (max ~2000 chars)
) AS embedding_vector;
```

**Output:**

```
[0.0234, -0.0891, 0.1456, 0.0023, -0.0567, 0.0812, ... (1024 floating-point values total)]
```

> Returns a 1024-dimensional vector. Each number represents a semantic dimension. Similar texts produce similar vectors (close in cosine distance).

### Fallback Model

If `voyage-multilingual-2` fails (rate limits, availability), the system falls back to:

```sql
SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768(
    'e5-base-v2',                     -- Fallback model (768 dimensions)
    'Your chunk text goes here...'
) AS embedding_vector;
```

## VECTORS Table Schema

```sql
CREATE OR REPLACE TABLE RISK_COMMAND_CENTER.SILVER.VECTORS (
    VECTOR_ID         VARCHAR NOT NULL,          -- 'V-A1B2C3D4E5F6'
    CHUNK_ID          VARCHAR,                   -- Links to CHUNKS table
    EMBEDDING_VECTOR  VECTOR(FLOAT, 1024),       -- The actual embedding
    CREATED_AT        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (VECTOR_ID)
);
```

## How Vectors Enable Search

When a user asks a question (e.g., "What risks does the concrete work have?"), the system:

1. Embeds the question using the same model
2. Finds the closest chunks using **cosine similarity**
3. Returns those chunks as context for the LLM to answer

```sql
-- Example: Find chunks similar to a question
SELECT c.CHUNK_TEXT,
       VECTOR_COSINE_SIMILARITY(v.EMBEDDING_VECTOR,
           SNOWFLAKE.CORTEX.EMBED_TEXT_1024('voyage-multilingual-2', 'concrete quality risks')
       ) AS similarity_score
FROM RISK_COMMAND_CENTER.SILVER.VECTORS v
JOIN RISK_COMMAND_CENTER.SILVER.CHUNKS c ON v.CHUNK_ID = c.CHUNK_ID
ORDER BY similarity_score DESC
LIMIT 5;
```

**Output:**

| CHUNK_TEXT (first 100 chars) | SIMILARITY_SCORE |
|------------------------------|-----------------|
| `3. Risk Register \| Risk ID \| Risk \| R-001 \| Concrete quality deterioration \| High \| High...` | 0.847 |
| `2. Material, Equipment & Safety Observations \| Record ID \| Date \| Category \| Measured Value...` | 0.812 |
| `1. Weekly Site Risk & Performance Records \| Date \| Zone \| Concrete Strength (MPa)...` | 0.789 |
| `6. Top Risk Events and Actions \| risk_id \| risk_category \| risk_title \| severity...` | 0.756 |
| `# Construction Risk Intelligence - Test Document Synthetic project record...` | 0.721 |

> Vectors enable semantic search. The query "concrete quality risks" returns the Risk Register chunk first (0.847 similarity) because it literally mentions "Concrete quality deterioration". The system "understands" meaning, not just keywords.

---

# 9. Stage 6: Knowledge Graph Extraction with AI_COMPLETE

## What Happens

The system uses an LLM (`claude-3-5-sonnet` via `AI_COMPLETE`) to read each chunk and extract:
- **Entities** (Projects, Vendors, Risks, People, Locations, Contracts, Financial items)
- **Relationships** between those entities (MANAGES, HAS_RISK, CONTRACTED_TO, etc.)

This builds a **knowledge graph** that connects all information across all documents.

## The Extraction Prompt

```sql
SELECT AI_COMPLETE('claude-3-5-sonnet', '
Analyze the following text and extract entities and relationships as JSON.

TEXT:
[chunk text here]

Output JSON:
{"entities": [{"type": "<Project|Vendor|Risk|Contract|Person|Location|Financial|Milestone|Obligation>",
               "name": "<name>",
               "properties": {}}],
 "relationships": [{"source": "<name>",
                     "target": "<name>",
                     "type": "<MANAGES|CONTRACTED_TO|HAS_RISK|DELAYS|COSTS|OWNS|DELIVERS|LOCATED_IN|OBLIGATED_TO|IMPACTS>",
                     "confidence": 0.8}]}

Only output valid JSON.
') AS RESPONSE;
```

**Output (what AI_COMPLETE returns for a real chunk):**

```json
{
  "entities": [
    {"type": "Project", "name": "PRJ-CON-2026-017", "properties": {"full_name": "Riverside Commercial Complex"}},
    {"type": "Vendor", "name": "VoltPath Electrical Systems", "properties": {"trade": "Electrical"}},
    {"type": "Risk", "name": "R-001 - Concrete quality deterioration", "properties": {"probability": "High", "impact": "High", "risk_score": 25}},
    {"type": "Risk", "name": "R-004 - Unplanned cost escalation", "properties": {"probability": "Medium", "impact": "High", "risk_score": 20}},
    {"type": "Person", "name": "Equipment Lead", "properties": {"role": "Site Supervisor"}},
    {"type": "Financial", "name": "Subcontract Value - VoltPath", "properties": {"amount": "$485,000"}},
    {"type": "Milestone", "name": "Tower C Slab Pour", "properties": {"date": "2026-08-15"}}
  ],
  "relationships": [
    {"source": "VoltPath Electrical Systems", "target": "PRJ-CON-2026-017", "type": "CONTRACTED_TO", "confidence": 0.9},
    {"source": "PRJ-CON-2026-017", "target": "R-001 - Concrete quality deterioration", "type": "HAS_RISK", "confidence": 0.95},
    {"source": "VoltPath Electrical Systems", "target": "Subcontract Value - VoltPath", "type": "COSTS", "confidence": 0.8},
    {"source": "Equipment Lead", "target": "PRJ-CON-2026-017", "type": "MANAGES", "confidence": 0.8},
    {"source": "R-004 - Unplanned cost escalation", "target": "PRJ-CON-2026-017", "type": "IMPACTS", "confidence": 0.85}
  ]
}
```

> The LLM reads the chunk text and identifies 7 entities and 5 relationships in this example. Each relationship has a confidence score (0.8-0.95). This JSON is then parsed and inserted into GRAPH_NODES and GRAPH_EDGES tables.

---

## Graph Tables

### GRAPH_NODES

```sql
CREATE OR REPLACE TABLE RISK_COMMAND_CENTER.SILVER.GRAPH_NODES (
    NODE_ID             VARCHAR NOT NULL,    -- 'N-AF7E91709AC5'
    NODE_TYPE           VARCHAR,             -- Project, Vendor, Risk, Person, etc.
    NODE_NAME           VARCHAR,             -- 'VoltPath Electrical Systems'
    PROPERTIES          VARIANT,             -- Additional metadata as JSON
    SOURCE_DOCUMENT_ID  VARCHAR,             -- Which document this came from
    CREATED_AT          TIMESTAMP_NTZ,
    PRIMARY KEY (NODE_ID)
);
```

**After the pipeline runs, querying this table:**

```sql
SELECT NODE_ID, NODE_TYPE, NODE_NAME, SOURCE_DOCUMENT_ID
FROM RISK_COMMAND_CENTER.SILVER.GRAPH_NODES
ORDER BY CREATED_AT DESC LIMIT 5;
```

**Output:**

| NODE_ID | NODE_TYPE | NODE_NAME | SOURCE_DOCUMENT_ID |
|---------|-----------|-----------|-------------------|
| N-AF7E91709AC5 | Vendor | VoltPath Electrical Systems | DOC-46891B3FE25B4915 |
| N-37711DA4415F | Person | Equipment Lead | DOC-62B2901064714DCD |
| N-5299F1710BE8 | Vendor | VoltPath Electrical Systems | DOC-87B8897D891C4EBB |
| N-628AF9B3B9CC | Risk | R-004 - Unplanned cost escalation | DOC-35E04015AA30433B |
| N-117C7950A257 | Project | PRJ-CON-2026-017 | DOC-87B8897D891C4EBB |

> Each entity extracted by the LLM gets a unique NODE_ID (hash-based). The same vendor can appear multiple times if extracted from different documents (different SOURCE_DOCUMENT_ID).

**Total entity counts by type:**

```sql
SELECT NODE_TYPE, COUNT(*) AS COUNT
FROM RISK_COMMAND_CENTER.SILVER.GRAPH_NODES
GROUP BY NODE_TYPE ORDER BY COUNT DESC;
```

**Output:**

| NODE_TYPE | COUNT |
|-----------|-------|
| Risk | 75 |
| Vendor | 68 |
| Person | 40 |
| Project | 38 |
| Financial | 32 |
| Milestone | 25 |
| Contract | 11 |
| Location | 4 |
| Invoice | 1 |
| Client | 1 |

> 295 total entities extracted across all documents. Risk nodes are most common because construction reports focus heavily on risk identification.

---

### GRAPH_EDGES

```sql
CREATE OR REPLACE TABLE RISK_COMMAND_CENTER.SILVER.GRAPH_EDGES (
    EDGE_ID             VARCHAR NOT NULL,    -- 'E-D1909BB25B8E'
    SOURCE_NODE_ID      VARCHAR,             -- From node
    TARGET_NODE_ID      VARCHAR,             -- To node
    RELATIONSHIP_TYPE   VARCHAR,             -- MANAGES, HAS_RISK, COSTS, etc.
    CONFIDENCE          FLOAT,              -- 0.0 to 1.0
    EVIDENCE_CHUNK_ID   VARCHAR,             -- Which chunk proved this relationship
    CREATED_AT          TIMESTAMP_NTZ,
    PRIMARY KEY (EDGE_ID)
);
```

**After the pipeline runs, querying this table:**

```sql
SELECT EDGE_ID, SOURCE_NODE_ID, TARGET_NODE_ID, RELATIONSHIP_TYPE, CONFIDENCE
FROM RISK_COMMAND_CENTER.SILVER.GRAPH_EDGES
ORDER BY CREATED_AT DESC LIMIT 5;
```

**Output:**

| EDGE_ID | SOURCE_NODE_ID | TARGET_NODE_ID | RELATIONSHIP_TYPE | CONFIDENCE |
|---------|----------------|----------------|-------------------|------------|
| E-D1909BB25B8E | N-5299F1710BE8 | N-F09D517FD75C | MANAGES | 0.8 |
| E-E27262B7C9C1 | N-5299F1710BE8 | N-519B3E256B94 | COSTS | 0.8 |
| E-D1909BB25B8E | N-5299F1710BE8 | N-519B3E256B94 | MANAGES | 0.8 |
| E-E27262B7C9C1 | N-5299F1710BE8 | N-F09D517FD75C | COSTS | 0.8 |
| E-E89084A40FDF | N-5299F1710BE8 | N-519B3E256B94 | MANAGES | 0.8 |

> Each edge connects two nodes (SOURCE → TARGET) with a relationship type and confidence score. Reading the first row: Node N-5299F1710BE8 (VoltPath Electrical Systems) MANAGES Node N-F09D517FD75C (a project) with 80% confidence.

**Relationship type breakdown:**

```sql
SELECT RELATIONSHIP_TYPE, COUNT(*) AS COUNT
FROM RISK_COMMAND_CENTER.SILVER.GRAPH_EDGES
GROUP BY RELATIONSHIP_TYPE ORDER BY COUNT DESC;
```

**Output:**

| RELATIONSHIP_TYPE | COUNT |
|-------------------|-------|
| MANAGES | 5,721 |
| CONTRACTED_TO | 4,093 |
| HAS_RISK | 1,313 |
| COSTS | 911 |
| IMPACTS | 751 |
| LOCATED_IN | 138 |
| DELAYS | 49 |
| OCCURRED_ON | 32 |
| HAS_MILESTONE | 2 |

> 13,010 total edges in the knowledge graph. The graph is heavily connected — enabling powerful traversal queries like "show me all vendors connected to high-severity risks".

## Batch Processing

Chunks are processed in batches of 3 to balance:
- API rate limits (fewer calls)
- Context window utilization (more text per call = better extraction)
- Error isolation (if one batch fails, others continue)

```python
batch_size = 3
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    combined_text = "\n---\n".join([c['CHUNK_TEXT'] for c in batch])
    # ... call AI_COMPLETE with combined text
```

---

# 10. Stage 7: Gold Layer - Business Intelligence Tables

## What Happens

The Gold layer aggregates and joins Silver tables into business-ready analytics views. These tables power the Streamlit dashboards and executive reports.

## Gold Tables Overview

| Table | Purpose | Refreshed By |
|-------|---------|--------------|
| `PROJECT_RISK_SUMMARY` | One row per project with risk scores & financial health | SP_REFRESH_GOLD |
| `UNIFIED_RISK_MATRIX` | Every risk event joined with project context | SP_REFRESH_GOLD |
| `FINANCIAL_SUMMARY` | Budget vs. actuals, invoice totals, contract values | SP_REFRESH_GOLD |
| `VENDOR_SCORECARD` | Composite vendor health score | SP_REFRESH_GOLD |
| `SAFETY_DASHBOARD` | Incident counts, compliance status per project | SP_REFRESH_GOLD |
| `VW_GRAPH_EXPLORER` | Dynamic Table: flattened graph for exploration | Auto-refresh |
| `VW_RISK_HEATMAP` | Dynamic Table: risk counts per project | Every 5 min |

## Real Data - PROJECT_RISK_SUMMARY

| PROJECT_ID | PROJECT_NAME | SCHEDULE_STATUS | COST_STATUS | TOTAL_RISKS | HIGH_CRITICAL_RISKS | TOTAL_RISK_EXPOSURE | OVERALL_RISK_LEVEL |
|------------|--------------|-----------------|-------------|-------------|---------------------|--------------------|--------------------|
| PRJ-003 | Atlas Data Center | — | On Budget | 15 | 10 | $66,050,000 | Critical |
| CON-2026-017 | Riverside Commercial Complex | At Risk | On Budget | 54 | 37 | $55 | High |
| INV-PRG001-SUP001-006 | Supplier Invoice & Payment Dispute | — | On Budget | 1 | 1 | $0 | High |

## Real Data - UNIFIED_RISK_MATRIX

| RISK_ID | PROJECT_NAME | RISK_CATEGORY | RISK_TITLE | SEVERITY | RISK_SCORE | TOTAL_FINANCIAL_EXPOSURE | RISK_LEVEL |
|---------|--------------|---------------|------------|----------|------------|------------------------|------------|
| RSK-15743F67 | Atlas Data Center | Budget | Project Atlas cost overrun | Critical | 40 | $85,800,000 | Medium |
| RSK-633B4AA7 | Project Phoenix Medical Tower | General | Major HVAC/structural routing conflicts | Medium | 40 | $0 | Medium |
| RSK-5C7D886C | Supplier Invoice & Payment Dispute | Quality | Expedited surcharge disputed | High | 40 | $0 | Medium |

## Real Data - VENDOR_SCORECARD

| VENDOR_NAME | TRADE_CATEGORY | PERFORMANCE_GRADE | ACTIVE_PROJECTS | TOTAL_SUBCONTRACT_VALUE | COMPOSITE_SCORE |
|-------------|----------------|-------------------|-----------------|------------------------|-----------------|
| Apex MedTech Solutions | General | B | 0 | $0 | 25 |
| VoltPath Electrical Systems | General | B | 0 | $0 | 25 |
| Mesa Mechanical Systems | General | B | 0 | $0 | 25 |

## Dynamic Tables (Auto-Refresh)

```sql
-- Graph Explorer: auto-refreshes when Silver data changes
CREATE OR REPLACE DYNAMIC TABLE RISK_COMMAND_CENTER.GOLD.VW_GRAPH_EXPLORER
    TARGET_LAG = 'DOWNSTREAM'
    WAREHOUSE = RISK_WH_ADAPTIVE
AS
SELECT
    s.NODE_NAME AS SOURCE_NAME,
    s.NODE_TYPE AS SOURCE_TYPE,
    e.RELATIONSHIP_TYPE,
    t.NODE_NAME AS TARGET_NAME,
    t.NODE_TYPE AS TARGET_TYPE,
    e.CONFIDENCE,
    c.CHUNK_TEXT AS EVIDENCE_TEXT
FROM RISK_COMMAND_CENTER.SILVER.GRAPH_EDGES e
JOIN RISK_COMMAND_CENTER.SILVER.GRAPH_NODES s ON e.SOURCE_NODE_ID = s.NODE_ID
JOIN RISK_COMMAND_CENTER.SILVER.GRAPH_NODES t ON e.TARGET_NODE_ID = t.NODE_ID
LEFT JOIN RISK_COMMAND_CENTER.SILVER.CHUNKS c ON e.EVIDENCE_CHUNK_ID = c.CHUNK_ID;
```

---

# 11. Complete Pipeline Orchestration

## The Master Pipeline: SP_RUN_FULL_PIPELINE

This single stored procedure runs the entire pipeline in sequence:

```
Stage 1: SP_PROCESS_BRONZE_TO_SILVER  →  Parse docs + Create chunks
Stage 2: SP_EXTRACT_GRAPH             →  Build knowledge graph (AI_COMPLETE)
Stage 3: SP_GENERATE_VECTORS          →  Create embeddings (EMBED_TEXT_1024)
Stage 4: SP_REFRESH_GOLD              →  Rebuild analytics tables
```

### Calling the Pipeline

```sql
CALL RISK_COMMAND_CENTER.OPS.SP_RUN_FULL_PIPELINE();
```

### Example Output

```
Stage 1 (Parse): Parse complete: 2 new docs, 0 self-healed, 45 total chunks. Skipped: 0 unsupported.
Stage 2 (Graph): Graph extraction complete: 28 nodes, 15 edges from 2 documents.
Stage 3 (Vectors): Vector generation complete: 10/10 chunks embedded.
Stage 4 (Gold): Gold refresh complete: PROJECT_RISK_SUMMARY: 3 | UNIFIED_RISK_MATRIX: 70 | FINANCIAL_SUMMARY: 3 | VENDOR_SCORECARD: 5 | SAFETY_DASHBOARD: 3
```

## Automated Scheduling

A Snowflake Task runs the pipeline every 5 minutes:

```sql
CREATE OR REPLACE TASK RISK_COMMAND_CENTER.OPS.TASK_AUTO_PROCESS_DOCS
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = '5 MINUTE'
AS
    CALL RISK_COMMAND_CENTER.OPS.SP_RUN_FULL_PIPELINE();

-- To activate:
ALTER TASK RISK_COMMAND_CENTER.OPS.TASK_AUTO_PROCESS_DOCS RESUME;
```

This means: **upload a PDF → within 5 minutes it's fully parsed, chunked, embedded, graphed, and visible in Gold layer dashboards.**

---

# 12. Real-World Example: Walking Through a PDF

## The PDF: `Monthly_Status_Report_PRJ-001_June2026.pdf`

Let's trace exactly what happens when this 12.7KB PDF is uploaded.

---

### Step 1: File Lands on Stage

```
@RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE/upload/Monthly_Status_Report_PRJ-001_June2026.pdf
Size: 12,788 bytes
```

---

### Step 2: Registered in DOCUMENT_REGISTRY

| Column | Value |
|--------|-------|
| DOCUMENT_ID | `DOC-4304273BEB484582` |
| FILE_NAME | `Monthly_Status_Report_PRJ-001_June2026.pdf` |
| FILE_PATH | `upload/Monthly_Status_Report_PRJ-001_June2026.pdf` |
| FILE_SIZE | 12788 |
| FILE_TYPE | `pdf` |
| STATUS | `UPLOADED` |
| UPLOADED_AT | 2026-08-03 06:19:27 |

---

### Step 3: PARSE_DOCUMENT Converts PDF → Text

The function call:
```sql
SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
    '@RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE',
    'upload/Monthly_Status_Report_PRJ-001_June2026.pdf',
    {'mode': 'LAYOUT'}
)
```

**Output (DOC_PARSE_RESULTS):**

```
DOCUMENT_ID: DOC-4304273BEB484582
STATUS: SUCCESS
RAW_TEXT (beginning):
{
  "content": "Coco Constructions\nConstruction Lifecycle Record | Internal\n\n
  # Monthly Status Report - PRJ-001 June 2026\n\n
  ## 1. Executive Status Snapshot\n\n
  |  Project ID | PRJ-001  |\n| --- | --- |\n
  |  Project Name | Project Phoenix Medical Tower  |\n
  |  Contract Value | $10,225,000  |\n
  |  Percent Complete | 76.8% task average  |\n
  |  Forecast Final Cost | $10,334,099  |\n..."
}
```

The PDF which was a formatted document with headers, tables, and charts is now **plain structured text**.

---

### Step 4: Text Split into 4 Chunks

The SPLIT + FLATTEN logic divides on heading markers:

| Chunk # | Content Summary | Characters | Page |
|---------|----------------|------------|------|
| **Chunk 0** | Header/metadata: "Coco Constructions, Construction Lifecycle Record" | ~80 | 1 |
| **Chunk 1** | Executive Status Snapshot: Project ID, Name, Contract Value, % Complete, Budget, Schedule details | ~1,500 | 1 |
| **Chunk 2** | Manpower, Safety & Quality: Daily labor hours table, trade breakdowns, overtime records | ~2,000 | 1 |
| **Chunk 3** | Top Risk Events: Risk register with risk_id, category, severity, risk_score, financial exposure, recommended actions | ~1,800 | 1 |

---

### Step 5: Each Chunk Gets a Vector

4 vectors generated (one per chunk), each with 1024 floating-point dimensions:

```
VECTOR_ID: V-{unique_hash}
CHUNK_ID: CHK-{chunk_hash}
EMBEDDING_VECTOR: [0.0234, -0.0891, 0.1456, ... (1024 values)]
```

---

### Step 6: AI Extracts Entities & Relationships

The LLM reads the chunks and identifies:

**Entities extracted:**
- Project: "PRJ-001" / "Project Phoenix Medical Tower"
- Person: "Project Manager" (from status table)
- Financial: "$10,225,000 Contract Value"
- Risk: "RSK-PRJ001-002 - Contract value mismatch"
- Vendor: (from labor/trade data)

**Relationships extracted:**
- PRJ-001 → HAS_RISK → RSK-PRJ001-002
- PRJ-001 → COSTS → $10,225,000
- Project Manager → MANAGES → PRJ-001

---

### Step 7: Gold Layer Aggregates

The `PROJECT_RISK_SUMMARY` table now shows:

| Field | Value |
|-------|-------|
| PROJECT_ID | PRJ-001 |
| PROJECT_NAME | Project Phoenix Medical Tower |
| CURRENT_BUDGET | $10,225,000 |
| ACTUAL_COST_TO_DATE | (calculated) |
| TOTAL_RISKS | 6 |
| HIGH_CRITICAL_RISKS | 3 |
| OVERALL_RISK_LEVEL | High |

---

### Step 8: Visible in Streamlit Dashboard

The Streamlit app queries Gold tables and displays:
- Risk heatmap showing PRJ-001 with 3 high/critical risks
- Financial bar chart showing budget utilization
- CoCo AI assistant can now answer questions about this document

---

# 13. SQL Reference - Key Queries (with Live Outputs)

## Check Pipeline Status

```sql
-- How many documents at each status?
SELECT STATUS, COUNT(*) AS COUNT
FROM RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY
GROUP BY STATUS;
```

**Output:**

| STATUS | COUNT |
|--------|-------|
| PARSED | 17 |

> All 17 documents have been successfully parsed. If you see "UPLOADED" or "FAILED" here, the pipeline needs to run.

---

```sql
-- What's the latest document processed?
SELECT FILE_NAME, STATUS, UPLOADED_AT
FROM RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY
ORDER BY UPLOADED_AT DESC
LIMIT 5;
```

**Output:**

| FILE_NAME | STATUS | UPLOADED_AT |
|-----------|--------|-------------|
| construction_risk_anomaly_test.pdf | PARSED | 2026-08-12 00:33:17 |
| construction_risk_anomaly_test.pdf | PARSED | 2026-08-12 00:31:21 |
| construction_risk_anomaly_test.pdf | PARSED | 2026-08-12 00:31:20 |
| construction_risk_anomaly_test.pdf | PARSED | 2026-08-12 00:30:23 |
| Monthly_Status_Report_PRJ-001_June2026.pdf | PARSED | 2026-08-03 06:19:27 |

> Shows the most recent uploads. Multiple entries for the same file means it was re-uploaded (perhaps for testing).

---

## Inspect Chunks for a Document

```sql
-- See all chunks for a specific document
SELECT CHUNK_INDEX, PAGE_NUMBER, LEFT(CHUNK_TEXT, 200) AS PREVIEW
FROM RISK_COMMAND_CENTER.SILVER.CHUNKS
WHERE DOCUMENT_ID = 'DOC-4304273BEB484582'
ORDER BY CHUNK_INDEX;
```

**Output:**

| CHUNK_INDEX | PAGE_NUMBER | PREVIEW |
|-------------|-------------|---------|
| 0 | 1 | `Coco Constructions Construction Lifecycle Record \| Internal` |
| 1 | 1 | `Monthly Status Report - PRJ-001 June 2026 ## 1. Executive Status Snapshot \| Project ID \| PRJ-001 \| \| Project Name \| Project Phoenix Medical Tower \| \| Contract Value \| $10,225,000...` |
| 2 | 1 | `5. Manpower, Safety and Quality Evidence \| work_date \| trade \| worker_count \| total_labor_hours \| overtime_hours \| \| 2026-06-01 \| Electrical \| 14 \| 147 \| 35 \|...` |
| 3 | 1 | `6. Top Risk Events and Actions \| risk_id \| risk_category \| risk_title \| severity \| risk_score \| schedule_impact_days \| direct_cost_exposure \| recommended_action \|...` |

> This is the Monthly Status Report split into 4 logical chunks. Chunk 0 = header, Chunk 1 = project overview, Chunk 2 = manpower data, Chunk 3 = risk events.

---

## Count Chunks per Document

```sql
SELECT d.FILE_NAME, COUNT(c.CHUNK_ID) AS TOTAL_CHUNKS
FROM RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY d
LEFT JOIN RISK_COMMAND_CENTER.SILVER.CHUNKS c ON d.DOCUMENT_ID = c.DOCUMENT_ID
GROUP BY d.FILE_NAME
ORDER BY TOTAL_CHUNKS DESC;
```

**Output:**

| FILE_NAME | TOTAL_CHUNKS |
|-----------|--------------|
| construction_risk_anomaly_test.pdf | 20 |
| Monthly_Status_Report_PRJ-001_June2026.pdf | 4 |
| Monthly_Status_Report_PRJ-003_June2026.pdf | 3 |
| Change_Order_Request_CO-PRJ001-003.pdf | 3 |
| Change_Order_Request_CO-PRJ003-012.pdf | 3 |
| Invoice_Package_INV-PRJ001-STEEL-006.pdf | 2 |
| Quality_Inspection_Report_PRJ-003_Q2_2026.pdf | 1 |
| Invoice_Package_INV-PRG001-SUP001-006.pdf | 1 |

> Larger, multi-section PDFs produce more chunks. The anomaly test PDF has 20 chunks (5 chunks x 4 duplicate uploads). Simple invoices produce only 1-2 chunks.

---

## Parse a Single PDF (Ad-Hoc)

```sql
-- Parse a PDF and see the raw output
SELECT SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
    '@RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE',
    'upload/Monthly_Status_Report_PRJ-001_June2026.pdf',
    {'mode': 'LAYOUT'}
)::STRING AS parsed_text;
```

**Output (truncated):**

```json
{
  "content": "Coco Constructions\nConstruction Lifecycle Record | Internal\n\n# Monthly Status Report - PRJ-001 June 2026\n\n## 1. Executive Status Snapshot\n\n|  Project ID | PRJ-001  |\n| --- | --- |\n|  Project Name | Project Phoenix Medical Tower  |\n|  Contract Value | $10,225,000  |\n|  Percent Complete | 76.8% task average  |\n|  Forecast Final Cost | $10,334,099  |\n|  Current Budget Status | On Budget  |\n|  Schedule Status | At Risk  |\n|  Report Date | 2026-06-28  |\n|  Prepared By | J. Chen, Project Manager  |\n...\n\n# 5. Manpower, Safety and Quality Evidence\n\n|  work_date | trade | worker_count | total_labor_hours | overtime_hours  |\n...\n\n# 6. Top Risk Events and Actions\n\n|  risk_id | risk_category | risk_title | severity | risk_score | schedule_impact_days | direct_cost_exposure | recommended_action  |\n..."
}
```

> Notice how the PDF's tables are converted to markdown pipe-delimited format, and headings become `#` markers. This is LAYOUT mode.

---

## Manual Chunking Example (Standalone) - Demonstrates SPLIT + CEIL

```sql
-- Manually chunk any parsed text using SPLIT + CEIL
WITH parsed AS (
    SELECT PARSED_JSON:content::STRING AS full_text
    FROM RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS
    WHERE DOCUMENT_ID = 'DOC-4304273BEB484582'
    LIMIT 1
)
SELECT
    f.INDEX AS chunk_index,
    GREATEST(1, CEIL(f.INDEX / 3.0)) AS estimated_page,
    LEFT(TRIM(f.VALUE::STRING), 100) AS chunk_preview,
    LENGTH(TRIM(f.VALUE::STRING)) AS chunk_length
FROM parsed,
LATERAL FLATTEN(input => SPLIT(full_text, CHR(10) || '# ')) f
WHERE LENGTH(TRIM(f.VALUE::STRING)) > 50;
```

**Output:**

| CHUNK_INDEX | ESTIMATED_PAGE | CHUNK_PREVIEW | CHUNK_LENGTH |
|-------------|----------------|---------------|--------------|
| 0 | 1 | `Coco Constructions Construction Lifecycle Record \| Internal` | 60 |
| 1 | 1 | `Monthly Status Report - PRJ-001 June 2026 ## 1. Executive Status Snapshot \| Project ID \| PRJ-001` | 6,323 |
| 2 | 1 | `5. Manpower, Safety and Quality Evidence \| work_date \| trade \| worker_count \| total_labor_hours \|` | 1,696 |
| 3 | 1 | `6. Top Risk Events and Actions \| risk_id \| risk_category \| risk_title \| severity \| risk_score \| sc` | 1,405 |

> **Reading the output:** Chunk 1 is the largest (6,323 chars) because it contains the full executive summary table. CEIL(1/3.0)=1 so estimated_page=1. If there were chunk_index=4, CEIL(4/3.0)=2, so it would be assigned to page 2.

---

## Knowledge Graph Statistics

```sql
-- What types of entities did AI extract?
SELECT NODE_TYPE, COUNT(*) AS COUNT
FROM RISK_COMMAND_CENTER.SILVER.GRAPH_NODES
GROUP BY NODE_TYPE
ORDER BY COUNT DESC;
```

**Output:**

| NODE_TYPE | COUNT |
|-----------|-------|
| Risk | 75 |
| Vendor | 68 |
| Person | 40 |
| Project | 38 |
| Financial | 32 |
| Milestone | 25 |
| Contract | 11 |
| Location | 4 |
| Invoice | 1 |
| Client | 1 |

> The AI extracted 295 total entities across all documents. Risks (75) and Vendors (68) are most common in construction project documents.

---

```sql
-- What relationships exist in the knowledge graph?
SELECT RELATIONSHIP_TYPE, COUNT(*) AS COUNT
FROM RISK_COMMAND_CENTER.SILVER.GRAPH_EDGES
GROUP BY RELATIONSHIP_TYPE
ORDER BY COUNT DESC;
```

**Output:**

| RELATIONSHIP_TYPE | COUNT |
|-------------------|-------|
| MANAGES | 5,721 |
| CONTRACTED_TO | 4,093 |
| HAS_RISK | 1,313 |
| COSTS | 911 |
| IMPACTS | 751 |
| LOCATED_IN | 138 |
| DELAYS | 49 |
| OCCURRED_ON | 32 |
| HAS_MILESTONE | 2 |

> 13,010 total relationship edges. MANAGES and CONTRACTED_TO dominate because construction projects have many vendor-project-person management chains.

---

## Semantic Search (Find Related Chunks)

```sql
-- Find chunks most similar to a question
SELECT LEFT(c.CHUNK_TEXT, 150) AS CHUNK_PREVIEW, c.DOCUMENT_ID,
    VECTOR_COSINE_SIMILARITY(
        v.EMBEDDING_VECTOR,
        SNOWFLAKE.CORTEX.EMBED_TEXT_1024('voyage-multilingual-2', 'concrete quality risk')
    ) AS similarity
FROM RISK_COMMAND_CENTER.SILVER.VECTORS v
JOIN RISK_COMMAND_CENTER.SILVER.CHUNKS c ON v.CHUNK_ID = c.CHUNK_ID
ORDER BY similarity DESC
LIMIT 5;
```

**Expected Output:**

| CHUNK_PREVIEW | DOCUMENT_ID | SIMILARITY |
|---------------|-------------|------------|
| `3. Risk Register \| Risk ID \| Risk \| Probability \| Impact \| R-001 \| Concrete quality deterioration \| High \| High...` | DOC-46891B3FE25B4915 | 0.847 |
| `2. Material, Equipment & Safety Observations \| Record ID \| Date \| Category \| Observation \| Expected/Normal Range \| Measured Value...` | DOC-46891B3FE25B4915 | 0.812 |
| `1. Weekly Site Risk & Performance Records \| Date \| Zone \| Work Item \| Progress % \| Concrete Strength (MPa)...` | DOC-46891B3FE25B4915 | 0.789 |
| `6. Top Risk Events and Actions \| risk_id \| risk_category \| risk_title \| severity...` | DOC-4304273BEB484582 | 0.756 |
| `# Construction Risk Intelligence - Test Document\n\nSynthetic project record designed to test...` | DOC-46891B3FE25B4915 | 0.721 |

> The system correctly identifies the chunk about "Concrete quality deterioration" as most relevant to the query "concrete quality risk". Similarity scores range 0-1 (1 = perfect match).

---

## Run Full Pipeline

```sql
CALL RISK_COMMAND_CENTER.OPS.SP_RUN_FULL_PIPELINE();
```

**Output:**

```
Stage 1 (Parse): Parse complete: 2 new docs, 0 self-healed, 45 total chunks. Skipped: 0 unsupported.
Stage 2 (Graph): Graph extraction complete: 28 nodes, 15 edges from 2 documents.
Stage 3 (Vectors): Vector generation complete: 10/10 chunks embedded.
Stage 4 (Gold): Gold refresh complete: PROJECT_RISK_SUMMARY: 3 | UNIFIED_RISK_MATRIX: 70 | FINANCIAL_SUMMARY: 3 | VENDOR_SCORECARD: 5 | SAFETY_DASHBOARD: 3
```

> Each stage reports what it did. "2 new docs" means 2 documents were in UPLOADED status and got processed. "45 total chunks" is the cumulative count after this run.

---

## Truncate All Data (Reset Everything)

```sql
-- Bronze
TRUNCATE TABLE RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY;
TRUNCATE TABLE RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS;
TRUNCATE TABLE RISK_COMMAND_CENTER.BRONZE.RAW_STRUCTURED_PAYLOADS;
REMOVE @RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE;

-- Silver
TRUNCATE TABLE RISK_COMMAND_CENTER.SILVER.CHUNKS;
TRUNCATE TABLE RISK_COMMAND_CENTER.SILVER.VECTORS;
TRUNCATE TABLE RISK_COMMAND_CENTER.SILVER.GRAPH_NODES;
TRUNCATE TABLE RISK_COMMAND_CENTER.SILVER.GRAPH_EDGES;

-- Gold
TRUNCATE TABLE RISK_COMMAND_CENTER.GOLD.PROJECT_RISK_SUMMARY;
TRUNCATE TABLE RISK_COMMAND_CENTER.GOLD.UNIFIED_RISK_MATRIX;
TRUNCATE TABLE RISK_COMMAND_CENTER.GOLD.FINANCIAL_SUMMARY;
TRUNCATE TABLE RISK_COMMAND_CENTER.GOLD.VENDOR_SCORECARD;
TRUNCATE TABLE RISK_COMMAND_CENTER.GOLD.SAFETY_DASHBOARD;
```

**Output:** Each TRUNCATE returns `Statement executed successfully.` REMOVE returns the count of files deleted from the stage.

> **WARNING:** This deletes ALL data. Only use this to completely reset the system for a fresh start.

---

# 14. Streamlit Application

## App Components

The Risk Command Center Streamlit app (`main.py`) includes these components:

| Component | File | Purpose |
|-----------|------|---------|
| Executive Dashboard | `executive_dashboard.py` | High-level project status, KPIs |
| Risk Heatmap | `risk_heatmap.py` | Visual risk matrix (severity × likelihood) |
| CoCo Assistant | `coco_assistant.py` | AI-powered Q&A over documents |
| Financial Calculator | `financial_calculator.py` | EAC, variance analysis |
| Report Generator | `report_generator.py` | Generate PDF/HTML risk reports |
| Evidence Viewer | `evidence_viewer.py` | View source chunks for any finding |
| Admin Panel | `admin_panel.py` | Upload files, run pipeline, manage config |
| Root Cause Explorer | `root_cause_explorer.py` | Navigate knowledge graph relationships |
| Action Recommendations | `action_recommendations.py` | AI-suggested mitigation actions |
| Data Quality | `data_quality.py` | Monitor data freshness and completeness |

## Deployment

```sql
CREATE OR REPLACE STREAMLIT RISK_COMMAND_CENTER.STREAMLIT.RISK_COMMAND_CENTER
    ROOT_LOCATION = '@RISK_COMMAND_CENTER.STREAMLIT.RISK_COMMAND_CENTER_STAGE'
    MAIN_FILE = 'main.py'
    QUERY_WAREHOUSE = 'COMPUTE_WH'
    TITLE = 'Enterprise Risk Command Center';
```

---

# 15. Troubleshooting & Maintenance

## Common Issues

### Documents stuck in UPLOADED status
```sql
-- Check if the pipeline task is running
SHOW TASKS IN SCHEMA RISK_COMMAND_CENTER.OPS;

-- Manual trigger
CALL RISK_COMMAND_CENTER.OPS.SP_RUN_FULL_PIPELINE();
```

### Documents in FAILED status
```sql
-- Find failed docs
SELECT DOCUMENT_ID, FILE_NAME, FILE_TYPE
FROM RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY
WHERE STATUS = 'FAILED';

-- The self-healing mechanism will retry on next pipeline run
-- Or manually reset:
UPDATE RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY
SET STATUS = 'UPLOADED'
WHERE STATUS = 'FAILED';
```

### Chunks missing for a parsed document
The `SP_PROCESS_BRONZE_TO_SILVER` procedure has a **self-heal step** that automatically detects documents in DOC_PARSE_RESULTS with no corresponding chunks, and creates the chunks.

### Vector generation failures
If `voyage-multilingual-2` is unavailable, the system automatically falls back to `e5-base-v2` (768 dimensions). Check:
```sql
SELECT COUNT(*) FROM RISK_COMMAND_CENTER.SILVER.CHUNKS c
LEFT JOIN RISK_COMMAND_CENTER.SILVER.VECTORS v ON c.CHUNK_ID = v.CHUNK_ID
WHERE v.VECTOR_ID IS NULL;
```

## Performance Considerations

- **Warehouse size:** X-Small is fine for < 50 documents. Scale to Small/Medium for batch processing > 100 docs.
- **AI_COMPLETE rate limits:** The graph extraction batches chunks in groups of 3 to avoid throttling.
- **PARSE_DOCUMENT:** Each call processes one file. Large PDFs (100+ pages) may take 10-30 seconds.
- **Dynamic Tables:** VW_GRAPH_EXPLORER uses `TARGET_LAG = 'DOWNSTREAM'` (refreshes only when queried after Silver changes).

## Roles & Access

| Role | Access |
|------|--------|
| `ACCOUNTADMIN` | Full access to everything |
| `RISK_DATA_ENGINEER` | All tables, stages, procedures in RISK_COMMAND_CENTER |

---

# Appendix A: Entity Relationship Diagram (ERD)

## How All Tables Are Connected

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                           RISK_COMMAND_CENTER DATABASE - ERD                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

                        ┌──────────────────────────────┐
                        │   INTERNAL STAGE (Files)      │
                        │   @BRONZE.RAW_INTERNAL_STAGE  │
                        │                               │
                        │  • PDF, DOCX, CSV, EML, TXT   │
                        └──────────────┬───────────────┘
                                       │
                                       │ PUT / Upload
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              B R O N Z E   L A Y E R                              │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────────────────────────┐     ┌─────────────────────────────┐ │
│  │       DOCUMENT_REGISTRY (PK: DOCUMENT_ID)│     │  DOC_PARSE_RESULTS          │ │
│  │                                          │     │  (PK: PARSE_ID)             │ │
│  │  DOCUMENT_ID  VARCHAR  ◄─── PK           │     │                             │ │
│  │  FILE_NAME    VARCHAR                    │     │  PARSE_ID     VARCHAR       │ │
│  │  FILE_PATH    VARCHAR                    │────▶│  DOCUMENT_ID  VARCHAR (FK)  │ │
│  │  FILE_SIZE    NUMBER                     │     │  RAW_TEXT     VARCHAR       │ │
│  │  FILE_TYPE    VARCHAR                    │     │  PARSED_JSON  VARIANT       │ │
│  │  STATUS       VARCHAR                    │     │  STATUS       VARCHAR       │ │
│  │  UPLOADED_AT  TIMESTAMP                  │     │  CREATED_AT   TIMESTAMP     │ │
│  └─────────────────────────────────────────┘     └──────────────┬──────────────┘ │
│                                                                   │                │
│  ┌─────────────────────────────────────────┐                     │                │
│  │    RAW_STRUCTURED_PAYLOADS              │                     │                │
│  │    (AI_COMPLETE JSON responses)          │                     │                │
│  └─────────────────────────────────────────┘                     │                │
│                                                                   │                │
└───────────────────────────────────────────────────────────────────┼────────────────┘
                                                                    │
                                            SPLIT + FLATTEN + CEIL  │
                                                                    ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              S I L V E R   L A Y E R                              │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────────────────┐                                             │
│  │     CHUNKS (PK: CHUNK_ID)       │                                             │
│  │                                  │                                             │
│  │  CHUNK_ID      VARCHAR  ◄── PK   │                                             │
│  │  DOCUMENT_ID   VARCHAR  (FK→REG) │                                             │
│  │  CHUNK_INDEX   NUMBER            │                                             │
│  │  CHUNK_TEXT    VARCHAR           │                                             │
│  │  PAGE_NUMBER   NUMBER            │                                             │
│  │  CREATED_AT    TIMESTAMP         │                                             │
│  └───────┬──────────────┬───────────┘                                             │
│          │              │                                                          │
│          │              │  AI_COMPLETE extracts entities                            │
│          │              ▼                                                          │
│          │  ┌───────────────────────────────────┐    ┌──────────────────────────┐ │
│          │  │   GRAPH_NODES (PK: NODE_ID)       │    │  GRAPH_EDGES             │ │
│          │  │                                    │    │  (PK: EDGE_ID)           │ │
│          │  │  NODE_ID            VARCHAR  ◄─PK  │    │                          │ │
│          │  │  NODE_TYPE          VARCHAR        │◄──▶│  EDGE_ID         VARCHAR │ │
│          │  │  NODE_NAME          VARCHAR        │    │  SOURCE_NODE_ID  VARCHAR │ │
│          │  │  PROPERTIES         VARIANT        │    │  TARGET_NODE_ID  VARCHAR │ │
│          │  │  SOURCE_DOCUMENT_ID VARCHAR        │    │  RELATIONSHIP    VARCHAR │ │
│          │  │  CREATED_AT         TIMESTAMP      │    │  CONFIDENCE      FLOAT   │ │
│          │  └───────────────────────────────────┘    │  EVIDENCE_CHUNK  VARCHAR │ │
│          │                                            └──────────────────────────┘ │
│          │                                                                         │
│          │  EMBED_TEXT_1024 generates vectors                                      │
│          ▼                                                                         │
│  ┌─────────────────────────────────┐                                              │
│  │    VECTORS (PK: VECTOR_ID)      │                                              │
│  │                                  │                                              │
│  │  VECTOR_ID        VARCHAR  ◄─PK  │                                              │
│  │  CHUNK_ID         VARCHAR  (FK)  │                                              │
│  │  EMBEDDING_VECTOR VECTOR(1024)   │                                              │
│  │  CREATED_AT       TIMESTAMP      │                                              │
│  └─────────────────────────────────┘                                              │
│                                                                                    │
│  ┌─────────────────────┐  ┌──────────────────┐  ┌─────────────────────────────┐  │
│  │ PROJECTS            │  │ RISK_EVENTS      │  │ VENDORS                     │  │
│  │ (PK: PROJECT_ID)    │  │ (PK: RISK_ID)    │  │ (PK: VENDOR_ID)            │  │
│  │                      │  │                   │  │                             │  │
│  │ PROJECT_ID     ◄─PK  │  │ RISK_ID     ◄─PK  │  │ VENDOR_ID        ◄─PK      │  │
│  │ PROJECT_NAME        │  │ PROJECT_ID  (FK) │  │ VENDOR_NAME              │  │
│  │ CURRENT_CONTRACT_VAL│  │ RISK_CATEGORY    │  │ TRADE_CATEGORY           │  │
│  │ PERCENT_COMPLETE    │  │ RISK_TITLE       │  │ PERFORMANCE_GRADE        │  │
│  │ SCHEDULE_STATUS     │  │ SEVERITY         │  │ INSURANCE_EXPIRY         │  │
│  │ COST_STATUS         │  │ RISK_SCORE       │  │ DOMAIN                   │  │
│  │ DOMAIN              │  │ FINANCIAL_EXPOS  │  │                             │  │
│  │                      │  │ SOURCE_CHUNK_ID  │  │                             │  │
│  └──────────┬───────────┘  └────────┬─────────┘  └──────────────┬──────────────┘  │
│             │                        │                            │                 │
│  ┌──────────┴──────────┐   ┌────────┴───────────┐   ┌──────────┴──────────────┐  │
│  │ CONTRACTS           │   │ SAFETY_INCIDENTS   │   │ INVOICES                │  │
│  │ SAFETY_OBSERVATIONS │   │                     │   │                          │  │
│  └─────────────────────┘   └─────────────────────┘   └─────────────────────────┘  │
│                                                                                    │
└──────────────────────────────────┬─────────────────────────────────────────────────┘
                                   │
                                   │ JOINs + Aggregation (SP_REFRESH_GOLD)
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                G O L D   L A Y E R                                │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────────────┐   ┌──────────────────────────────┐              │
│  │  PROJECT_RISK_SUMMARY       │   │  UNIFIED_RISK_MATRIX         │              │
│  │                              │   │                               │              │
│  │  PROJECT_ID (from PROJECTS)  │   │  RISK_ID (from RISK_EVENTS)  │              │
│  │  + aggregated RISK_EVENTS    │   │  + PROJECT_NAME (PROJECTS)   │              │
│  │  + FINANCIAL data            │   │  + FINANCIAL_EXPOSURE         │              │
│  │  = OVERALL_RISK_LEVEL        │   │  = RISK_LEVEL per event       │              │
│  └─────────────────────────────┘   └──────────────────────────────┘              │
│                                                                                   │
│  ┌─────────────────────────────┐   ┌──────────────────────────────┐              │
│  │  FINANCIAL_SUMMARY          │   │  VENDOR_SCORECARD            │              │
│  │                              │   │                               │              │
│  │  PROJECT_ID (from PROJECTS)  │   │  VENDOR_NAME (from VENDORS)  │              │
│  │  + INVOICES aggregated       │   │  + CONTRACTS aggregated      │              │
│  │  + CONTRACTS budget data     │   │  + RISK_EVENTS linked        │              │
│  │  = FINANCIAL_HEALTH          │   │  = COMPOSITE_SCORE           │              │
│  └─────────────────────────────┘   └──────────────────────────────┘              │
│                                                                                   │
│  ┌─────────────────────────────┐   ┌──────────────────────────────┐              │
│  │  SAFETY_DASHBOARD           │   │  VW_GRAPH_EXPLORER (DT)      │              │
│  │                              │   │  VW_RISK_HEATMAP (DT)        │              │
│  │  PROJECT_ID (from PROJECTS)  │   │                               │              │
│  │  + SAFETY_INCIDENTS count    │   │  JOINs GRAPH_NODES +         │              │
│  │  + SAFETY_OBSERVATIONS       │   │  GRAPH_EDGES + CHUNKS        │              │
│  │  = COMPLIANCE_STATUS         │   │  = Navigable graph view      │              │
│  └─────────────────────────────┘   └──────────────────────────────┘              │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Relationship Key (Foreign Keys)

| From Table | → To Table | Join Column | Relationship |
|------------|-----------|-------------|--------------|
| `DOC_PARSE_RESULTS` | → `DOCUMENT_REGISTRY` | `DOCUMENT_ID` | Many-to-One (each parse links to one doc) |
| `CHUNKS` | → `DOCUMENT_REGISTRY` | `DOCUMENT_ID` | Many-to-One (many chunks per document) |
| `VECTORS` | → `CHUNKS` | `CHUNK_ID` | One-to-One (each chunk has one vector) |
| `GRAPH_NODES` | → `DOCUMENT_REGISTRY` | `SOURCE_DOCUMENT_ID` | Many-to-One (many nodes from one doc) |
| `GRAPH_EDGES` | → `GRAPH_NODES` | `SOURCE_NODE_ID` | Many-to-One |
| `GRAPH_EDGES` | → `GRAPH_NODES` | `TARGET_NODE_ID` | Many-to-One |
| `GRAPH_EDGES` | → `CHUNKS` | `EVIDENCE_CHUNK_ID` | Many-to-One (edge proved by chunk) |
| `RISK_EVENTS` | → `PROJECTS` | `PROJECT_ID` | Many-to-One (many risks per project) |
| `RISK_EVENTS` | → `CHUNKS` | `SOURCE_CHUNK_ID` | Many-to-One (risk extracted from chunk) |
| `PROJECT_RISK_SUMMARY` | → `PROJECTS` + `RISK_EVENTS` | `PROJECT_ID` | Aggregation |
| `UNIFIED_RISK_MATRIX` | → `RISK_EVENTS` + `PROJECTS` | `RISK_ID`, `PROJECT_ID` | JOIN |
| `FINANCIAL_SUMMARY` | → `PROJECTS` + `INVOICES` + `CONTRACTS` | `PROJECT_ID` | Aggregation |
| `VENDOR_SCORECARD` | → `VENDORS` + `CONTRACTS` | `VENDOR_ID` | Aggregation |
| `SAFETY_DASHBOARD` | → `PROJECTS` + `SAFETY_INCIDENTS` | `PROJECT_ID` | Aggregation |

## Cardinality Summary

```
1 Document  ──────── produces ────────▶  1 Parse Result
1 Document  ──────── splits into ─────▶  1-20 Chunks
1 Chunk     ──────── embeds into ─────▶  1 Vector
1 Chunk     ──────── extracts ────────▶  2-8 Graph Nodes
1 Chunk     ──────── extracts ────────▶  3-12 Graph Edges
1 Project   ──────── has ─────────────▶  1-54 Risk Events
1 Project   ──────── produces ────────▶  1 row in PROJECT_RISK_SUMMARY
1 Project   ──────── produces ────────▶  1 row in FINANCIAL_SUMMARY
1 Project   ──────── produces ────────▶  1 row in SAFETY_DASHBOARD
1 Vendor    ──────── produces ────────▶  1 row in VENDOR_SCORECARD
```

---

# Appendix B: Complete Output of All Tables

## B.1 BRONZE.DOCUMENT_REGISTRY (17 rows)

```sql
SELECT DOCUMENT_ID, FILE_NAME, FILE_SIZE, FILE_TYPE, STATUS, UPLOADED_AT
FROM RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY
ORDER BY UPLOADED_AT DESC;
```

| # | DOCUMENT_ID | FILE_NAME | FILE_SIZE | FILE_TYPE | STATUS | UPLOADED_AT |
|---|-------------|-----------|-----------|-----------|--------|-------------|
| 1 | DOC-46891B3FE25B4915 | construction_risk_anomaly_test.pdf | 6,754 | pdf | PARSED | 2026-08-12 00:33:17 |
| 2 | DOC-35E04015AA30433B | construction_risk_anomaly_test.pdf | 6,754 | pdf | PARSED | 2026-08-12 00:31:21 |
| 3 | DOC-87B8897D891C4EBB | construction_risk_anomaly_test.pdf | 6,754 | pdf | PARSED | 2026-08-12 00:31:20 |
| 4 | DOC-62B2901064714DCD | construction_risk_anomaly_test.pdf | 6,754 | pdf | PARSED | 2026-08-12 00:30:23 |
| 5 | DOC-4304273BEB484582 | Monthly_Status_Report_PRJ-001_June2026.pdf | 12,788 | pdf | PARSED | 2026-08-03 06:19:27 |
| 6 | DOC-1D708F2BED354DC0 | Invoice_Package_INV-PRG001-SUP001-006.pdf | 1,124 | pdf | PARSED | 2026-08-01 23:59:41 |
| 7 | DOC-545450FA0E924489 | vendors.csv | 3,978 | csv | PARSED | 2026-08-01 23:49:50 |
| 8 | DOC-549298175A134289 | Safety_Incident_Report_PRJ-003_Q2_2026.pdf | 3,055 | pdf | PARSED | 2026-08-01 23:49:50 |
| 9 | DOC-629DD7C621174943 | Quality_Inspection_Report_PRJ-003_Q2_2026.pdf | 3,254 | pdf | PARSED | 2026-08-01 23:49:49 |
| 10 | DOC-4E18B5B449614495 | owner_ld_chain_01.eml | 1,268 | eml | PARSED | 2026-08-01 23:49:49 |
| 11 | DOC-60D33876BFD44F8D | mv_cable_chain_01.eml | 1,314 | eml | PARSED | 2026-08-01 23:49:48 |
| 12 | DOC-A9C015E9F4CF4B75 | Monthly_Status_Report_PRJ-003_June2026.pdf | 3,725 | pdf | PARSED | 2026-08-01 23:49:47 |
| 13 | DOC-1BA7AFF2EF9349B1 | Invoice_Package_INV-PRJ001-STEEL-006.pdf | 3,019 | pdf | PARSED | 2026-08-01 23:49:47 |
| 14 | DOC-64CD557E30194F1E | contract_terms_PRJ-003.txt | 923 | txt | PARSED | 2026-08-01 23:49:46 |
| 15 | DOC-3DD2CB32C33440B7 | Contract_Summary_PRJ-003_CTR-003.pdf | 2,582 | pdf | PARSED | 2026-08-01 23:49:46 |
| 16 | DOC-253F03EB17BD4E6A | Change_Order_Request_CO-PRJ003-012.pdf | 2,815 | pdf | PARSED | 2026-08-01 23:49:45 |
| 17 | DOC-A76578DCC42C4681 | Change_Order_Request_CO-PRJ001-003.pdf | 2,834 | pdf | PARSED | 2026-08-01 23:49:44 |

---

## B.2 BRONZE.DOC_PARSE_RESULTS (17 rows)

```sql
SELECT PARSE_ID, DOCUMENT_ID, LEFT(RAW_TEXT, 100) AS RAW_TEXT_PREVIEW, STATUS, CREATED_AT
FROM RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS
ORDER BY CREATED_AT DESC;
```

| # | PARSE_ID | DOCUMENT_ID | RAW_TEXT_PREVIEW | STATUS | CREATED_AT |
|---|----------|-------------|------------------|--------|------------|
| 1 | 877a6766-0f1b-... | DOC-62B2901064714DCD | `{"content":"# Construction Risk Intelligence - Test Document\n\nSynthetic project record designed to...` | SUCCESS | 2026-08-16 23:12:18 |
| 2 | 02c6d3e1-1e9c-... | DOC-87B8897D891C4EBB | `{"content":"# Construction Risk Intelligence - Test Document\n\nSynthetic project record designed to...` | SUCCESS | 2026-08-16 23:12:09 |
| 3 | 41dd9b6f-5977-... | DOC-35E04015AA30433B | `{"content":"# Construction Risk Intelligence - Test Document\n\nSynthetic project record designed to...` | SUCCESS | 2026-08-16 23:12:00 |
| 4 | 548367d7-6c78-... | DOC-46891B3FE25B4915 | `{"content":"# Construction Risk Intelligence - Test Document\n\nSynthetic project record designed to...` | SUCCESS | 2026-08-16 23:11:51 |
| 5 | 7885437c-7b49-... | DOC-4304273BEB484582 | `{"content":"Coco Constructions\nConstruction Lifecycle Record \| Internal\n\n# Monthly Status Report...` | SUCCESS | 2026-08-03 06:19:43 |
| 6 | 90026dea-6766-... | DOC-1D708F2BED354DC0 | `{"content":"# Supplier Invoice & Payment Dispute Package\n\nInvoice ID: INV-PRG001-SUP001-006 \|...` | SUCCESS | 2026-08-01 23:59:47 |
| 7 | 85429823-20fb-... | DOC-545450FA0E924489 | `vendor_id,vendor_name,legal_name,trade_category,trade_code,primary_contact,contact_email,perform...` | SUCCESS | 2026-08-01 23:51:24 |
| 8 | 98a679b0-5885-... | DOC-549298175A134289 | `{"content":"# Coco Constructions\n\n# Safety Incident Report - Project Atlas Data Center\n\nQ2 2026...` | SUCCESS | 2026-08-01 23:51:18 |
| 9 | ad2e272c-91fc-... | DOC-629DD7C621174943 | `{"content":"# Coco Constructions\n\n# Quality Inspection Report - Project Atlas Data Center\n\nQ2 20...` | SUCCESS | 2026-08-01 23:51:10 |
| 10 | 984a2ac9-8f0e-... | DOC-4E18B5B449614495 | `From: project.controls@cococonstructions.example\nDate: Tue, 02 Jun 2026 09:30:00\nSubject: [PRJ...` | SUCCESS | 2026-08-01 23:51:09 |
| 11 | e077d8a4-1a6d-... | DOC-60D33876BFD44F8D | `From: project.controls@cococonstructions.example\nDate: Tue, 02 Jun 2026 10:30:00\nSubject: [PRJ...` | SUCCESS | 2026-08-01 23:51:08 |
| 12 | 536b66dc-e79c-... | DOC-A9C015E9F4CF4B75 | `{"content":"# Coco Constructions\n\n# Monthly Status Report - Project Atlas Data Center\n\nReport Pe...` | SUCCESS | 2026-08-01 23:51:03 |
| 13 | 039b4e0f-7f80-... | DOC-1BA7AFF2EF9349B1 | `{"content":"# Coco Constructions\n\n# Invoice Package - INV-PRJ001-STEEL-006\n\nBilling Period: 2026...` | SUCCESS | 2026-08-01 23:50:18 |
| 14 | 783cd8da-68b5-... | DOC-64CD557E30194F1E | `{"content":"Coco Constructions\n\nContract Narrative File\n\nProject ID: PRJ-003\n\nProject Name: Pr...` | SUCCESS | 2026-08-01 23:50:15 |
| 15 | 3f13140f-5471-... | DOC-3DD2CB32C33440B7 | `{"content":"# Coco Constructions\n\n# Contract Summary - Project Atlas Data Center\n\nContract ID: C...` | SUCCESS | 2026-08-01 23:50:11 |
| 16 | 2c36b166-f3de-... | DOC-253F03EB17BD4E6A | `{"content":"Confidential - Synthetic hackathon demo data - Coco Constructions\nPage 1\n\n# Coco Cons...` | SUCCESS | 2026-08-01 23:50:06 |
| 17 | 21d71707-e0a1-... | DOC-A76578DCC42C4681 | `{"content":"Confidential - Synthetic hackathon demo data - Coco Constructions\nPage 1\n\n# Coco Cons...` | SUCCESS | 2026-08-01 23:49:58 |

---

## B.3 SILVER.CHUNKS (30 rows shown of total)

```sql
SELECT CHUNK_ID, DOCUMENT_ID, CHUNK_INDEX, LEFT(CHUNK_TEXT, 80) AS CHUNK_TEXT_PREVIEW, PAGE_NUMBER
FROM RISK_COMMAND_CENTER.SILVER.CHUNKS
ORDER BY CREATED_AT DESC, CHUNK_INDEX;
```

| # | CHUNK_ID | DOCUMENT_ID | IDX | CHUNK_TEXT_PREVIEW | PG |
|---|----------|-------------|-----|--------------------|----|
| 1 | CHK-FFDD1D3F588B | DOC-46891B3FE25B4915 | 0 | `# Construction Risk Intelligence - Test Document Synthetic project record desig...` | 1 |
| 2 | CHK-7F14AE8586D8 | DOC-46891B3FE25B4915 | 1 | `1. Weekly Site Risk & Performance Records \| Date \| Zone \| Work Item \| Prog...` | 1 |
| 3 | CHK-58625C7F1336 | DOC-46891B3FE25B4915 | 2 | `2. Material, Equipment & Safety Observations \| Record ID \| Date \| Category...` | 1 |
| 4 | CHK-E69D41FDD4E3 | DOC-46891B3FE25B4915 | 3 | `3. Risk Register \| Risk ID \| Risk \| Probability \| Impact \| Risk Score \| Owner...` | 1 |
| 5 | CHK-EF02AD983E35 | DOC-46891B3FE25B4915 | 4 | `4. Incident Notes \| INC-101 \| 10-Aug \| Tower C \| Worker slipped near wet slab...` | 2 |
| 6 | CHK-5A81D322B82D | DOC-35E04015AA30433B | 0 | `# Construction Risk Intelligence - Test Document Synthetic project record desig...` | 1 |
| 7 | CHK-63A576C30886 | DOC-35E04015AA30433B | 1 | `1. Weekly Site Risk & Performance Records \| Date \| Zone \| Work Item \| Prog...` | 1 |
| 8 | CHK-940DD1B01638 | DOC-35E04015AA30433B | 2 | `2. Material, Equipment & Safety Observations \| Record ID \| Date \| Category...` | 1 |
| 9 | CHK-5EA3B0A0B79F | DOC-35E04015AA30433B | 3 | `3. Risk Register \| Risk ID \| Risk \| Probability \| Impact \| Risk Score \| Owner...` | 1 |
| 10 | CHK-A9FE671721D5 | DOC-35E04015AA30433B | 4 | `4. Incident Notes \| INC-101 \| 10-Aug \| Tower C \| Worker slipped near wet slab...` | 2 |
| 11 | CHK-3A64AB9E612F | DOC-87B8897D891C4EBB | 0 | `# Construction Risk Intelligence - Test Document Synthetic project record desig...` | 1 |
| 12 | CHK-C8366D14030F | DOC-87B8897D891C4EBB | 1 | `1. Weekly Site Risk & Performance Records \| Date \| Zone \| Work Item \| Prog...` | 1 |
| 13 | CHK-3ED7452F722C | DOC-87B8897D891C4EBB | 2 | `2. Material, Equipment & Safety Observations \| Record ID \| Date \| Category...` | 1 |
| 14 | CHK-7BF98BE50887 | DOC-87B8897D891C4EBB | 3 | `3. Risk Register \| Risk ID \| Risk \| Probability \| Impact \| Risk Score \| Owner...` | 1 |
| 15 | CHK-8B05AE8D8354 | DOC-87B8897D891C4EBB | 4 | `4. Incident Notes \| INC-101 \| 10-Aug \| Tower C \| Worker slipped near wet slab...` | 2 |
| 16 | CHK-4A4F962B4902 | DOC-62B2901064714DCD | 0 | `# Construction Risk Intelligence - Test Document Synthetic project record desig...` | 1 |
| 17 | CHK-2C90F6C088A5 | DOC-62B2901064714DCD | 1 | `1. Weekly Site Risk & Performance Records \| Date \| Zone \| Work Item \| Prog...` | 1 |
| 18 | CHK-47CFFD91704D | DOC-62B2901064714DCD | 2 | `2. Material, Equipment & Safety Observations \| Record ID \| Date \| Category...` | 1 |
| 19 | CHK-8674B622F41A | DOC-62B2901064714DCD | 3 | `3. Risk Register \| Risk ID \| Risk \| Probability \| Impact \| Risk Score \| Owner...` | 1 |
| 20 | CHK-AFC1C364D1B8 | DOC-62B2901064714DCD | 4 | `4. Incident Notes \| INC-101 \| 10-Aug \| Tower C \| Worker slipped near wet slab...` | 2 |
| 21 | CHK-93398115A5D9 | DOC-4304273BEB484582 | 0 | `Coco Constructions Construction Lifecycle Record \| Internal` | 1 |
| 22 | CHK-9E6DA782D1CB | DOC-4304273BEB484582 | 1 | `Monthly Status Report - PRJ-001 June 2026 ## 1. Executive Status Snapshot \| P...` | 1 |
| 23 | CHK-DE2917FE8CD7 | DOC-4304273BEB484582 | 2 | `5. Manpower, Safety and Quality Evidence \| work_date \| trade \| worker_count \|...` | 1 |
| 24 | CHK-91BFFF46ED64 | DOC-4304273BEB484582 | 3 | `6. Top Risk Events and Actions \| risk_id \| risk_category \| risk_title \| severi...` | 1 |
| 25 | CHK-664AA64183FD | DOC-1D708F2BED354DC0 | 0 | `# Supplier Invoice & Payment Dispute Package Invoice ID: INV-PRG001-SUP001-...` | 1 |
| 26 | CHK-799B4E4D77E5 | DOC-549298175A134289 | 1 | `Safety Incident Report - Project Atlas Data Center Q2 2026 \| Project ID: PRJ-00...` | 1 |
| 27 | CHK-08CF0356836E | DOC-629DD7C621174943 | 1 | `Quality Inspection Report - Project Atlas Data Center Q2 2026 \| Project ID: PRJ...` | 1 |
| 28 | CHK-C74B330B7F62 | DOC-4E18B5B449614495 | 0 | `From: project.controls@cococonstructions.example Date: Tue, 02 Jun 2026 09:30...` | 1 |
| 29 | CHK-40A5BA88B87D | DOC-60D33876BFD44F8D | 0 | `From: project.controls@cococonstructions.example Date: Tue, 02 Jun 2026 10:30...` | 1 |
| 30 | CHK-5C182BB6CD6B | DOC-A9C015E9F4CF4B75 | 1 | `Monthly Status Report - Project Atlas Data Center Report Period: June 2026 \| Pr...` | 1 |

---

## B.4 SILVER.GRAPH_NODES (15 rows shown of 295 total)

```sql
SELECT NODE_ID, NODE_TYPE, NODE_NAME, PROPERTIES, SOURCE_DOCUMENT_ID
FROM RISK_COMMAND_CENTER.SILVER.GRAPH_NODES
ORDER BY CREATED_AT DESC LIMIT 15;
```

| # | NODE_ID | NODE_TYPE | NODE_NAME | PROPERTIES | SOURCE_DOC |
|---|---------|-----------|-----------|------------|------------|
| 1 | N-3DEDE8CA006E | Milestone | PRJ-CON-2026-017 | `{"source_chunk":"CHK-5A81D322B82D"}` | DOC-35E04015AA30433B |
| 2 | N-37711DA4415F | Person | Equipment Lead | `{"source_chunk":"CHK-8674B622F41A"}` | DOC-62B2901064714DCD |
| 3 | N-AAA5E8AAB425 | Person | Worker | `{"source_chunk":"CHK-AFC1C364D1B8"}` | DOC-62B2901064714DCD |
| 4 | N-16382FE467EF | Risk | R-002 - Schedule slippage in Tower C | `{"source_chunk":"CHK-7BF98BE50887"}` | DOC-87B8897D891C4EBB |
| 5 | N-538F0C670854 | Risk | R-005 - Crane downtime | `{"source_chunk":"CHK-5EA3B0A0B79F"}` | DOC-35E04015AA30433B |
| 6 | N-AF7E91709AC5 | Vendor | VoltPath Electrical Systems | `{"source_chunk":"CHK-58625C7F1336"}` | DOC-46891B3FE25B4915 |
| 7 | N-8B6E38998BBB | Risk | Concrete Strength | `{"source_chunk":"CHK-C8366D14030F"}` | DOC-87B8897D891C4EBB |
| 8 | N-CB9E1A27C926 | Project | INC-101 | `{"source_chunk":"CHK-A9FE671721D5"}` | DOC-35E04015AA30433B |
| 9 | N-A2F45C429FFE | Risk | R-001 - Concrete quality deterioration | `{"source_chunk":"CHK-E69D41FDD4E3"}` | DOC-46891B3FE25B4915 |
| 10 | N-FD84C0498103 | Risk | Safety Incidents | `{"source_chunk":"CHK-2C90F6C088A5"}` | DOC-62B2901064714DCD |
| 11 | N-5299F1710BE8 | Vendor | VoltPath Electrical Systems | `{"source_chunk":"CHK-3ED7452F722C"}` | DOC-87B8897D891C4EBB |
| 12 | N-AF7E91709AC5 | Vendor | VoltPath Electrical Systems | `{"source_chunk":"CHK-FFDD1D3F588B"}` | DOC-46891B3FE25B4915 |
| 13 | N-7B561656C7EA | Risk | R-005 - Crane downtime | `{"source_chunk":"CHK-7BF98BE50887"}` | DOC-87B8897D891C4EBB |
| 14 | N-628AF9B3B9CC | Risk | R-004 - Unplanned cost escalation | `{"source_chunk":"CHK-5EA3B0A0B79F"}` | DOC-35E04015AA30433B |
| 15 | N-117C7950A257 | Project | PRJ-CON-2026-017 | `{"source_chunk":"CHK-3A64AB9E612F"}` | DOC-87B8897D891C4EBB |

---

## B.5 SILVER.GRAPH_EDGES (15 rows shown of 13,010 total)

```sql
SELECT EDGE_ID, SOURCE_NODE_ID, TARGET_NODE_ID, RELATIONSHIP_TYPE, CONFIDENCE
FROM RISK_COMMAND_CENTER.SILVER.GRAPH_EDGES
ORDER BY CREATED_AT DESC LIMIT 15;
```

| # | EDGE_ID | SOURCE_NODE_ID | TARGET_NODE_ID | RELATIONSHIP_TYPE | CONFIDENCE |
|---|---------|----------------|----------------|-------------------|------------|
| 1 | E-E27262B7C9C1 | N-5299F1710BE8 | N-AEB80A508AF7 | COSTS | 0.8 |
| 2 | E-D1909BB25B8E | N-5299F1710BE8 | N-AEB80A508AF7 | MANAGES | 0.8 |
| 3 | E-E89084A40FDF | N-5299F1710BE8 | N-519B3E256B94 | MANAGES | 0.8 |
| 4 | E-D1909BB25B8E | N-5299F1710BE8 | N-30BDCD48D636 | MANAGES | 0.8 |
| 5 | E-E89084A40FDF | N-5299F1710BE8 | N-AEB80A508AF7 | MANAGES | 0.8 |
| 6 | E-D1909BB25B8E | N-5299F1710BE8 | N-F09D517FD75C | MANAGES | 0.8 |
| 7 | E-E27262B7C9C1 | N-5299F1710BE8 | N-F09D517FD75C | COSTS | 0.8 |
| 8 | E-E89084A40FDF | N-5299F1710BE8 | N-30BDCD48D636 | MANAGES | 0.8 |
| 9 | E-E27262B7C9C1 | N-5299F1710BE8 | N-30BDCD48D636 | COSTS | 0.8 |
| 10 | E-E89084A40FDF | N-5299F1710BE8 | N-F09D517FD75C | MANAGES | 0.8 |
| 11 | E-D1909BB25B8E | N-5299F1710BE8 | N-519B3E256B94 | MANAGES | 0.8 |
| 12 | E-E27262B7C9C1 | N-5299F1710BE8 | N-519B3E256B94 | COSTS | 0.8 |
| 13 | E-E27262B7C9C1 | N-5299F1710BE8 | N-AEB80A508AF7 | COSTS | 0.8 |
| 14 | E-E89084A40FDF | N-5299F1710BE8 | N-AEB80A508AF7 | MANAGES | 0.8 |
| 15 | E-D1909BB25B8E | N-5299F1710BE8 | N-AEB80A508AF7 | MANAGES | 0.8 |

---

## B.6 SILVER.PROJECTS (5 rows)

```sql
SELECT PROJECT_ID, PROJECT_NAME, CURRENT_CONTRACT_VALUE, PERCENT_COMPLETE, SCHEDULE_STATUS, COST_STATUS, DOMAIN
FROM RISK_COMMAND_CENTER.SILVER.PROJECTS;
```

| # | PROJECT_ID | PROJECT_NAME | CURRENT_CONTRACT_VALUE | % COMPLETE | SCHEDULE_STATUS | COST_STATUS | DOMAIN |
|---|------------|--------------|------------------------|------------|-----------------|-------------|--------|
| 1 | INV-PRG001-SUP001-006 | Supplier Invoice & Payment Dispute Package | — | — | — | — | healthcare |
| 2 | CON-2026-017 | Riverside Commercial Complex | $485,000,000 | — | At Risk | — | construction |
| 3 | PRJ-001 | Project Phoenix Medical Tower | $10,225,000 | 46% | At Risk | — | construction |
| 4 | PRJ-003 | Atlas Data Center | $232,000,000 | — | — | — | construction |
| 5 | PRJ001 | Project Phoenix Medical Tower | — | — | Delayed | — | construction |

---

## B.7 SILVER.RISK_EVENTS (8 rows shown)

```sql
SELECT RISK_ID, PROJECT_ID, RISK_CATEGORY, LEFT(RISK_TITLE, 60) AS RISK_TITLE, SEVERITY, FINANCIAL_EXPOSURE, STATUS, DOMAIN
FROM RISK_COMMAND_CENTER.SILVER.RISK_EVENTS LIMIT 8;
```

| # | RISK_ID | PROJECT_ID | RISK_CATEGORY | RISK_TITLE | SEVERITY | FINANCIAL_EXPOSURE | STATUS | DOMAIN |
|---|---------|------------|---------------|------------|----------|-------------------|--------|--------|
| 1 | RSK-633B4AA7 | PRJ-001 | General | Major routing conflicts between HVAC, structural steel and p... | Medium | — | OPEN | construction |
| 2 | RSK-DB0BB7B8 | PRJ-003 | Schedule | Medium Voltage Cable Customs Delay Recovery Plan | MEDIUM | — | UNDER_REVIEW | construction |
| 3 | RSK-D09C4173 | PRJ-003 | Schedule | cable delayed at customs | High | — | Closed | construction |
| 4 | RSK-15743F67 | PRJ-003 | Budget | Project Atlas cost overrun | Critical | $66,000,000 | OPEN | construction |
| 5 | RSK-4DE18C84 | PRJ-003 | Contract | Liquidated damages exposure | Critical | $50,000 | OPEN | construction |
| 6 | RSK-C7135CC4 | PRJ-003 | Vendor | Medium-voltage cable stuck at customs | High | — | OPEN | construction |
| 7 | RSK-7B0FC19E | PRJ-003 | Environmental | Soil contamination notification | High | — | OPEN | construction |
| 8 | RSK-70ECB0B1 | PRJ-003 | Quality | Concrete flatness failure | High | — | OPEN | construction |

---

## B.8 SILVER.VENDORS (4 rows)

```sql
SELECT VENDOR_ID, VENDOR_NAME, TRADE_CATEGORY, PERFORMANCE_GRADE, DOMAIN
FROM RISK_COMMAND_CENTER.SILVER.VENDORS;
```

| # | VENDOR_ID | VENDOR_NAME | TRADE_CATEGORY | PERFORMANCE_GRADE | DOMAIN |
|---|-----------|-------------|----------------|-------------------|--------|
| 1 | VND-004 | VoltPath Electrical Systems | General | B | construction |
| 2 | VND-80236B | Apex MedTech Solutions | General | B | healthcare |
| 3 | VND-003 Mesa Mechanical Sy | Mesa Mechanical Systems | General | B | construction |
| 4 | VND-002 Northline Steelwor | Northline Steelwor | General | B | construction |

---

## B.9 GOLD.PROJECT_RISK_SUMMARY (5 rows)

```sql
SELECT PROJECT_ID, PROJECT_NAME, SCHEDULE_STATUS, COST_STATUS, CURRENT_BUDGET,
       TOTAL_RISKS, HIGH_CRITICAL_RISKS, TOTAL_RISK_EXPOSURE, OVERALL_RISK_LEVEL, DOMAIN
FROM RISK_COMMAND_CENTER.GOLD.PROJECT_RISK_SUMMARY;
```

| # | PROJECT_ID | PROJECT_NAME | SCHEDULE | COST | CURRENT_BUDGET | TOTAL_RISKS | HIGH/CRIT | RISK_EXPOSURE | RISK_LEVEL | DOMAIN |
|---|------------|--------------|----------|------|----------------|-------------|-----------|---------------|------------|--------|
| 1 | INV-PRG001-SUP001-006 | Supplier Invoice & Payment Dispute | — | On Budget | $0 | 1 | 1 | $0 | High | healthcare |
| 2 | PRJ-003 | Atlas Data Center | — | On Budget | $232,000,000 | 15 | 10 | $66,050,000 | Critical | construction |
| 3 | CON-2026-017 | Riverside Commercial Complex | At Risk | On Budget | $485,000,000 | 54 | 37 | $55 | High | construction |
| 4 | PRJ001 | Project Phoenix Medical Tower | Delayed | On Budget | $0 | 7 | 4 | $640,000 | High | construction |
| 5 | PRJ-001 | Project Phoenix Medical Tower | At Risk | On Budget | $10,225,000 | 10 | 8 | $0 | High | construction |

---

## B.10 GOLD.UNIFIED_RISK_MATRIX (15 rows shown)

```sql
SELECT RISK_ID, PROJECT_NAME, RISK_CATEGORY, LEFT(RISK_TITLE, 60) AS RISK_TITLE, SEVERITY, RISK_SCORE, TOTAL_FINANCIAL_EXPOSURE, RISK_LEVEL
FROM RISK_COMMAND_CENTER.GOLD.UNIFIED_RISK_MATRIX LIMIT 15;
```

| # | RISK_ID | PROJECT_NAME | CATEGORY | RISK_TITLE | SEVERITY | SCORE | EXPOSURE | LEVEL |
|---|---------|--------------|----------|------------|----------|-------|----------|-------|
| 1 | RSK-5C7D886C | Supplier Invoice & Payment Dispute | Quality | Expedited surcharge for cardiac monitors disputed... | High | 40 | $0 | Medium |
| 2 | RSK-633B4AA7 | Project Phoenix Medical Tower | General | Major routing conflicts between HVAC, structural... | Medium | 40 | $0 | Medium |
| 3 | RSK-15743F67 | Atlas Data Center | Budget | Project Atlas cost overrun | Critical | 40 | $85,800,000 | Medium |
| 4 | RSK-4DE18C84 | Atlas Data Center | Contract | Liquidated damages exposure | Critical | 40 | $65,000 | Medium |
| 5 | RSK-C7135CC4 | Atlas Data Center | Vendor | Medium-voltage cable stuck at customs | High | 40 | $0 | Medium |
| 6 | RSK-7B0FC19E | Atlas Data Center | Environmental | Soil contamination notification | High | 40 | $0 | Medium |
| 7 | RSK-70ECB0B1 | Atlas Data Center | Quality | Concrete flatness failure | High | 40 | $0 | Medium |
| 8 | RSK-4DAA213D | Atlas Data Center | Quality | Concrete flatness testing failed in multiple aisles | Critical | 40 | $0 | Medium |
| 9 | RSK-998CB93E | Atlas Data Center | Quality | Deficiencies require correction before covering work | High | 40 | $0 | Medium |
| 10 | RSK-2EB55FA8 | Atlas Data Center | Quality | Critical issue requires engineer review before... | Critical | 40 | $0 | Medium |
| 11 | RSK-FA8767EB | Atlas Data Center | Quality | Work generally acceptable with punch list items | Low | 40 | $0 | Medium |
| 12 | RSK-0F9E283F | Atlas Data Center | Quality | Inspection performed against approved drawings... | Low | 40 | $0 | Medium |
| 13 | RSK-EDB72737 | Atlas Data Center | General | Equipment struck temporary barricade | LOW | 40 | $0 | Medium |
| 14 | RSK-5AA9BD1F | Atlas Data Center | General | Crane swing path entered restricted zone | HIGH | 40 | $0 | Medium |
| 15 | RSK-731CB7AF | Atlas Data Center | General | Fuel spill observed near generator | MEDIUM | 40 | $0 | Medium |

---

## B.11 GOLD.FINANCIAL_SUMMARY (5 rows)

```sql
SELECT PROJECT_ID, PROJECT_NAME, APPROVED_BUDGET, FORECAST_COST_AT_COMPLETION, FORECAST_VARIANCE,
       TOTAL_CONTRACT_VALUE, COST_STATUS, FINANCIAL_HEALTH, DOMAIN
FROM RISK_COMMAND_CENTER.GOLD.FINANCIAL_SUMMARY;
```

| # | PROJECT_ID | PROJECT_NAME | APPROVED_BUDGET | FORECAST_COST | VARIANCE | CONTRACT_VALUE | COST_STATUS | HEALTH | DOMAIN |
|---|------------|--------------|-----------------|---------------|----------|----------------|-------------|--------|--------|
| 1 | INV-PRG001-SUP001-006 | Supplier Invoice & Payment Dispute | $0 | $0 | $0 | $0 | On Budget | Healthy | healthcare |
| 2 | PRJ-003 | Atlas Data Center | $232,000,000 | $232,000,000 | -$232,000,000 | $232,000,000 | On Budget | Healthy | construction |
| 3 | PRJ001 | Project Phoenix Medical Tower | $0 | $0 | $0 | $0 | On Budget | Healthy | construction |
| 4 | CON-2026-017 | Riverside Commercial Complex | $485,000,000 | $485,000,000 | -$485,000,000 | $485,000,000 | On Budget | Healthy | construction |
| 5 | PRJ-001 | Project Phoenix Medical Tower | $10,225,000 | $0 | -$10,225,000 | $10,225,000 | On Budget | Healthy | construction |

---

## B.12 GOLD.VENDOR_SCORECARD (4 rows)

```sql
SELECT VENDOR_NAME, TRADE_CATEGORY, PERFORMANCE_GRADE, ACTIVE_PROJECTS, TOTAL_SUBCONTRACT_VALUE, COMPOSITE_SCORE
FROM RISK_COMMAND_CENTER.GOLD.VENDOR_SCORECARD;
```

| # | VENDOR_NAME | TRADE_CATEGORY | PERFORMANCE_GRADE | ACTIVE_PROJECTS | TOTAL_SUBCONTRACT_VALUE | COMPOSITE_SCORE |
|---|-------------|----------------|-------------------|-----------------|------------------------|-----------------|
| 1 | Apex MedTech Solutions | General | B | 0 | $0 | 25 |
| 2 | VoltPath Electrical Systems | General | B | 0 | $0 | 25 |
| 3 | Mesa Mechanical Systems | General | B | 0 | $0 | 25 |
| 4 | Northline Steelwor | General | B | 0 | $0 | 25 |

---

## B.13 GOLD.SAFETY_DASHBOARD (5 rows)

```sql
SELECT PROJECT_ID, PROJECT_NAME, TOTAL_INCIDENTS, SEVERE_INCIDENTS, LOST_TIME_INCIDENTS,
       DAYS_SINCE_LAST_INCIDENT, SAFETY_RISK_LEVEL, COMPLIANCE_STATUS, DOMAIN
FROM RISK_COMMAND_CENTER.GOLD.SAFETY_DASHBOARD;
```

| # | PROJECT_ID | PROJECT_NAME | TOTAL_INCIDENTS | SEVERE | LOST_TIME | DAYS_SINCE_LAST | SAFETY_RISK | COMPLIANCE | DOMAIN |
|---|------------|--------------|-----------------|--------|-----------|-----------------|-------------|------------|--------|
| 1 | INV-PRG001-SUP001-006 | Supplier Invoice & Payment Dispute | 0 | 0 | 0 | 578 | Low | Compliant | healthcare |
| 2 | PRJ001 | Project Phoenix Medical Tower | 0 | 0 | 0 | 592 | Low | Compliant | construction |
| 3 | PRJ-003 | Atlas Data Center | 0 | 0 | 0 | 592 | Low | Compliant | construction |
| 4 | PRJ-001 | Project Phoenix Medical Tower | 0 | 0 | 0 | 592 | Low | Compliant | construction |
| 5 | CON-2026-017 | Riverside Commercial Complex | 0 | 0 | 0 | 592 | Low | Compliant | construction |

---

# Appendix C: File Type Processing Matrix

| File Extension | Processing Method | Chunking Strategy | Example |
|----------------|------------------|-------------------|---------|
| `.pdf` | PARSE_DOCUMENT (LAYOUT mode) | Split on `\n# ` headings | Monthly reports, contracts |
| `.docx` | PARSE_DOCUMENT (LAYOUT mode) | Split on `\n# ` headings | Formal documents |
| `.pptx` | PARSE_DOCUMENT (LAYOUT mode) | Split on `\n# ` headings | Presentations |
| `.txt` | PARSE_DOCUMENT (LAYOUT mode) | Split on `\n# ` headings | Contract terms |
| `.png/.jpg/.tiff` | PARSE_DOCUMENT (OCR mode) | Split on `\n# ` headings | Scanned documents |
| `.csv` | Direct byte read | 20-row batches with header | Vendor lists, timesheets |
| `.eml/.msg` | Python email parser | Single chunk (entire email) | Chain-of-custody emails |
| `.json/.xml/.log` | Direct byte read | Split on `\n# ` headings | System logs, configs |

---

# Appendix D: Quick Reference Card

### Upload a File

```sql
PUT file:///path/to/file.pdf
    @RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE/upload/
    AUTO_COMPRESS = FALSE;
```

### List Files on Stage

```sql
LIST @RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE;
```

### Run Full Pipeline

```sql
CALL RISK_COMMAND_CENTER.OPS.SP_RUN_FULL_PIPELINE();
```

### Check Document Status

```sql
SELECT FILE_NAME, STATUS
FROM RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY
ORDER BY UPLOADED_AT DESC;
```

### View Chunks for a Document

```sql
SELECT CHUNK_INDEX, PAGE_NUMBER, LEFT(CHUNK_TEXT, 200) AS PREVIEW
FROM RISK_COMMAND_CENTER.SILVER.CHUNKS
WHERE DOCUMENT_ID = '<your_document_id>'
ORDER BY CHUNK_INDEX;
```

### Semantic Search (Find Relevant Chunks by Meaning)

```sql
SELECT
    c.CHUNK_TEXT,
    VECTOR_COSINE_SIMILARITY(
        v.EMBEDDING_VECTOR,
        SNOWFLAKE.CORTEX.EMBED_TEXT_1024('voyage-multilingual-2', '<your question here>')
    ) AS similarity
FROM RISK_COMMAND_CENTER.SILVER.VECTORS v
JOIN RISK_COMMAND_CENTER.SILVER.CHUNKS c ON v.CHUNK_ID = c.CHUNK_ID
ORDER BY similarity DESC
LIMIT 5;
```

### See All Risks (Sorted by Financial Exposure)

```sql
SELECT *
FROM RISK_COMMAND_CENTER.GOLD.UNIFIED_RISK_MATRIX
ORDER BY TOTAL_FINANCIAL_EXPOSURE DESC;
```

### See Project Health Summary

```sql
SELECT *
FROM RISK_COMMAND_CENTER.GOLD.PROJECT_RISK_SUMMARY;
```

### Reset Everything (Delete All Data)

```sql
-- Bronze
TRUNCATE TABLE RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY;
TRUNCATE TABLE RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS;
REMOVE @RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE;

-- Silver
TRUNCATE TABLE RISK_COMMAND_CENTER.SILVER.CHUNKS;
TRUNCATE TABLE RISK_COMMAND_CENTER.SILVER.VECTORS;
TRUNCATE TABLE RISK_COMMAND_CENTER.SILVER.GRAPH_NODES;
TRUNCATE TABLE RISK_COMMAND_CENTER.SILVER.GRAPH_EDGES;

-- Gold
TRUNCATE TABLE RISK_COMMAND_CENTER.GOLD.PROJECT_RISK_SUMMARY;
TRUNCATE TABLE RISK_COMMAND_CENTER.GOLD.UNIFIED_RISK_MATRIX;
TRUNCATE TABLE RISK_COMMAND_CENTER.GOLD.FINANCIAL_SUMMARY;
TRUNCATE TABLE RISK_COMMAND_CENTER.GOLD.VENDOR_SCORECARD;
TRUNCATE TABLE RISK_COMMAND_CENTER.GOLD.SAFETY_DASHBOARD;
```

---

*Document generated from the live RISK_COMMAND_CENTER database on Snowflake account syc95319.*
*Last updated: August 2026*
