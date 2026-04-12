"""Shared test data schema -- Customer + SHARES_ACCOUNT graph definition.

Single source of truth for the graph schema used across tutorials,
E2E tests, UAT validation, and test fixtures.

These are DATA CONSTANTS, not helper functions. The notebook/test is
responsible for calling client.mappings.create(), etc.

The SQL references target a configurable Starburst catalog/schema.
Override STARBURST_CATALOG and STARBURST_SCHEMA for different environments.
"""

from graph_olap_schemas import (
    EdgeDefinition,
    NodeDefinition,
    PropertyDefinition,
)

# ---------------------------------------------------------------------------
# Starburst catalog/schema -- override for your environment
# ---------------------------------------------------------------------------
STARBURST_CATALOG: str = "default_catalog"
STARBURST_SCHEMA: str = "default_schema"
TABLE_PREFIX: str = f"{STARBURST_CATALOG}.{STARBURST_SCHEMA}"

# ---------------------------------------------------------------------------
# Naming conventions
# ---------------------------------------------------------------------------
MAPPING_NAME: str = "tutorial-customer-graph"
INSTANCE_NAME: str = "tutorial-instance"
INSTANCE_TTL: str = "PT1H"

# ---------------------------------------------------------------------------
# Node definitions
# ---------------------------------------------------------------------------
CUSTOMER_NODE = NodeDefinition(
    label="Customer",
    sql=f"""SELECT DISTINCT CAST(psdo_cust_id AS VARCHAR) AS id, MIN(bk_sectr) AS bk_sectr, COUNT(DISTINCT psdo_acno) AS account_count, MIN(acct_stus) AS acct_stus FROM "{STARBURST_CATALOG}"."{STARBURST_SCHEMA}".bis_acct_dh WHERE image_dt >= DATE '2020-01-01' GROUP BY psdo_cust_id""",
    primary_key={"name": "id", "type": "STRING"},
    properties=[
        PropertyDefinition(name="bk_sectr", type="STRING"),
        PropertyDefinition(name="account_count", type="INT64"),
        PropertyDefinition(name="acct_stus", type="STRING"),
    ],
)

NODE_DEFINITIONS = [CUSTOMER_NODE]

# ---------------------------------------------------------------------------
# Edge definitions
# ---------------------------------------------------------------------------
SHARES_ACCOUNT_EDGE = EdgeDefinition(
    type="SHARES_ACCOUNT",
    from_node="Customer",
    to_node="Customer",
    sql=f"""SELECT DISTINCT CAST(a.psdo_cust_id AS VARCHAR) AS from_id, CAST(b.psdo_cust_id AS VARCHAR) AS to_id FROM "{STARBURST_CATALOG}"."{STARBURST_SCHEMA}".bis_acct_dh a JOIN "{STARBURST_CATALOG}"."{STARBURST_SCHEMA}".bis_acct_dh b ON a.psdo_acno = b.psdo_acno AND a.psdo_cust_id < b.psdo_cust_id AND a.image_dt >= DATE '2020-01-01' AND b.image_dt >= DATE '2020-01-01'""",
    from_key="from_id",
    to_key="to_id",
)

EDGE_DEFINITIONS = [SHARES_ACCOUNT_EDGE]
