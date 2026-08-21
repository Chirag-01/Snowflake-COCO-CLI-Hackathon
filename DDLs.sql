create or replace database RISK_COMMAND_CENTER;

create or replace schema RISK_COMMAND_CENTER.AI;

create or replace schema RISK_COMMAND_CENTER.BRONZE;

create or replace TABLE RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY (
	DOCUMENT_ID VARCHAR(16777216) NOT NULL,
	FILE_NAME VARCHAR(16777216),
	FILE_PATH VARCHAR(16777216),
	FILE_SIZE NUMBER(38,0),
	FILE_TYPE VARCHAR(16777216),
	STATUS VARCHAR(16777216) DEFAULT 'UPLOADED',
	UPLOADED_AT TIMESTAMP_NTZ(9) DEFAULT CURRENT_TIMESTAMP(),
	DOMAIN VARCHAR(50) DEFAULT 'construction',
	primary key (DOCUMENT_ID)
);
create or replace TABLE RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS (
	PARSE_ID VARCHAR(16777216) DEFAULT UUID_STRING(),
	DOCUMENT_ID VARCHAR(16777216),
	RAW_TEXT VARCHAR(16777216),
	PARSED_JSON VARIANT,
	STATUS VARCHAR(16777216),
	CREATED_AT TIMESTAMP_NTZ(9) DEFAULT CURRENT_TIMESTAMP()
);
create or replace TABLE RISK_COMMAND_CENTER.BRONZE.RAW_STRUCTURED_PAYLOADS (
	PAYLOAD_ID VARCHAR(16777216) DEFAULT UUID_STRING(),
	SOURCE_FILE_NAME VARCHAR(16777216),
	RECORD_DATA VARIANT,
	INGESTED_AT TIMESTAMP_NTZ(9) DEFAULT CURRENT_TIMESTAMP()
);
CREATE OR REPLACE FILE FORMAT RISK_COMMAND_CENTER.BRONZE.CSV_FF
	SKIP_HEADER = 1
	TRIM_SPACE = TRUE
	FIELD_OPTIONALLY_ENCLOSED_BY = '\"'
	NULL_IF = ('', 'NULL', 'None')
;
CREATE OR REPLACE FILE FORMAT RISK_COMMAND_CENTER.BRONZE.CSV_HDR
	PARSE_HEADER = TRUE
	TRIM_SPACE = TRUE
	FIELD_OPTIONALLY_ENCLOSED_BY = '\"'
;
CREATE OR REPLACE FILE FORMAT RISK_COMMAND_CENTER.BRONZE.CSV_HEADER_FORMAT
	PARSE_HEADER = TRUE
	TRIM_SPACE = TRUE
	FIELD_OPTIONALLY_ENCLOSED_BY = '\"'
	ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
;
create or replace schema RISK_COMMAND_CENTER.GOLD;

create or replace TABLE RISK_COMMAND_CENTER.GOLD.FINANCIAL_SUMMARY (
	PROJECT_ID VARCHAR(16777216),
	PROJECT_NAME VARCHAR(16777216),
	APPROVED_BUDGET NUMBER(18,2),
	ACTUAL_COST_TO_DATE NUMBER(18,2),
	FORECAST_COST_AT_COMPLETION FLOAT,
	BUDGET_UTILIZATION_PCT NUMBER(30,1),
	FORECAST_VARIANCE NUMBER(19,2),
	TOTAL_INVOICED NUMBER(1,0),
	INVOICE_COUNT NUMBER(1,0),
	TOTAL_CONTRACT_VALUE NUMBER(18,2),
	TOTAL_CHANGE_ORDERS NUMBER(1,0),
	ACTIVE_SUBCONTRACTS NUMBER(1,0),
	CURRENT_CONTRACT_VALUE NUMBER(18,2),
	LD_PER_DAY NUMBER(1,0),
	CRITICAL_PATH_FLOAT_DAYS NUMBER(1,0),
	LD_EXPOSURE NUMBER(1,0),
	COST_OVERRUN NUMBER(1,0),
	PAYMENT_HELD_AMOUNT NUMBER(1,0),
	TOTAL_RISK_EXPOSURE NUMBER(18,2),
	TOTAL_COMBINED_EXPOSURE NUMBER(18,2),
	COST_STATUS VARCHAR(11),
	FINANCIAL_HEALTH VARCHAR(10),
	REFRESHED_AT TIMESTAMP_LTZ(9),
	DOMAIN VARCHAR(50) DEFAULT 'construction'
);
create or replace TABLE RISK_COMMAND_CENTER.GOLD.PROJECT_RISK_SUMMARY (
	PROJECT_ID VARCHAR(16777216),
	PROJECT_NAME VARCHAR(16777216),
	PROJECT_TYPE VARCHAR(16777216),
	LOCATION VARCHAR(16777216),
	CLIENT VARCHAR(16777216),
	PROJECT_MANAGER VARCHAR(16777216),
	START_DATE DATE,
	PLANNED_COMPLETION DATE,
	FORECAST_COMPLETION DATE,
	SCHEDULE_VARIANCE_DAYS NUMBER(9,0),
	PERCENT_COMPLETE FLOAT,
	SCHEDULE_STATUS VARCHAR(16777216),
	COST_STATUS VARCHAR(11),
	CURRENT_BUDGET NUMBER(18,2),
	ACTUAL_COST_TO_DATE NUMBER(18,2),
	FORECAST_COST_AT_COMPLETION FLOAT,
	COST_VARIANCE NUMBER(19,2),
	TOTAL_RISKS NUMBER(18,0),
	HIGH_CRITICAL_RISKS NUMBER(13,0),
	TOTAL_RISK_EXPOSURE NUMBER(30,2),
	TOTAL_SCHEDULE_IMPACT_DAYS NUMBER(38,0),
	AVG_RISK_SCORE NUMBER(38,6),
	OVERALL_RISK_LEVEL VARCHAR(8),
	REFRESHED_AT TIMESTAMP_LTZ(9),
	DOMAIN VARCHAR(50) DEFAULT 'construction'
);
create or replace TABLE RISK_COMMAND_CENTER.GOLD.REPORT_REGISTRY (
	REPORT_ID VARCHAR(16777216),
	REPORT_NAME VARCHAR(16777216),
	REPORT_JSON VARIANT,
	CREATED_BY VARCHAR(16777216),
	CREATED_AT TIMESTAMP_NTZ(9)
);
create or replace TABLE RISK_COMMAND_CENTER.GOLD.SAFETY_DASHBOARD (
	PROJECT_ID VARCHAR(16777216),
	PROJECT_NAME VARCHAR(16777216),
	LOCATION VARCHAR(16777216),
	SUPERINTENDENT VARCHAR(16777216),
	TOTAL_INCIDENTS NUMBER(1,0),
	SEVERE_INCIDENTS NUMBER(1,0),
	RECORDABLE_INCIDENTS NUMBER(1,0),
	LOST_TIME_INCIDENTS NUMBER(1,0),
	LAST_INCIDENT_DATE VARCHAR(16777216),
	DAYS_SINCE_LAST_INCIDENT NUMBER(9,0),
	TOTAL_OBSERVATIONS NUMBER(1,0),
	AT_RISK_OBSERVATIONS NUMBER(1,0),
	OPEN_OBSERVATIONS NUMBER(1,0),
	SAFETY_RISK_LEVEL VARCHAR(3),
	COMPLIANCE_STATUS VARCHAR(9),
	REFRESHED_AT TIMESTAMP_LTZ(9),
	DOMAIN VARCHAR(50) DEFAULT 'construction'
);
create or replace TABLE RISK_COMMAND_CENTER.GOLD.UNIFIED_RISK_MATRIX (
	RISK_ID VARCHAR(16777216),
	PROJECT_ID VARCHAR(16777216),
	PROJECT_NAME VARCHAR(16777216),
	RISK_CATEGORY VARCHAR(16777216),
	RISK_TITLE VARCHAR(16777216),
	RISK_DESCRIPTION VARCHAR(16777216),
	SEVERITY VARCHAR(16777216),
	LIKELIHOOD VARCHAR(16777216),
	RISK_SCORE NUMBER(38,0),
	SCHEDULE_IMPACT_DAYS NUMBER(38,0),
	DIRECT_COST_EXPOSURE NUMBER(18,2),
	DOWNSTREAM_COST_EXPOSURE NUMBER(20,3),
	TOTAL_FINANCIAL_EXPOSURE NUMBER(20,3),
	RISK_DIMENSION VARCHAR(16777216),
	RISK_LEVEL VARCHAR(8),
	PROJECT_SCHEDULE_STATUS VARCHAR(16777216),
	PROJECT_COST_STATUS VARCHAR(11),
	PROJECT_PERCENT_COMPLETE FLOAT,
	REFRESHED_AT TIMESTAMP_LTZ(9),
	DOMAIN VARCHAR(50) DEFAULT 'construction'
);
create or replace TABLE RISK_COMMAND_CENTER.GOLD.VENDOR_SCORECARD (
	VENDOR_ID VARCHAR(16777216),
	VENDOR_NAME VARCHAR(16777216),
	TRADE_CATEGORY VARCHAR(16777216),
	PERFORMANCE_GRADE VARCHAR(16777216),
	PRIMARY_CONTACT VARCHAR(16777216),
	CONTACT_EMAIL VARCHAR(16777216),
	INSURANCE_EXPIRY DATE,
	INSURANCE_STATUS VARCHAR(13),
	ACTIVE_PROJECTS NUMBER(1,0),
	TOTAL_SUBCONTRACTS NUMBER(1,0),
	TOTAL_SUBCONTRACT_VALUE NUMBER(1,0),
	HIGH_RISK_CONTRACTS NUMBER(1,0),
	SAFETY_INCIDENTS NUMBER(1,0),
	TOTAL_BILLED NUMBER(1,0),
	INVOICE_COUNT NUMBER(1,0),
	COMPOSITE_SCORE NUMBER(2,0),
	REFRESHED_AT TIMESTAMP_LTZ(9),
	DOMAIN VARCHAR(50) DEFAULT 'construction'
);
create or replace TABLE RISK_COMMAND_CENTER.GOLD.VISUALIZATION_REGISTRY (
	VISUALIZATION_ID VARCHAR(16777216),
	TITLE VARCHAR(16777216),
	CHART_TYPE VARCHAR(16777216),
	SQL_QUERY VARCHAR(16777216),
	CHART_SPEC VARIANT,
	CREATED_AT TIMESTAMP_NTZ(9)
);
create or replace dynamic table RISK_COMMAND_CENTER.GOLD.VW_GRAPH_EXPLORER(
	SOURCE_NAME,
	SOURCE_TYPE,
	RELATIONSHIP_TYPE,
	TARGET_NAME,
	TARGET_TYPE,
	CONFIDENCE,
	EVIDENCE_TEXT
) target_lag = 'DOWNSTREAM' refresh_mode = AUTO initialize = ON_CREATE warehouse = RISK_WH_ADAPTIVE
 as
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
create or replace dynamic table RISK_COMMAND_CENTER.GOLD.VW_RISK_HEATMAP(
	PROJECT_NAME,
	TOTAL_RISK_EVENTS,
	TOTAL_EXPOSURE
) target_lag = '5 minutes' refresh_mode = AUTO initialize = ON_CREATE warehouse = RISK_WH_ADAPTIVE
 as
SELECT
    n.NODE_NAME AS PROJECT_NAME,
    COUNT(e.EDGE_ID) AS TOTAL_RISK_EVENTS,
    SUM(TRY_CAST(n.PROPERTIES:financial_impact::VARCHAR AS NUMBER)) AS TOTAL_EXPOSURE
FROM RISK_COMMAND_CENTER.SILVER.GRAPH_NODES n
LEFT JOIN RISK_COMMAND_CENTER.SILVER.GRAPH_EDGES e ON n.NODE_ID = e.TARGET_NODE_ID
WHERE n.NODE_TYPE = 'Project'
GROUP BY n.NODE_NAME;
create or replace schema RISK_COMMAND_CENTER.GOVERNANCE;

create or replace schema RISK_COMMAND_CENTER.KNOWLEDGE;

create or replace schema RISK_COMMAND_CENTER.OPS;

CREATE OR REPLACE PROCEDURE RISK_COMMAND_CENTER.OPS.SP_EXTRACT_GRAPH()
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
ARTIFACT_REPOSITORY = snowflake.snowpark.pypi_shared_repository
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'extract_graph'
EXECUTE AS OWNER
AS '
def extract_graph(session):
    unprocessed = session.sql("""
        SELECT DISTINCT DOCUMENT_ID FROM RISK_COMMAND_CENTER.SILVER.CHUNKS
        WHERE DOCUMENT_ID NOT IN (SELECT DISTINCT SOURCE_DOCUMENT_ID FROM RISK_COMMAND_CENTER.SILVER.GRAPH_NODES)
    """).collect()

    if not unprocessed:
        return "No new documents to process."

    session.sql("""
        CREATE OR REPLACE TABLE RISK_COMMAND_CENTER.SILVER.TMP_AI_EXTRACT AS
        SELECT
            c.CHUNK_ID,
            c.DOCUMENT_ID,
            AI_COMPLETE(''llama3.1-8b'',
                CONCAT(
                    ''Extract all entities and relationships from this construction text as JSON only. '',
                    ''For Vendor entities: extract the COMPANY NAME only, NOT the vendor ID. '',
                    ''Example: "VND-004 - VoltPath Electrical Systems" -> name should be "VoltPath Electrical Systems". '',
                    ''Example: "VND-003 - RedMesa Mechanical" -> name should be "RedMesa Mechanical". '',
                    ''For Project entities: use format "PRJ-XXX" as name if a project ID is present. '',
                    ''Keys: "entities" array (each with "type" and "name") and "relationships" array '',
                    ''(each with "source","target","type","confidence"). '',
                    ''Entity types: Project,Vendor,Risk,Contract,Person,Financial,Milestone. '',
                    ''Relationship types: MANAGES,HAS_RISK,COSTS,DELAYS,CONTRACTED_TO,IMPACTS. '',
                    ''No markdown fences. Text: '',
                    SUBSTR(c.CHUNK_TEXT, 1, 3000)
                )
            ) AS ai_response
        FROM RISK_COMMAND_CENTER.SILVER.CHUNKS c
        WHERE c.DOCUMENT_ID NOT IN (SELECT DISTINCT SOURCE_DOCUMENT_ID FROM RISK_COMMAND_CENTER.SILVER.GRAPH_NODES)
    """).collect()

    # Insert nodes — strip "VND-XXX - " prefixes from vendor names at insert time
    session.sql("""
        INSERT INTO RISK_COMMAND_CENTER.SILVER.GRAPH_NODES
            (NODE_ID, NODE_TYPE, NODE_NAME, PROPERTIES, SOURCE_DOCUMENT_ID, CREATED_AT)
        SELECT DISTINCT
            ''N-'' || UPPER(SUBSTR(MD5(t.DOCUMENT_ID || cleaned_name || e.VALUE:type::STRING), 1, 12)),
            e.VALUE:type::STRING,
            cleaned_name,
            OBJECT_CONSTRUCT(''source_chunk'', t.CHUNK_ID),
            t.DOCUMENT_ID,
            CURRENT_TIMESTAMP()
        FROM RISK_COMMAND_CENTER.SILVER.TMP_AI_EXTRACT t,
        LATERAL FLATTEN(input => TRY_PARSE_JSON(
            CASE
                WHEN t.ai_response LIKE ''%```json%''
                    THEN SPLIT_PART(SPLIT_PART(t.ai_response, ''```json'', 2), ''```'', 1)
                WHEN t.ai_response LIKE ''%```%''
                    THEN SPLIT_PART(SPLIT_PART(t.ai_response, ''```'', 2), ''```'', 1)
                ELSE t.ai_response
            END
        ):entities) e,
        LATERAL (
            SELECT
                -- Strip "VND-XXX - " or "PRJ-XXX - " prefix if present for Vendor names
                CASE
                    WHEN e.VALUE:type::STRING = ''Vendor''
                         AND CONTAINS(e.VALUE:name::STRING, '' - '')
                         AND REGEXP_LIKE(SPLIT_PART(e.VALUE:name::STRING,'' - '',1), ''^(VND|CTR|SHP)-[0-9A-Z]+.*'')
                    THEN TRIM(SPLIT_PART(e.VALUE:name::STRING, '' - '', 2))
                    ELSE TRIM(e.VALUE:name::STRING)
                END AS cleaned_name
        ) AS name_cleanup
        WHERE e.VALUE:name IS NOT NULL
          AND cleaned_name != ''''
          -- Skip bare IDs (VND-013, VND-022 etc with no real name)
          AND NOT (e.VALUE:type::STRING = ''Vendor''
                   AND cleaned_name LIKE ''VND-%'')
    """).collect()

    # Insert edges
    session.sql("""
        INSERT INTO RISK_COMMAND_CENTER.SILVER.GRAPH_EDGES
            (EDGE_ID, SOURCE_NODE_ID, TARGET_NODE_ID, RELATIONSHIP_TYPE, CONFIDENCE, EVIDENCE_CHUNK_ID, CREATED_AT)
        SELECT
            ''E-'' || UPPER(SUBSTR(MD5(t.CHUNK_ID || rel.INDEX::STRING), 1, 12)),
            src.NODE_ID,
            tgt.NODE_ID,
            rel.VALUE:type::STRING,
            COALESCE(TRY_CAST(rel.VALUE:confidence::STRING AS FLOAT), 0.8),
            t.CHUNK_ID,
            CURRENT_TIMESTAMP()
        FROM RISK_COMMAND_CENTER.SILVER.TMP_AI_EXTRACT t,
        LATERAL FLATTEN(input => TRY_PARSE_JSON(
            CASE
                WHEN t.ai_response LIKE ''%```json%''
                    THEN SPLIT_PART(SPLIT_PART(t.ai_response, ''```json'', 2), ''```'', 1)
                WHEN t.ai_response LIKE ''%```%''
                    THEN SPLIT_PART(SPLIT_PART(t.ai_response, ''```'', 2), ''```'', 1)
                ELSE t.ai_response
            END
        ):relationships) rel
        JOIN RISK_COMMAND_CENTER.SILVER.GRAPH_NODES src ON src.NODE_NAME = rel.VALUE:source::STRING
        JOIN RISK_COMMAND_CENTER.SILVER.GRAPH_NODES tgt ON tgt.NODE_NAME = rel.VALUE:target::STRING
        WHERE rel.VALUE:source IS NOT NULL AND rel.VALUE:target IS NOT NULL
    """).collect()

    # Post-insert cleanup: fix any vendor nodes that still have "VND-XXX - Name" format
    session.sql("""
        UPDATE RISK_COMMAND_CENTER.SILVER.GRAPH_NODES
        SET NODE_NAME = TRIM(SPLIT_PART(NODE_NAME, '' - '', 2))
        WHERE NODE_TYPE = ''Vendor''
          AND CONTAINS(NODE_NAME, '' - '')
          AND REGEXP_LIKE(SPLIT_PART(NODE_NAME, '' - '', 1), ''^(VND|CTR|SHP)-[0-9A-Z]+.*'')
          AND LENGTH(TRIM(SPLIT_PART(NODE_NAME, '' - '', 2))) > 2
    """).collect()

    # Remove vendor nodes that are still bare IDs after cleanup
    session.sql("""
        DELETE FROM RISK_COMMAND_CENTER.SILVER.GRAPH_NODES
        WHERE NODE_TYPE = ''Vendor''
          AND (NODE_NAME LIKE ''VND-%''
               OR NODE_NAME LIKE ''SHP-%''
               OR UPPER(TRIM(NODE_NAME)) IN (''TEAM'',''CUSTOMS'',''TRADE PARTNER'',
                                              ''COCO CONSTRUCTIONS'',''UNKNOWN''))
    """).collect()

    nodes = session.sql("SELECT COUNT(*) AS C FROM RISK_COMMAND_CENTER.SILVER.GRAPH_NODES").collect()[0][''C'']
    edges = session.sql("SELECT COUNT(*) AS C FROM RISK_COMMAND_CENTER.SILVER.GRAPH_EDGES").collect()[0][''C'']

    session.sql("DROP TABLE IF EXISTS RISK_COMMAND_CENTER.SILVER.TMP_AI_EXTRACT").collect()

    return f"Graph extraction complete: {nodes} nodes, {edges} edges."
';
CREATE OR REPLACE PROCEDURE RISK_COMMAND_CENTER.OPS.SP_EXTRACT_STRUCTURED_DATA("DOMAIN" VARCHAR DEFAULT 'construction')
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
ARTIFACT_REPOSITORY = snowflake.snowpark.pypi_shared_repository
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'extract_structured'
EXECUTE AS OWNER
AS '
def extract_structured(session, domain=''construction''):
    import re, json

    DOMAIN_HINTS = {
        ''construction'': (
            "Extract ALL risks and project data from the text. Return a JSON array of objects. "
            "Each object must have keys (null if not found): "
            "project_id, project_name, contract_value (number), "
            "percent_complete (0-100, estimate from SPI*100 if SPI given), "
            "schedule_status (On Track|At Risk|Delayed|IN_PROGRESS), "
            "vendor_name, vendor_id, "
            "risk_title (extract from Risk/Incident/Deficiency/Issue/FAIL items), "
            "risk_description, risk_category (Schedule|Budget|Safety|Vendor|Contract|Quality|Compliance|Environmental), "
            "severity (map CRITICAL->Critical HIGH->High FAIL->High MEDIUM->Medium LOW->Low), "
            "financial_exposure (number), status (OPEN). "
            "Return ONLY the JSON array, no explanation."
        ),
        ''healthcare'': (
            "Extract ALL risks and program data. Return a JSON array of objects. "
            "Keys: project_id, project_name, contract_value, percent_complete, schedule_status, "
            "vendor_name, vendor_id, risk_title, risk_description, "
            "risk_category (Patient Safety|Regulatory|Budget|Staffing|Infection Control|Quality|Compliance), "
            "severity (Critical|High|Medium|Low), financial_exposure, status (OPEN). "
            "Return ONLY the JSON array."
        ),
        ''ecommerce'': (
            "Extract ALL risks and project data. Return a JSON array with keys: "
            "project_id, project_name, contract_value, percent_complete, schedule_status, "
            "vendor_name, vendor_id, risk_title, risk_description, "
            "risk_category (Inventory|Fraud|Churn|Shipping|Returns|Compliance|Budget), "
            "severity (Critical|High|Medium|Low), financial_exposure, status (OPEN). "
            "Return ONLY the JSON array."
        ),
        ''education'': (
            "Extract ALL risks and program data. Return a JSON array with keys: "
            "project_id, project_name, contract_value, percent_complete, schedule_status, "
            "vendor_name, vendor_id, risk_title, risk_description, "
            "risk_category (Enrollment|Compliance|Budget|Safety|Accreditation|Staffing|Quality), "
            "severity (Critical|High|Medium|Low), financial_exposure, status (OPEN). "
            "Return ONLY the JSON array."
        ),
    }

    extract_prompt = DOMAIN_HINTS.get(domain, DOMAIN_HINTS[''construction''])

    # ── Pre-step 1: Clean bad project rows (id == name, null names) ───────────
    session.sql("""
        DELETE FROM RISK_COMMAND_CENTER.SILVER.PROJECTS
        WHERE PROJECT_ID = PROJECT_NAME
           OR PROJECT_NAME IS NULL
           OR TRIM(PROJECT_NAME) IN ('''',''null'',''None'')
    """).collect()

    # ── Pre-step 2: Build document → project_id context map ───────────────────
    # Scan first chunk of each document for ''Project ID: PRJ-XXX'' pattern
    doc_project_map = {}
    try:
        ctx_rows = session.sql(f"""
            SELECT c.DOCUMENT_ID,
                   REGEXP_SUBSTR(c.CHUNK_TEXT, ''PRJ-[0-9]+'', 1, 1, ''i'') AS FOUND_PID
            FROM RISK_COMMAND_CENTER.SILVER.CHUNKS c
            WHERE COALESCE(c.DOMAIN,''construction'') = ''{domain}''
              AND c.CHUNK_INDEX <= 2
              AND REGEXP_SUBSTR(c.CHUNK_TEXT, ''PRJ-[0-9]+'', 1, 1, ''i'') IS NOT NULL
        """).collect()
        for r in ctx_rows:
            if r[''DOCUMENT_ID''] and r[''FOUND_PID'']:
                doc_project_map[r[''DOCUMENT_ID'']] = r[''FOUND_PID''].upper()
    except Exception:
        pass

    # Also load project_id → project_name from Silver for fallback
    proj_id_map = {}
    try:
        for r in session.sql(f"""
            SELECT PROJECT_ID, PROJECT_NAME FROM RISK_COMMAND_CENTER.SILVER.PROJECTS
            WHERE COALESCE(DOMAIN,''construction'')=''{domain}''
              AND PROJECT_NAME IS NOT NULL
        """).collect():
            if r[''PROJECT_NAME'']:
                proj_id_map[r[''PROJECT_NAME''].lower()] = r[''PROJECT_ID'']
    except Exception:
        pass

    # ── Fetch eligible chunks ──────────────────────────────────────────────────
    chunks = session.sql(f"""
        SELECT c.CHUNK_ID, c.CHUNK_TEXT, c.DOCUMENT_ID
        FROM RISK_COMMAND_CENTER.SILVER.CHUNKS c
        WHERE COALESCE(c.DOMAIN,''construction'') = ''{domain}''
          AND NOT EXISTS (
              SELECT 1 FROM RISK_COMMAND_CENTER.SILVER.RISK_EVENTS re
              WHERE re.SOURCE_CHUNK_ID = c.CHUNK_ID
          )
          AND LENGTH(c.CHUNK_TEXT) > 100
        LIMIT 200
    """).collect()

    inserted_projects = 0
    inserted_vendors  = 0
    inserted_risks    = 0

    BAD = ('''', ''null'', ''None'', ''none'', ''NULL'')

    def sql_str(v):
        if v is None or str(v).strip() in BAD:
            return ''NULL''
        return "''" + str(v).replace("''", "''''") + "''"

    def sql_num(v):
        try:
            return str(float(v))
        except (TypeError, ValueError):
            return ''NULL''

    def decode_ai(raw):
        if raw is None:
            return ''''
        raw = str(raw).strip()
        if raw.startswith(''"'') and raw.endswith(''"''):
            try:
                return json.loads(raw)
            except Exception:
                pass
        return raw

    def parse_items(text):
        arr_m = re.search(r''\\[[\\s\\S]*\\]'', text)
        if arr_m:
            try:
                parsed = json.loads(arr_m.group(0))
                return parsed if isinstance(parsed, list) else [parsed]
            except Exception:
                pass
        obj_m = re.search(r''\\{[\\s\\S]*?\\}'', text)
        if obj_m:
            try:
                parsed = json.loads(obj_m.group(0))
                if isinstance(parsed, dict):
                    return [parsed]
            except Exception:
                pass
        return []

    for row in chunks:
        chunk_id   = row[''CHUNK_ID'']
        doc_id     = row[''DOCUMENT_ID'']
        chunk_text = row[''CHUNK_TEXT''][:3000]
        prompt_esc = (extract_prompt + "\\n\\nTEXT:\\n" + chunk_text).replace("''", "''''")

        # Document-level project_id fallback
        doc_pid = doc_project_map.get(doc_id, '''')

        try:
            res = session.sql(
                f"SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(''llama3.1-8b'', ''{prompt_esc}'') AS RESP"
            ).collect()
            if not res:
                continue
            raw   = decode_ai(res[0][''RESP''])
            items = parse_items(raw)
            if not items:
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue

                pid      = str(item.get(''project_id'') or '''').strip()
                pname    = str(item.get(''project_name'') or '''').strip()
                cv       = item.get(''contract_value'')
                pct      = item.get(''percent_complete'')
                sched_st = str(item.get(''schedule_status'') or '''').strip()
                vname    = str(item.get(''vendor_name'') or '''').strip()
                vid      = str(item.get(''vendor_id'') or '''').strip()
                rtitle   = str(item.get(''risk_title'') or '''').strip()
                rdesc    = str(item.get(''risk_description'') or '''').strip()
                rcat     = str(item.get(''risk_category'') or ''General'').strip()
                sev      = str(item.get(''severity'') or ''Medium'').strip()
                fexp     = item.get(''financial_exposure'')
                rstatus  = str(item.get(''status'') or ''OPEN'').strip().upper()

                # Guard: reject rows where AI returned id == name (hallucination)
                if pid and pid == pname:
                    pid = doc_pid
                if pid in BAD:
                    pid = doc_pid
                # Name-to-id lookup fallback
                if pid in BAD and pname not in BAD:
                    pid = proj_id_map.get(pname.lower(), doc_pid)

                # Merge project (only if meaningful name and name != id)
                if pid not in BAD and pname not in BAD and pid != pname:
                    session.sql(f"""
                        MERGE INTO RISK_COMMAND_CENTER.SILVER.PROJECTS tgt
                        USING (SELECT {sql_str(pid)} AS PID, {sql_str(pname)} AS PNAME,
                                      {sql_num(cv)} AS CV, {sql_num(pct)} AS PCT,
                                      {sql_str(sched_st)} AS SS, ''{domain}'' AS DOM
                        ) src ON tgt.PROJECT_ID = src.PID AND tgt.DOMAIN = src.DOM
                        WHEN NOT MATCHED THEN
                            INSERT (PROJECT_ID,PROJECT_NAME,CURRENT_CONTRACT_VALUE,PERCENT_COMPLETE,SCHEDULE_STATUS,DOMAIN)
                            VALUES (src.PID,src.PNAME,src.CV,src.PCT,src.SS,src.DOM)
                        WHEN MATCHED THEN
                            UPDATE SET
                                PROJECT_NAME           = COALESCE(src.PNAME, tgt.PROJECT_NAME),
                                CURRENT_CONTRACT_VALUE = COALESCE(src.CV, tgt.CURRENT_CONTRACT_VALUE),
                                PERCENT_COMPLETE       = COALESCE(src.PCT, tgt.PERCENT_COMPLETE),
                                SCHEDULE_STATUS        = COALESCE(src.SS, tgt.SCHEDULE_STATUS)
                    """).collect()
                    inserted_projects += 1

                # Merge vendor
                if vname not in BAD:
                    vid_sql = sql_str(vid) if vid not in BAD else ''NULL''
                    session.sql(f"""
                        MERGE INTO RISK_COMMAND_CENTER.SILVER.VENDORS tgt
                        USING (SELECT {sql_str(vname)} AS VNAME, {vid_sql} AS VID, ''{domain}'' AS DOM
                        ) src ON tgt.VENDOR_NAME = src.VNAME AND tgt.DOMAIN = src.DOM
                        WHEN NOT MATCHED THEN
                            INSERT (VENDOR_ID,VENDOR_NAME,TRADE_CATEGORY,PERFORMANCE_GRADE,DOMAIN)
                            VALUES (COALESCE(src.VID,''VND-''||UPPER(SUBSTR(MD5(src.VNAME),1,6))),
                                    src.VNAME,''General'',''B'',src.DOM)
                    """).collect()
                    inserted_vendors += 1

                # Insert risk event
                if rtitle not in BAD:
                    # Final project_id assignment priority: AI → doc context → biggest project
                    if pid in BAD:
                        pid = doc_pid
                    session.sql(f"""
                        MERGE INTO RISK_COMMAND_CENTER.SILVER.RISK_EVENTS tgt
                        USING (SELECT ''RSK-''||UPPER(SUBSTR(MD5({sql_str(rtitle)}||''{chunk_id}''),1,8)) AS RID,
                                      {sql_str(pid)} AS PID, {sql_str(rtitle)} AS RTITLE,
                                      {sql_str(rdesc)} AS RDESC, {sql_str(rcat)} AS RCAT,
                                      {sql_str(sev)} AS SEV, {sql_num(fexp)} AS FEXP,
                                      {sql_str(rstatus)} AS RSTATUS,
                                      ''{chunk_id}'' AS SCHUNK, ''{domain}'' AS DOM
                        ) src ON tgt.RISK_ID = src.RID
                        WHEN NOT MATCHED THEN
                            INSERT (RISK_ID,PROJECT_ID,RISK_TITLE,RISK_DESCRIPTION,RISK_CATEGORY,
                                    SEVERITY,FINANCIAL_EXPOSURE,STATUS,SOURCE_CHUNK_ID,DOMAIN)
                            VALUES (src.RID,src.PID,src.RTITLE,src.RDESC,src.RCAT,
                                    src.SEV,src.FEXP,src.RSTATUS,src.SCHUNK,src.DOM)
                    """).collect()
                    inserted_risks += 1

        except Exception:
            continue

    # ── Post-step: assign any remaining NULL project_ids using keyword matching ─
    try:
        session.sql(f"""
            UPDATE RISK_COMMAND_CENTER.SILVER.RISK_EVENTS
            SET PROJECT_ID = (
                SELECT PROJECT_ID FROM RISK_COMMAND_CENTER.SILVER.PROJECTS
                WHERE COALESCE(DOMAIN,''construction'')=''{domain}''
                  AND PROJECT_NAME IS NOT NULL
                ORDER BY COALESCE(CURRENT_CONTRACT_VALUE,0) DESC LIMIT 1
            )
            WHERE (PROJECT_ID IS NULL OR TRIM(PROJECT_ID) IN ('''',''None'',''null''))
              AND COALESCE(DOMAIN,''construction'')=''{domain}''
        """).collect()
    except Exception:
        pass

    return (f"Extraction ({domain}): {inserted_projects} project updates, "
            f"{inserted_vendors} vendor merges, {inserted_risks} risk events")
';
CREATE OR REPLACE PROCEDURE RISK_COMMAND_CENTER.OPS.SP_GENERATE_VECTORS()
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
ARTIFACT_REPOSITORY = snowflake.snowpark.pypi_shared_repository
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'generate_vectors'
EXECUTE AS OWNER
AS '
def generate_vectors(session):
    # Single set-based INSERT - no Python loop
    result = session.sql("""
        INSERT INTO RISK_COMMAND_CENTER.SILVER.VECTORS (VECTOR_ID, CHUNK_ID, EMBEDDING_VECTOR)
        SELECT 
            ''VEC-'' || UPPER(SUBSTR(MD5(c.CHUNK_ID), 1, 12)),
            c.CHUNK_ID,
            SNOWFLAKE.CORTEX.EMBED_TEXT_1024(''snowflake-arctic-embed-l-v2.0'', SUBSTR(c.CHUNK_TEXT, 1, 8000))
        FROM RISK_COMMAND_CENTER.SILVER.CHUNKS c
        WHERE c.CHUNK_ID NOT IN (SELECT CHUNK_ID FROM RISK_COMMAND_CENTER.SILVER.VECTORS)
    """).collect()

    count = session.sql("SELECT COUNT(*) AS C FROM RISK_COMMAND_CENTER.SILVER.VECTORS").collect()[0][''C'']
    new_count = session.sql("""
        SELECT COUNT(*) AS C FROM RISK_COMMAND_CENTER.SILVER.CHUNKS 
        WHERE CHUNK_ID NOT IN (SELECT CHUNK_ID FROM RISK_COMMAND_CENTER.SILVER.VECTORS)
    """).collect()[0][''C'']
    
    if new_count == 0:
        return f"Vector generation complete: {count}/{count} chunks embedded."
    else:
        return f"All chunks already have vectors."
';
CREATE OR REPLACE PROCEDURE RISK_COMMAND_CENTER.OPS.SP_POPULATE_SILVER_FROM_GRAPH()
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
ARTIFACT_REPOSITORY = snowflake.snowpark.pypi_shared_repository
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'populate_silver'
EXECUTE AS OWNER
AS '
def populate_silver(session):
    import re
    results = []

    # ── 1. Projects from GRAPH_NODES ──────────────────────────────────────────
    session.sql("""
        MERGE INTO RISK_COMMAND_CENTER.SILVER.PROJECTS tgt
        USING (
            SELECT DISTINCT
                SPLIT_PART(NODE_NAME, '' - '', 1) AS PROJECT_ID,
                CASE WHEN CONTAINS(NODE_NAME, '' - '') THEN SPLIT_PART(NODE_NAME, '' - '', 2)
                     ELSE NODE_NAME END AS PROJECT_NAME
            FROM RISK_COMMAND_CENTER.SILVER.GRAPH_NODES
            WHERE NODE_TYPE = ''Project''
              AND REGEXP_LIKE(NODE_NAME, ''^PRJ-[0-9].*'')
              AND NODE_NAME != ''Unknown''
        ) src ON tgt.PROJECT_ID = src.PROJECT_ID
        WHEN MATCHED AND (tgt.PROJECT_NAME IS NULL OR tgt.PROJECT_NAME = tgt.PROJECT_ID) THEN
            UPDATE SET PROJECT_NAME = src.PROJECT_NAME
        WHEN NOT MATCHED THEN
            INSERT (PROJECT_ID, PROJECT_NAME, PERCENT_COMPLETE, SCHEDULE_STATUS, COST_STATUS, LOADED_AT)
            VALUES (src.PROJECT_ID, src.PROJECT_NAME, NULL, NULL, NULL, CURRENT_TIMESTAMP())
    """).collect()

    # ── 2. Vendors from GRAPH_NODES ────────────────────────────────────────────
    session.sql("""
        MERGE INTO RISK_COMMAND_CENTER.SILVER.VENDORS tgt
        USING (
            SELECT DISTINCT
                SPLIT_PART(NODE_NAME, '' - '', 1) AS VENDOR_ID,
                SPLIT_PART(NODE_NAME, '' - '', 2) AS VENDOR_NAME
            FROM RISK_COMMAND_CENTER.SILVER.GRAPH_NODES
            WHERE NODE_TYPE = ''Vendor''
              AND CONTAINS(NODE_NAME, '' - '')
              AND REGEXP_LIKE(SPLIT_PART(NODE_NAME, '' - '', 1), ''^VND-[0-9].*'')
              AND LENGTH(TRIM(SPLIT_PART(NODE_NAME, '' - '', 2))) > 2
              AND UPPER(TRIM(SPLIT_PART(NODE_NAME, '' - '', 2)))
                  NOT IN (''NULL'',''NONE'',''UNKNOWN'',''TEAM'',''CUSTOMS'',''TRADE PARTNER'')
        ) src ON tgt.VENDOR_ID = src.VENDOR_ID
        WHEN MATCHED AND (tgt.VENDOR_NAME IS NULL OR tgt.VENDOR_NAME = tgt.VENDOR_ID
                          OR tgt.VENDOR_NAME LIKE ''VND-%'') THEN
            UPDATE SET VENDOR_NAME = src.VENDOR_NAME
        WHEN NOT MATCHED THEN
            INSERT (VENDOR_ID, VENDOR_NAME, TRADE_CATEGORY, PERFORMANCE_GRADE, LOADED_AT)
            VALUES (src.VENDOR_ID, src.VENDOR_NAME, ''General'', ''B'', CURRENT_TIMESTAMP())
    """).collect()

    # ── 3. CSV vendor import from SILVER.CHUNKS ────────────────────────────────
    csv_chunks = session.sql("""
        SELECT c.CHUNK_ID, c.CHUNK_TEXT, c.DOMAIN
        FROM RISK_COMMAND_CENTER.SILVER.CHUNKS c
        JOIN RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY r ON c.DOCUMENT_ID = r.DOCUMENT_ID
        WHERE LOWER(r.FILE_TYPE) = ''csv''
    """).collect()

    csv_imported = 0
    NOISE = {''null'',''none'',''unknown'',''team'',''customs'',''trade partner'',''n/a'',''na'',''tbd'',
             ''vendor'',''vendor_name'',''name'',''company'',''supplier''}

    for chunk in csv_chunks:
        text   = chunk[''CHUNK_TEXT''] or ''''
        domain = chunk[''DOMAIN''] or ''construction''
        for line in text.splitlines():
            line  = line.strip()
            if not line:
                continue
            parts = re.split(r''[,|]'', line)
            parts = [p.strip().strip(''"'') for p in parts]
            if len(parts) < 2:
                continue
            vid = parts[0].strip()
            if not re.match(r''^VND-[0-9A-Z]+$'', vid, re.IGNORECASE):
                continue
            vname = parts[1].strip()
            if not vname or vname.lower() in NOISE or len(vname) <= 2:
                continue
            if re.match(r''^VND-[0-9A-Z]+$'', vname, re.IGNORECASE):
                continue
            grade    = parts[3].strip() if len(parts) > 3 else ''B''
            category = parts[2].strip() if len(parts) > 2 else ''General''
            if grade not in (''A'',''B'',''C'',''D''):
                grade = ''B''
            vid_esc   = vid.replace("''","''''")
            vname_esc = vname.replace("''","''''")
            cat_esc   = category.replace("''","''''")
            session.sql(f"""
                MERGE INTO RISK_COMMAND_CENTER.SILVER.VENDORS tgt
                USING (SELECT ''{vid_esc}'' AS VID, ''{vname_esc}'' AS VNAME,
                              ''{cat_esc}'' AS CAT, ''{grade}'' AS GRD,
                              ''{domain}'' AS DOM) src
                ON tgt.VENDOR_ID = src.VID
                WHEN MATCHED AND (tgt.VENDOR_NAME IS NULL
                                  OR tgt.VENDOR_NAME = tgt.VENDOR_ID
                                  OR tgt.VENDOR_NAME LIKE ''VND-%'') THEN
                    UPDATE SET VENDOR_NAME=src.VNAME, TRADE_CATEGORY=src.CAT,
                               PERFORMANCE_GRADE=src.GRD, DOMAIN=src.DOM
                WHEN NOT MATCHED THEN
                    INSERT (VENDOR_ID,VENDOR_NAME,TRADE_CATEGORY,PERFORMANCE_GRADE,DOMAIN,LOADED_AT)
                    VALUES (src.VID,src.VNAME,src.CAT,src.GRD,src.DOM,CURRENT_TIMESTAMP())
            """).collect()
            csv_imported += 1

    # ── 4. Auto-backfill PERCENT_COMPLETE from chunk content ───────────────────
    # Look for SPI values and estimate percent_complete; also extract schedule_status
    pct_chunks = session.sql("""
        SELECT c.DOCUMENT_ID,
               REGEXP_SUBSTR(c.CHUNK_TEXT, ''PRJ-[0-9]+'', 1, 1, ''i'') AS PID,
               REGEXP_SUBSTR(c.CHUNK_TEXT, ''SPI[\\\\s:]+([0-9]+\\\\.?[0-9]*)'', 1, 1, ''ie'', 1) AS SPI_VAL,
               REGEXP_SUBSTR(c.CHUNK_TEXT, ''percent[\\\\s_]?complete[^0-9]*([0-9]+)'', 1, 1, ''ie'', 1) AS PCT_DIRECT,
               CASE
                   WHEN UPPER(c.CHUNK_TEXT) LIKE ''%IN_PROGRESS%'' THEN ''In Progress''
                   WHEN UPPER(c.CHUNK_TEXT) LIKE ''%AT RISK%'' OR UPPER(c.CHUNK_TEXT) LIKE ''%AT_RISK%'' THEN ''At Risk''
                   WHEN UPPER(c.CHUNK_TEXT) LIKE ''%DELAYED%'' THEN ''Delayed''
                   WHEN UPPER(c.CHUNK_TEXT) LIKE ''%ON TRACK%'' THEN ''On Track''
                   ELSE NULL
               END AS SCHED_STATUS
        FROM RISK_COMMAND_CENTER.SILVER.CHUNKS c
        WHERE (CHUNK_TEXT ILIKE ''%SPI%'' OR CHUNK_TEXT ILIKE ''%percent complete%''
               OR CHUNK_TEXT ILIKE ''%IN_PROGRESS%'' OR CHUNK_TEXT ILIKE ''%AT RISK%'')
          AND REGEXP_SUBSTR(c.CHUNK_TEXT, ''PRJ-[0-9]+'', 1, 1, ''i'') IS NOT NULL
    """).collect()

    for r in pct_chunks:
        pid   = (r[''PID''] or '''').upper()
        spi   = r[''SPI_VAL'']
        pct_d = r[''PCT_DIRECT'']
        sched = r[''SCHED_STATUS'']
        if not pid:
            continue
        pct_val = None
        if pct_d:
            try:
                pct_val = min(100, max(0, float(pct_d)))
            except Exception:
                pass
        if pct_val is None and spi:
            try:
                pct_val = round(min(100, max(0, float(spi) * 100)), 1)
            except Exception:
                pass
        if pct_val is not None or sched:
            pid_esc = pid.replace("''","''''")
            pct_sql = str(pct_val) if pct_val is not None else ''NULL''
            sched_sql = f"''{sched}''" if sched else ''NULL''
            session.sql(f"""
                UPDATE RISK_COMMAND_CENTER.SILVER.PROJECTS
                SET PERCENT_COMPLETE = COALESCE(PERCENT_COMPLETE, {pct_sql}),
                    SCHEDULE_STATUS  = COALESCE(SCHEDULE_STATUS, {sched_sql})
                WHERE PROJECT_ID = ''{pid_esc}''
                  AND (PERCENT_COMPLETE IS NULL OR SCHEDULE_STATUS IS NULL)
            """).collect()

    # ── 5. Clean noise vendors ─────────────────────────────────────────────────
    session.sql("""
        DELETE FROM RISK_COMMAND_CENTER.SILVER.VENDORS
        WHERE VENDOR_NAME LIKE ''VND-%''
           OR VENDOR_NAME LIKE ''SHP-%''
           OR VENDOR_NAME LIKE ''INV-%''
           OR UPPER(TRIM(VENDOR_NAME)) IN (''TEAM'',''CUSTOMS'',''TRADE PARTNER'',
                                            ''COCO CONSTRUCTIONS'',''UNKNOWN'',''NULL'',''NONE'')
           OR LENGTH(TRIM(VENDOR_NAME)) <= 2
    """).collect()

    p_count = session.sql("SELECT COUNT(*) AS C FROM RISK_COMMAND_CENTER.SILVER.PROJECTS").collect()[0][''C'']
    v_count = session.sql("SELECT COUNT(*) AS C FROM RISK_COMMAND_CENTER.SILVER.VENDORS").collect()[0][''C'']
    results.append(f"PROJECTS: {p_count}")
    results.append(f"VENDORS: {v_count} ({csv_imported} from CSV)")
    return "Silver population complete: " + " | ".join(results)
';
CREATE OR REPLACE PROCEDURE RISK_COMMAND_CENTER.OPS.SP_PROCESS_BRONZE_TO_SILVER()
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
ARTIFACT_REPOSITORY = snowflake.snowpark.pypi_shared_repository
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'process_docs'
EXECUTE AS OWNER
AS '
def process_docs(session):
    PARSE_DOCUMENT_TYPES = (''pdf'',''docx'',''pptx'',''txt'',''html'',''png'',''jpg'',''jpeg'',''tiff'',''tif'')

    # ── Step 0: Self-heal — fix STATUS for docs already parsed but wrongly flagged ─
    session.sql("""
        UPDATE RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY r
        SET STATUS = ''PARSED''
        WHERE r.STATUS IN (''UPLOADED'',''FAILED'')
          AND r.DOCUMENT_ID IN (
              SELECT DOCUMENT_ID FROM RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS
              WHERE STATUS = ''SUCCESS''
          )
          AND r.DOCUMENT_ID IN (
              SELECT DOCUMENT_ID FROM RISK_COMMAND_CENTER.SILVER.CHUNKS
          )
    """).collect()

    # ── Step 1: Process truly new / unprocessed docs ───────────────────────────
    unparsed = session.sql("""
        SELECT r.DOCUMENT_ID, r.FILE_PATH, r.FILE_NAME,
               LOWER(r.FILE_TYPE) AS FILE_TYPE,
               COALESCE(r.DOMAIN, ''construction'') AS DOMAIN
        FROM RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY r
        WHERE r.STATUS IN (''UPLOADED'', ''FAILED'')
          AND r.DOCUMENT_ID NOT IN (SELECT DOCUMENT_ID FROM RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS)
    """).collect()

    parsed_count = 0
    skipped      = 0

    for row in unparsed:
        doc_id    = row[''DOCUMENT_ID'']
        file_path = row[''FILE_PATH'']
        file_type = (row[''FILE_TYPE''] or '''').strip().lower()
        domain    = row[''DOMAIN''] or ''construction''

        try:
            if file_type in PARSE_DOCUMENT_TYPES:
                session.sql(f"""
                    INSERT INTO RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS
                        (DOCUMENT_ID, RAW_TEXT, PARSED_JSON, STATUS)
                    SELECT ''{doc_id}'',
                           SUBSTR(SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
                               ''@RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE'', ''{file_path}'',
                               {{''mode'':''LAYOUT''}}
                           )::STRING, 1, 50000),
                           TRY_PARSE_JSON(SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
                               ''@RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE'', ''{file_path}'',
                               {{''mode'':''LAYOUT''}}
                           )::STRING),
                           ''SUCCESS''
                """).collect()

            elif file_type in (''eml'', ''msg''):
                import email
                file_bytes = session.file.get_stream(
                    f"@RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE/{file_path}"
                ).read()
                msg    = email.message_from_bytes(file_bytes)
                parts  = []
                for part in msg.walk():
                    if part.get_content_type() in (''text/plain'',''text/html'') and not part.get(''Content-Disposition''):
                        try:
                            parts.append(part.get_payload(decode=True).decode(''utf-8'', errors=''replace''))
                        except Exception:
                            pass
                content = (f"From: {msg.get(''From'','''')}\\nDate: {msg.get(''Date'','''')}\\n"
                           f"Subject: {msg.get(''Subject'','''')}\\n\\n") + ''\\n''.join(parts)[:40000]
                content_esc = content.replace("''", "''''")
                session.sql(f"""
                    INSERT INTO RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS
                        (DOCUMENT_ID, RAW_TEXT, PARSED_JSON, STATUS)
                    VALUES (''{doc_id}'', ''{content_esc}'', NULL, ''SUCCESS'')
                """).collect()

            elif file_type == ''csv'':
                file_bytes = session.file.get_stream(
                    f"@RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE/{file_path}"
                ).read()
                content  = file_bytes.decode(''utf-8'', errors=''replace'')
                full_esc = content[:40000].replace("''", "''''")
                session.sql(f"""
                    INSERT INTO RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS
                        (DOCUMENT_ID, RAW_TEXT, PARSED_JSON, STATUS)
                    VALUES (''{doc_id}'', ''{full_esc}'', NULL, ''SUCCESS'')
                """).collect()

            elif file_type in (''json'', ''xml'', ''log''):
                file_bytes  = session.file.get_stream(
                    f"@RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE/{file_path}"
                ).read()
                content     = file_bytes.decode(''utf-8'', errors=''replace'')[:40000]
                content_esc = content.replace("''", "''''")
                session.sql(f"""
                    INSERT INTO RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS
                        (DOCUMENT_ID, RAW_TEXT, PARSED_JSON, STATUS)
                    VALUES (''{doc_id}'', ''{content_esc}'', NULL, ''SUCCESS'')
                """).collect()

            else:
                skipped += 1
                session.sql(f"UPDATE RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY SET STATUS=''UNSUPPORTED'' WHERE DOCUMENT_ID=''{doc_id}''").collect()
                continue

            parsed_count += 1
            session.sql(f"UPDATE RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY SET STATUS=''PARSED'' WHERE DOCUMENT_ID=''{doc_id}''").collect()

        except Exception:
            session.sql(f"UPDATE RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY SET STATUS=''FAILED'' WHERE DOCUMENT_ID=''{doc_id}''").collect()

    # ── Step 2: Self-heal — create missing chunks for docs in DOC_PARSE_RESULTS ─
    # Covers: CSV files where chunk-insert failed, or any doc re-uploaded
    missing_chunks = session.sql("""
        SELECT p.DOCUMENT_ID, p.RAW_TEXT, LOWER(r.FILE_TYPE) AS FILE_TYPE,
               COALESCE(r.DOMAIN,''construction'') AS DOMAIN
        FROM RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS p
        JOIN RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY r ON p.DOCUMENT_ID = r.DOCUMENT_ID
        WHERE p.STATUS = ''SUCCESS''
          AND p.DOCUMENT_ID NOT IN (
              SELECT DISTINCT DOCUMENT_ID FROM RISK_COMMAND_CENTER.SILVER.CHUNKS
          )
          AND LENGTH(COALESCE(p.RAW_TEXT,'''')) > 10
    """).collect()

    healed = 0
    for row in missing_chunks:
        doc_id    = row[''DOCUMENT_ID'']
        raw_text  = row[''RAW_TEXT''] or ''''
        file_type = row[''FILE_TYPE'']
        domain    = row[''DOMAIN'']

        try:
            if file_type == ''csv'':
                # Chunk by 20-row batches
                lines      = [l for l in raw_text.splitlines() if l.strip()]
                header     = lines[0] if lines else ''''
                data_rows  = lines[1:] if len(lines) > 1 else lines
                BATCH      = 20
                for idx in range(0, max(1, len(data_rows)), BATCH):
                    batch     = data_rows[idx:idx + BATCH]
                    chunk_txt = header + ''\\n'' + ''\\n''.join(batch)
                    if len(chunk_txt.strip()) < 10:
                        continue
                    chunk_esc = chunk_txt.replace("''", "''''")
                    chunk_num = idx // BATCH
                    session.sql(f"""
                        INSERT INTO RISK_COMMAND_CENTER.SILVER.CHUNKS
                            (CHUNK_ID,DOCUMENT_ID,CHUNK_INDEX,CHUNK_TEXT,PAGE_NUMBER,DOMAIN)
                        VALUES (''CHK-''||UPPER(SUBSTR(MD5(''{doc_id}-csv-{chunk_num}''),1,12)),
                                ''{doc_id}'',{chunk_num},''{chunk_esc}'',1,''{domain}'')
                    """).collect()
                    healed += 1
            else:
                # Generic: split by section markers
                session.sql(f"""
                    INSERT INTO RISK_COMMAND_CENTER.SILVER.CHUNKS
                        (CHUNK_ID,DOCUMENT_ID,CHUNK_INDEX,CHUNK_TEXT,PAGE_NUMBER,DOMAIN)
                    SELECT ''CHK-''||UPPER(SUBSTR(MD5(''{doc_id}''||''-''||f.INDEX::STRING),1,12)),
                           ''{doc_id}'', f.INDEX, TRIM(f.VALUE::STRING),
                           GREATEST(1, CEIL(f.INDEX/3.0)), ''{domain}''
                    FROM RISK_COMMAND_CENTER.BRONZE.DOC_PARSE_RESULTS d,
                    LATERAL FLATTEN(input => SPLIT(
                        COALESCE(d.PARSED_JSON:content::STRING, d.RAW_TEXT), chr(10)||''# ''
                    )) f
                    WHERE d.DOCUMENT_ID = ''{doc_id}''
                      AND LENGTH(TRIM(f.VALUE::STRING)) > 50
                """).collect()
                healed += 1

            session.sql(f"UPDATE RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY SET STATUS=''PARSED'' WHERE DOCUMENT_ID=''{doc_id}''").collect()

        except Exception:
            pass

    total_chunks = session.sql("SELECT COUNT(*) AS C FROM RISK_COMMAND_CENTER.SILVER.CHUNKS").collect()[0][''C'']
    return (f"Parse complete: {parsed_count} new docs, {healed} self-healed, "
            f"{total_chunks} total chunks. Skipped: {skipped} unsupported.")
';
CREATE OR REPLACE PROCEDURE RISK_COMMAND_CENTER.OPS.SP_REFRESH_GOLD("DOMAIN" VARCHAR DEFAULT 'construction')
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
ARTIFACT_REPOSITORY = snowflake.snowpark.pypi_shared_repository
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'refresh_gold'
EXECUTE AS OWNER
AS '
def refresh_gold(session, domain=''construction''):
    results = []

    # ── Pre-cleanup ────────────────────────────────────────────────────────
    # Remove bad project rows (ai hallucinated id=name)
    session.sql("""
        DELETE FROM RISK_COMMAND_CENTER.SILVER.PROJECTS
        WHERE PROJECT_ID = PROJECT_NAME
           OR PROJECT_NAME IS NULL
           OR TRIM(PROJECT_NAME) IN ('''',''null'',''None'')
    """).collect()

    # Fix RISK_EVENTS with NULL project_id using keyword matching
    session.sql(f"""
        UPDATE RISK_COMMAND_CENTER.SILVER.RISK_EVENTS
        SET PROJECT_ID = ''PRJ-003''
        WHERE COALESCE(DOMAIN,''construction'') = ''{domain}''
          AND (PROJECT_ID IS NULL OR TRIM(PROJECT_ID) IN ('''',''None'',''null''))
          AND (UPPER(RISK_TITLE) LIKE ''%ATLAS%'' OR UPPER(RISK_TITLE) LIKE ''%CUSTOMS%''
            OR UPPER(RISK_TITLE) LIKE ''%CABLE%'' OR UPPER(RISK_TITLE) LIKE ''%LIQUIDATED%''
            OR UPPER(RISK_TITLE) LIKE ''%SOIL%'' OR UPPER(RISK_TITLE) LIKE ''%FLATNESS%''
            OR UPPER(RISK_TITLE) LIKE ''%COST OVERRUN%'')
    """).collect()

    session.sql(f"""
        UPDATE RISK_COMMAND_CENTER.SILVER.RISK_EVENTS
        SET PROJECT_ID = ''PRJ-001''
        WHERE COALESCE(DOMAIN,''construction'') = ''{domain}''
          AND (PROJECT_ID IS NULL OR TRIM(PROJECT_ID) IN ('''',''None'',''null''))
          AND (UPPER(RISK_TITLE) LIKE ''%MEP%'' OR UPPER(RISK_TITLE) LIKE ''%HVAC%''
            OR UPPER(RISK_TITLE) LIKE ''%ROUTING%'' OR UPPER(RISK_TITLE) LIKE ''%CEILING%'')
    """).collect()

    # Any remaining NULL project_ids → default to most contract-value project
    session.sql(f"""
        UPDATE RISK_COMMAND_CENTER.SILVER.RISK_EVENTS
        SET PROJECT_ID = (
            SELECT PROJECT_ID FROM RISK_COMMAND_CENTER.SILVER.PROJECTS
            WHERE COALESCE(DOMAIN,''construction'') = ''{domain}''
              AND PROJECT_NAME IS NOT NULL
              AND TRIM(PROJECT_NAME) NOT IN ('''',''null'',''None'')
            ORDER BY COALESCE(CURRENT_CONTRACT_VALUE,0) DESC LIMIT 1
        )
        WHERE COALESCE(DOMAIN,''construction'') = ''{domain}''
          AND (PROJECT_ID IS NULL OR TRIM(PROJECT_ID) IN ('''',''None'',''null''))
    """).collect()
    # ── End pre-cleanup ────────────────────────────────────────────────────

    session.sql(f"DELETE FROM RISK_COMMAND_CENTER.GOLD.PROJECT_RISK_SUMMARY WHERE DOMAIN = ''{domain}''").collect()
    session.sql(f"""
        INSERT INTO RISK_COMMAND_CENTER.GOLD.PROJECT_RISK_SUMMARY
        SELECT p.PROJECT_ID, p.PROJECT_NAME, p.PROJECT_TYPE, p.LOCATION, p.CLIENT,
            p.PROJECT_MANAGER, p.START_DATE, p.PLANNED_COMPLETION, p.FORECAST_COMPLETION,
            DATEDIFF(''day'', p.PLANNED_COMPLETION, COALESCE(p.FORECAST_COMPLETION, p.PLANNED_COMPLETION)) AS SCHEDULE_VARIANCE_DAYS,
            p.PERCENT_COMPLETE, p.SCHEDULE_STATUS,
            CASE WHEN COALESCE(p.ACTUAL_COST,0) > COALESCE(p.CURRENT_CONTRACT_VALUE,1)*1.1 THEN ''Over Budget''
                 WHEN COALESCE(p.ACTUAL_COST,0) > COALESCE(p.CURRENT_CONTRACT_VALUE,1)*0.95 THEN ''At Risk''
                 ELSE ''On Budget'' END AS COST_STATUS,
            COALESCE(p.CURRENT_CONTRACT_VALUE,0) AS CURRENT_BUDGET,
            COALESCE(p.ACTUAL_COST,0) AS ACTUAL_COST_TO_DATE,
            CASE WHEN COALESCE(p.PERCENT_COMPLETE,0) > 0 THEN COALESCE(p.ACTUAL_COST,0)*(100.0/p.PERCENT_COMPLETE)
                 ELSE COALESCE(p.CURRENT_CONTRACT_VALUE,0) END AS FORECAST_COST_AT_COMPLETION,
            COALESCE(p.ACTUAL_COST,0)-COALESCE(p.CURRENT_CONTRACT_VALUE,0) AS COST_VARIANCE,
            COUNT(r.RISK_ID) AS TOTAL_RISKS,
            COUNT_IF(UPPER(r.SEVERITY) IN (''HIGH'',''CRITICAL'')) AS HIGH_CRITICAL_RISKS,
            SUM(COALESCE(r.FINANCIAL_EXPOSURE,0)) AS TOTAL_RISK_EXPOSURE,
            SUM(COALESCE(r.SCHEDULE_IMPACT_DAYS,0)) AS TOTAL_SCHEDULE_IMPACT_DAYS,
            COALESCE(AVG(r.RISK_SCORE),0) AS AVG_RISK_SCORE,
            CASE WHEN COUNT_IF(UPPER(r.SEVERITY)=''CRITICAL'')>0 THEN ''Critical''
                 WHEN COUNT_IF(UPPER(r.SEVERITY)=''HIGH'')>0 THEN ''High''
                 WHEN COUNT(r.RISK_ID)>3 THEN ''Medium'' ELSE ''Low'' END AS OVERALL_RISK_LEVEL,
            CURRENT_TIMESTAMP() AS REFRESHED_AT, ''{domain}'' AS DOMAIN
        FROM RISK_COMMAND_CENTER.SILVER.PROJECTS_CLEAN p
        LEFT JOIN RISK_COMMAND_CENTER.SILVER.RISK_EVENTS r
            ON p.PROJECT_ID=r.PROJECT_ID AND UPPER(r.STATUS)=''OPEN''
            AND COALESCE(r.DOMAIN,''construction'')=''{domain}''
        WHERE COALESCE(p.DOMAIN,''construction'')=''{domain}''
          AND p.PROJECT_NAME IS NOT NULL
          AND TRIM(p.PROJECT_NAME) NOT IN ('''',''null'',''None'')
          AND p.PROJECT_ID != p.PROJECT_NAME
        GROUP BY p.PROJECT_ID,p.PROJECT_NAME,p.PROJECT_TYPE,p.LOCATION,p.CLIENT,
            p.PROJECT_MANAGER,p.START_DATE,p.PLANNED_COMPLETION,p.FORECAST_COMPLETION,
            p.PERCENT_COMPLETE,p.SCHEDULE_STATUS,p.CURRENT_CONTRACT_VALUE,p.ACTUAL_COST
    """).collect()
    count = session.sql(f"SELECT COUNT(*) AS N FROM RISK_COMMAND_CENTER.GOLD.PROJECT_RISK_SUMMARY WHERE DOMAIN=''{domain}''").collect()[0][''N'']
    results.append(f"PROJECT_RISK_SUMMARY: {count}")

    session.sql(f"DELETE FROM RISK_COMMAND_CENTER.GOLD.UNIFIED_RISK_MATRIX WHERE DOMAIN=''{domain}''").collect()
    session.sql(f"""
        INSERT INTO RISK_COMMAND_CENTER.GOLD.UNIFIED_RISK_MATRIX
        SELECT r.RISK_ID, r.PROJECT_ID, p.PROJECT_NAME, r.RISK_CATEGORY, r.RISK_TITLE, r.RISK_DESCRIPTION,
            r.SEVERITY, r.LIKELIHOOD, COALESCE(r.RISK_SCORE,40) AS RISK_SCORE,
            COALESCE(r.SCHEDULE_IMPACT_DAYS,0) AS SCHEDULE_IMPACT_DAYS,
            COALESCE(r.FINANCIAL_EXPOSURE,0) AS DIRECT_COST_EXPOSURE,
            COALESCE(r.FINANCIAL_EXPOSURE,0)*0.3 AS DOWNSTREAM_COST_EXPOSURE,
            COALESCE(r.FINANCIAL_EXPOSURE,0)*1.3 AS TOTAL_FINANCIAL_EXPOSURE,
            r.RISK_CATEGORY AS RISK_DIMENSION,
            CASE WHEN COALESCE(r.RISK_SCORE,40)>=80 THEN ''Critical'' WHEN COALESCE(r.RISK_SCORE,40)>=60 THEN ''High''
                 WHEN COALESCE(r.RISK_SCORE,40)>=40 THEN ''Medium'' ELSE ''Low'' END AS RISK_LEVEL,
            p.SCHEDULE_STATUS AS PROJECT_SCHEDULE_STATUS,
            CASE WHEN COALESCE(p.ACTUAL_COST,0)>COALESCE(p.CURRENT_CONTRACT_VALUE,1)*1.1 THEN ''Over Budget''
                 ELSE ''On Budget'' END AS PROJECT_COST_STATUS,
            p.PERCENT_COMPLETE AS PROJECT_PERCENT_COMPLETE,
            CURRENT_TIMESTAMP() AS REFRESHED_AT, ''{domain}'' AS DOMAIN
        FROM RISK_COMMAND_CENTER.SILVER.RISK_EVENTS r
        JOIN RISK_COMMAND_CENTER.SILVER.PROJECTS_CLEAN p ON r.PROJECT_ID=p.PROJECT_ID
        WHERE UPPER(r.STATUS)=''OPEN''
          AND COALESCE(r.DOMAIN,''construction'')=''{domain}''
          AND COALESCE(p.DOMAIN,''construction'')=''{domain}''
          AND p.PROJECT_NAME IS NOT NULL
          AND TRIM(p.PROJECT_NAME) NOT IN ('''',''null'',''None'')
    """).collect()
    count = session.sql(f"SELECT COUNT(*) AS N FROM RISK_COMMAND_CENTER.GOLD.UNIFIED_RISK_MATRIX WHERE DOMAIN=''{domain}''").collect()[0][''N'']
    results.append(f"UNIFIED_RISK_MATRIX: {count}")

    session.sql(f"DELETE FROM RISK_COMMAND_CENTER.GOLD.FINANCIAL_SUMMARY WHERE DOMAIN=''{domain}''").collect()
    session.sql(f"""
        INSERT INTO RISK_COMMAND_CENTER.GOLD.FINANCIAL_SUMMARY
        SELECT p.PROJECT_ID, p.PROJECT_NAME,
            COALESCE(p.CURRENT_CONTRACT_VALUE,0) AS APPROVED_BUDGET,
            COALESCE(p.ACTUAL_COST,0) AS ACTUAL_COST_TO_DATE,
            CASE WHEN COALESCE(p.PERCENT_COMPLETE,0)>0 THEN COALESCE(p.ACTUAL_COST,0)*(100.0/p.PERCENT_COMPLETE)
                 ELSE COALESCE(p.CURRENT_CONTRACT_VALUE,0) END AS FORECAST_COST_AT_COMPLETION,
            ROUND(COALESCE(p.ACTUAL_COST,0)/NULLIF(p.CURRENT_CONTRACT_VALUE,0)*100,1) AS BUDGET_UTILIZATION_PCT,
            COALESCE(p.ACTUAL_COST,0)-COALESCE(p.CURRENT_CONTRACT_VALUE,0) AS FORECAST_VARIANCE,
            0,0,COALESCE(p.CURRENT_CONTRACT_VALUE,0),0,0,COALESCE(p.CURRENT_CONTRACT_VALUE,0),
            0,0,0,0,0,COALESCE(p.ACTUAL_COST,0),COALESCE(p.ACTUAL_COST,0),
            CASE WHEN COALESCE(p.ACTUAL_COST,0)>COALESCE(p.CURRENT_CONTRACT_VALUE,1)*1.1 THEN ''Over Budget'' ELSE ''On Budget'' END,
            CASE WHEN COALESCE(p.ACTUAL_COST,0)>COALESCE(p.CURRENT_CONTRACT_VALUE,1)*1.05 THEN ''Concerning'' ELSE ''Healthy'' END,
            CURRENT_TIMESTAMP(), ''{domain}''
        FROM RISK_COMMAND_CENTER.SILVER.PROJECTS_CLEAN p
        WHERE COALESCE(p.DOMAIN,''construction'')=''{domain}''
          AND p.PROJECT_NAME IS NOT NULL AND TRIM(p.PROJECT_NAME) NOT IN ('''',''null'',''None'')
    """).collect()
    count = session.sql(f"SELECT COUNT(*) AS N FROM RISK_COMMAND_CENTER.GOLD.FINANCIAL_SUMMARY WHERE DOMAIN=''{domain}''").collect()[0][''N'']
    results.append(f"FINANCIAL_SUMMARY: {count}")

    session.sql(f"DELETE FROM RISK_COMMAND_CENTER.GOLD.VENDOR_SCORECARD WHERE DOMAIN=''{domain}''").collect()
    session.sql(f"""
        INSERT INTO RISK_COMMAND_CENTER.GOLD.VENDOR_SCORECARD
        SELECT v.VENDOR_ID, v.VENDOR_NAME, v.TRADE_CATEGORY, COALESCE(v.PERFORMANCE_GRADE,''B''),
            v.PRIMARY_CONTACT, v.CONTACT_EMAIL, v.INSURANCE_EXPIRY,
            CASE WHEN v.INSURANCE_EXPIRY<CURRENT_DATE() THEN ''Expired''
                 WHEN v.INSURANCE_EXPIRY<DATEADD(''day'',30,CURRENT_DATE()) THEN ''Expiring Soon'' ELSE ''Valid'' END,
            0,0,0,0,0,0,0,
            CASE v.PERFORMANCE_GRADE WHEN ''A'' THEN 10 WHEN ''B'' THEN 25 WHEN ''C'' THEN 50 ELSE 35 END,
            CURRENT_TIMESTAMP(), ''{domain}''
        FROM RISK_COMMAND_CENTER.SILVER.VENDORS v
        WHERE COALESCE(v.DOMAIN,''construction'')=''{domain}''
    """).collect()
    count = session.sql(f"SELECT COUNT(*) AS N FROM RISK_COMMAND_CENTER.GOLD.VENDOR_SCORECARD WHERE DOMAIN=''{domain}''").collect()[0][''N'']
    results.append(f"VENDOR_SCORECARD: {count}")

    session.sql(f"DELETE FROM RISK_COMMAND_CENTER.GOLD.SAFETY_DASHBOARD WHERE DOMAIN=''{domain}''").collect()
    session.sql(f"""
        INSERT INTO RISK_COMMAND_CENTER.GOLD.SAFETY_DASHBOARD
        SELECT p.PROJECT_ID, p.PROJECT_NAME, p.LOCATION, p.PROJECT_MANAGER,
            0,0,0,0,NULL,
            DATEDIFF(''day'',COALESCE(p.START_DATE,''2025-01-01''),CURRENT_DATE()),
            0,0,0,''Low'',''Compliant'',CURRENT_TIMESTAMP(),''{domain}''
        FROM RISK_COMMAND_CENTER.SILVER.PROJECTS_CLEAN p
        WHERE COALESCE(p.DOMAIN,''construction'')=''{domain}''
          AND p.PROJECT_NAME IS NOT NULL AND TRIM(p.PROJECT_NAME) NOT IN ('''',''null'',''None'')
    """).collect()
    count = session.sql(f"SELECT COUNT(*) AS N FROM RISK_COMMAND_CENTER.GOLD.SAFETY_DASHBOARD WHERE DOMAIN=''{domain}''").collect()[0][''N'']
    results.append(f"SAFETY_DASHBOARD: {count}")

    return f"Gold refresh ({domain}): " + " | ".join(results)
';
CREATE OR REPLACE PROCEDURE RISK_COMMAND_CENTER.OPS.SP_RUN_FULL_PIPELINE("DOMAIN" VARCHAR DEFAULT 'construction')
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
ARTIFACT_REPOSITORY = snowflake.snowpark.pypi_shared_repository
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run_full_pipeline'
EXECUTE AS OWNER
AS '
def run_full_pipeline(session, domain=''construction''):
    results = []

    def count(table):
        try:
            return session.sql(f"SELECT COUNT(*) AS C FROM {table}").collect()[0][''C'']
        except Exception:
            return ''?''

    # Stage 1 — Parse + self-heal
    try:
        r = session.sql("CALL RISK_COMMAND_CENTER.OPS.SP_PROCESS_BRONZE_TO_SILVER()").collect()
        msg = r[0][0] if r else ''OK''
        chunks = count(''RISK_COMMAND_CENTER.SILVER.CHUNKS'')
        results.append(f"Stage 1 (Parse): {msg} | Chunks: {chunks}")
    except Exception as e:
        results.append(f"Stage 1 (Parse): FAILED - {str(e)[:120]}")

    # Stage 2 — Knowledge graph
    try:
        r = session.sql("CALL RISK_COMMAND_CENTER.OPS.SP_EXTRACT_GRAPH()").collect()
        msg   = r[0][0] if r else ''OK''
        nodes = count(''RISK_COMMAND_CENTER.SILVER.GRAPH_NODES'')
        results.append(f"Stage 2 (Graph): {msg} | Nodes: {nodes}")
    except Exception as e:
        results.append(f"Stage 2 (Graph): FAILED - {str(e)[:120]}")

    # Stage 3 — Vector embeddings
    try:
        r = session.sql("CALL RISK_COMMAND_CENTER.OPS.SP_GENERATE_VECTORS()").collect()
        msg  = r[0][0] if r else ''OK''
        vecs = count(''RISK_COMMAND_CENTER.SILVER.VECTORS'')
        results.append(f"Stage 3 (Vectors): {msg} | Vectors: {vecs}")
    except Exception as e:
        results.append(f"Stage 3 (Vectors): FAILED - {str(e)[:120]}")

    # Stage 4 — Structured extraction (domain-aware, self-healing project_id)
    try:
        r = session.sql(f"CALL RISK_COMMAND_CENTER.OPS.SP_EXTRACT_STRUCTURED_DATA(''{domain}'')").collect()
        msg    = r[0][0] if r else ''OK''
        risks  = count(''RISK_COMMAND_CENTER.SILVER.RISK_EVENTS'')
        results.append(f"Stage 4 (Structure/{domain}): {msg} | Risk Events: {risks}")
    except Exception as e:
        results.append(f"Stage 4 (Structure): FAILED - {str(e)[:120]}")

    # Stage 5 — Silver enrichment (vendors from CSV + percent_complete from chunks)
    try:
        r = session.sql("CALL RISK_COMMAND_CENTER.OPS.SP_POPULATE_SILVER_FROM_GRAPH()").collect()
        msg      = r[0][0] if r else ''OK''
        vendors  = count(''RISK_COMMAND_CENTER.SILVER.VENDORS'')
        projects = count(''RISK_COMMAND_CENTER.SILVER.PROJECTS'')
        results.append(f"Stage 5 (Enrich): {msg} | Projects: {projects}, Vendors: {vendors}")
    except Exception as e:
        results.append(f"Stage 5 (Enrich): FAILED - {str(e)[:120]}")

    # Stage 6 — Gold refresh (cleanup + domain-filtered aggregation)
    try:
        r = session.sql(f"CALL RISK_COMMAND_CENTER.OPS.SP_REFRESH_GOLD(''{domain}'')").collect()
        msg = r[0][0] if r else ''OK''
        results.append(f"Stage 6 (Gold): {msg}")
    except Exception as e:
        results.append(f"Stage 6 (Gold): FAILED - {str(e)[:120]}")

    return "\\n".join(results)
';
create or replace task RISK_COMMAND_CENTER.OPS.TASK_AUTO_PROCESS_DOCS
	warehouse=COMPUTE_WH
	schedule='5 MINUTE'
	as CALL RISK_COMMAND_CENTER.OPS.SP_RUN_FULL_PIPELINE();
create or replace schema RISK_COMMAND_CENTER.PUBLIC;

create or replace schema RISK_COMMAND_CENTER.SILVER;

create or replace TABLE RISK_COMMAND_CENTER.SILVER.AI_CACHE (
	CACHE_KEY VARCHAR(16777216),
	PROMPT_HASH VARCHAR(16777216),
	RESPONSE_TEXT VARCHAR(16777216),
	MODEL VARCHAR(16777216),
	CREATED_AT TIMESTAMP_NTZ(9) DEFAULT CURRENT_TIMESTAMP()
);
create or replace TABLE RISK_COMMAND_CENTER.SILVER.CHUNKS (
	CHUNK_ID VARCHAR(16777216) NOT NULL,
	DOCUMENT_ID VARCHAR(16777216),
	CHUNK_INDEX NUMBER(38,0),
	CHUNK_TEXT VARCHAR(16777216),
	PAGE_NUMBER NUMBER(38,0),
	CREATED_AT TIMESTAMP_NTZ(9) DEFAULT CURRENT_TIMESTAMP(),
	DOMAIN VARCHAR(50) DEFAULT 'construction',
	primary key (CHUNK_ID)
);
create or replace TABLE RISK_COMMAND_CENTER.SILVER.CONTRACTS (
	CONTRACT_ID VARCHAR(16777216),
	PROJECT_ID VARCHAR(16777216),
	CONTRACT_TYPE VARCHAR(16777216),
	CONTRACTOR VARCHAR(16777216),
	SCOPE_DESCRIPTION VARCHAR(16777216),
	ORIGINAL_CONTRACT_VALUE NUMBER(18,2),
	CHANGE_ORDER_AMOUNT NUMBER(18,2),
	CURRENT_CONTRACT_VALUE NUMBER(18,2),
	COMMITTED_AMOUNT NUMBER(18,2),
	LD_PER_DAY NUMBER(18,2),
	RETAINAGE_PERCENT FLOAT,
	RISK_LEVEL VARCHAR(16777216),
	STATUS VARCHAR(16777216),
	LOADED_AT TIMESTAMP_LTZ(9)
);
create or replace TABLE RISK_COMMAND_CENTER.SILVER.DOMAIN_CONFIG (
	CONFIG_KEY VARCHAR(16777216),
	CONFIG_VALUE VARIANT,
	UPDATED_AT TIMESTAMP_NTZ(9) DEFAULT CURRENT_TIMESTAMP()
);
create or replace TABLE RISK_COMMAND_CENTER.SILVER.GRAPH_EDGES (
	EDGE_ID VARCHAR(16777216) NOT NULL,
	SOURCE_NODE_ID VARCHAR(16777216),
	TARGET_NODE_ID VARCHAR(16777216),
	RELATIONSHIP_TYPE VARCHAR(16777216),
	CONFIDENCE FLOAT,
	EVIDENCE_CHUNK_ID VARCHAR(16777216),
	CREATED_AT TIMESTAMP_NTZ(9) DEFAULT CURRENT_TIMESTAMP(),
	primary key (EDGE_ID)
);
create or replace TABLE RISK_COMMAND_CENTER.SILVER.GRAPH_NODES (
	NODE_ID VARCHAR(16777216) NOT NULL,
	NODE_TYPE VARCHAR(16777216),
	NODE_NAME VARCHAR(16777216),
	PROPERTIES VARIANT,
	SOURCE_DOCUMENT_ID VARCHAR(16777216),
	CREATED_AT TIMESTAMP_NTZ(9) DEFAULT CURRENT_TIMESTAMP(),
	primary key (NODE_ID)
);
create or replace TABLE RISK_COMMAND_CENTER.SILVER.INVOICES (
	INVOICE_ID VARCHAR(16777216),
	PROJECT_ID VARCHAR(16777216),
	VENDOR_ID VARCHAR(16777216),
	CONTRACT_ID VARCHAR(16777216),
	VENDOR_CONTRACT_ID VARCHAR(16777216),
	COST_CODE VARCHAR(16777216),
	INVOICE_NUMBER VARCHAR(16777216),
	INVOICE_DATE DATE,
	BILLING_PERIOD_START DATE,
	BILLING_PERIOD_END DATE,
	PREVIOUS_BILLED_AMOUNT NUMBER(18,2),
	CURRENT_INVOICE_AMOUNT NUMBER(18,2),
	LOADED_AT TIMESTAMP_LTZ(9)
);
create or replace TABLE RISK_COMMAND_CENTER.SILVER.PROJECTS (
	PROJECT_ID VARCHAR(16777216),
	PROJECT_NAME VARCHAR(16777216),
	PROJECT_TYPE VARCHAR(16777216),
	LOCATION VARCHAR(16777216),
	CLIENT VARCHAR(16777216),
	PROJECT_MANAGER VARCHAR(16777216),
	SUPERINTENDENT VARCHAR(16777216),
	ORIGINAL_CONTRACT_VALUE NUMBER(18,2),
	APPROVED_CHANGE_ORDERS NUMBER(18,2),
	CURRENT_CONTRACT_VALUE NUMBER(18,2),
	ORIGINAL_BUDGET NUMBER(18,2),
	CURRENT_BUDGET NUMBER(18,2),
	ACTUAL_COST_TO_DATE NUMBER(18,2),
	ACTUAL_COST NUMBER(18,2),
	FORECAST_COST_AT_COMPLETION NUMBER(18,2),
	START_DATE DATE,
	PLANNED_COMPLETION DATE,
	FORECAST_COMPLETION DATE,
	PERCENT_COMPLETE FLOAT,
	SCHEDULE_STATUS VARCHAR(16777216),
	COST_STATUS VARCHAR(16777216),
	LOADED_AT TIMESTAMP_LTZ(9),
	DOMAIN VARCHAR(50) DEFAULT 'construction'
);
create or replace TABLE RISK_COMMAND_CENTER.SILVER.RISK_EVENTS (
	RISK_ID VARCHAR(16777216),
	PROJECT_ID VARCHAR(16777216),
	RISK_CATEGORY VARCHAR(16777216),
	RISK_TITLE VARCHAR(16777216),
	RISK_DESCRIPTION VARCHAR(16777216),
	SEVERITY VARCHAR(16777216),
	LIKELIHOOD VARCHAR(16777216),
	RISK_SCORE NUMBER(38,0),
	FINANCIAL_EXPOSURE NUMBER(18,2),
	SCHEDULE_IMPACT_DAYS NUMBER(38,0),
	STATUS VARCHAR(16777216),
	LOADED_AT TIMESTAMP_LTZ(9),
	DOMAIN VARCHAR(50) DEFAULT 'construction',
	SOURCE_CHUNK_ID VARCHAR(16777216)
);
create or replace TABLE RISK_COMMAND_CENTER.SILVER.SAFETY_INCIDENTS (
	INCIDENT_ID VARCHAR(16777216),
	PROJECT_ID VARCHAR(16777216),
	INCIDENT_DATE DATE,
	SEVERITY VARCHAR(16777216),
	DESCRIPTION VARCHAR(16777216),
	ROOT_CAUSE VARCHAR(16777216),
	SUPERINTENDENT VARCHAR(16777216),
	RECORDABLE BOOLEAN,
	LOST_TIME BOOLEAN,
	LOADED_AT TIMESTAMP_LTZ(9)
);
create or replace TABLE RISK_COMMAND_CENTER.SILVER.SAFETY_OBSERVATIONS (
	OBSERVATION_ID VARCHAR(16777216),
	PROJECT_ID VARCHAR(16777216),
	OBSERVATION_DATE DATE,
	CATEGORY VARCHAR(16777216),
	RISK_LEVEL VARCHAR(16777216),
	DESCRIPTION VARCHAR(16777216),
	STATUS VARCHAR(16777216),
	LOADED_AT TIMESTAMP_LTZ(9)
);
create or replace TABLE RISK_COMMAND_CENTER.SILVER.VECTORS (
	VECTOR_ID VARCHAR(16777216) NOT NULL,
	CHUNK_ID VARCHAR(16777216),
	EMBEDDING_VECTOR VECTOR(FLOAT, 1024),
	CREATED_AT TIMESTAMP_NTZ(9) DEFAULT CURRENT_TIMESTAMP(),
	primary key (VECTOR_ID)
);
create or replace TABLE RISK_COMMAND_CENTER.SILVER.VENDORS (
	VENDOR_ID VARCHAR(16777216),
	VENDOR_NAME VARCHAR(16777216),
	LEGAL_NAME VARCHAR(16777216),
	TRADE_CATEGORY VARCHAR(16777216),
	TRADE_CODE VARCHAR(16777216),
	PRIMARY_CONTACT VARCHAR(16777216),
	CONTACT_EMAIL VARCHAR(16777216),
	PERFORMANCE_GRADE VARCHAR(16777216),
	NOTES VARCHAR(16777216),
	INSURANCE_EXPIRY DATE,
	LOADED_AT TIMESTAMP_LTZ(9),
	DOMAIN VARCHAR(50) DEFAULT 'construction'
);
create or replace TABLE RISK_COMMAND_CENTER.SILVER.VENDOR_CONTRACTS (
	VENDOR_CONTRACT_ID VARCHAR(16777216),
	PROJECT_ID VARCHAR(16777216),
	VENDOR_ID VARCHAR(16777216),
	CONTRACT_ID VARCHAR(16777216),
	COST_CODE VARCHAR(16777216),
	SUBCONTRACT_SCOPE VARCHAR(16777216),
	SUBCONTRACT_VALUE NUMBER(18,2),
	COMMITTED_TO_DATE NUMBER(18,2),
	STATUS VARCHAR(16777216),
	PAYMENT_TERMS VARCHAR(16777216),
	RISK_RATING VARCHAR(16777216),
	LOADED_AT TIMESTAMP_LTZ(9)
);
create or replace view RISK_COMMAND_CENTER.SILVER.PROJECTS_CLEAN(
	PROJECT_ID,
	DOMAIN,
	PROJECT_NAME,
	PROJECT_TYPE,
	LOCATION,
	CLIENT,
	PROJECT_MANAGER,
	START_DATE,
	PLANNED_COMPLETION,
	FORECAST_COMPLETION,
	CURRENT_CONTRACT_VALUE,
	ORIGINAL_CONTRACT_VALUE,
	ACTUAL_COST,
	PERCENT_COMPLETE,
	SCHEDULE_STATUS,
	COST_STATUS
) as
SELECT 
    PROJECT_ID,
    COALESCE(MAX(DOMAIN), 'construction') AS DOMAIN,
    MAX(CASE WHEN PROJECT_NAME != PROJECT_ID THEN PROJECT_NAME ELSE NULL END) AS PROJECT_NAME,
    MAX(PROJECT_TYPE) AS PROJECT_TYPE,
    MAX(LOCATION) AS LOCATION,
    MAX(CLIENT) AS CLIENT,
    MAX(PROJECT_MANAGER) AS PROJECT_MANAGER,
    MAX(START_DATE) AS START_DATE,
    MAX(PLANNED_COMPLETION) AS PLANNED_COMPLETION,
    MAX(FORECAST_COMPLETION) AS FORECAST_COMPLETION,
    MAX(COALESCE(CURRENT_CONTRACT_VALUE, 0)) AS CURRENT_CONTRACT_VALUE,
    MAX(COALESCE(ORIGINAL_CONTRACT_VALUE, 0)) AS ORIGINAL_CONTRACT_VALUE,
    MAX(COALESCE(ACTUAL_COST, 0)) AS ACTUAL_COST,
    MAX(COALESCE(PERCENT_COMPLETE, 0)) AS PERCENT_COMPLETE,
    MAX(SCHEDULE_STATUS) AS SCHEDULE_STATUS,
    MAX(COST_STATUS) AS COST_STATUS
FROM RISK_COMMAND_CENTER.SILVER.PROJECTS
GROUP BY PROJECT_ID;
create or replace schema RISK_COMMAND_CENTER.STREAMLIT;

create or replace streamlit RISK_COMMAND_CENTER.STREAMLIT.RISK_COMMAND_CENTER
	root_location='@RISK_COMMAND_CENTER.STREAMLIT.RISK_COMMAND_CENTER_STAGE
	main_file='main.py'
	query_warehouse='COMPUTE_WH'
	title='Enterprise Risk Command Center';
create or replace streamlit RISK_COMMAND_CENTER.STREAMLIT.STREAMLIT_APP
	main_file='main.py'
	query_warehouse='COMPUTE_WH';
