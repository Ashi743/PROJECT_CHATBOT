# CSV Analysis Spec Sheet

## Purpose
Analyze CSV/Excel datasets with 20+ operations: head, tail, describe, groupby, filter, sort, correlation, visualizations.
RAG-enabled semantic search. Plots: histograms, heatmaps, bar charts, time series, box plots.
Pandas + ChromaDB integration.

## Status
[WIP] - Core operations working, visualizations in progress

## Trigger Phrases
- "show me the first 10 rows of sales data"
- "what's the average by region"
- "visualize the sales dataset"
- "find rows where profit > 1000"
- "search for high performing regions in the data"
- "generate correlation heatmap"

## Input Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| dataset_name | str | yes | none | Dataset name (file without extension) |
| operation | str | yes | none | See Operations table below |
| params | str | no | varies | Parameters specific to operation |
| db_name | str | no | analytics | Database name (for SQL integration) |

## Operations (20+ supported)
| Operation | Params | Output |
|-----------|--------|--------|
| head | N (rows) | First N rows |
| tail | N (rows) | Last N rows |
| describe | none | Mean, std, min, max per numeric column |
| info | none | Column names, types, null counts |
| shape | none | Rows x Columns |
| columns | none | List all column names |
| dtypes | none | Data type per column |
| value_counts | column_name | Unique value counts |
| groupby_sum | group_col,value_col | Sum by group |
| groupby_mean | group_col,value_col | Average by group |
| groupby_count | column_name | Count by group |
| filter | column>value (or ==) | Filtered rows |
| correlation | none | Correlation matrix |
| unique | none | Unique count per column |
| sort | column,asc/desc,N | Top N sorted rows |
| null_count | none | Null value count per column |
| sample | N | N random rows |
| rag_search | "your query" | Semantic search via ChromaDB |
| dataset_info | none | Metadata: rows, columns, types |
| visualize | none | All plots (histograms, heatmap, bar, time series, box) |
| histogram | none | Distribution for numeric columns |
| correlation_plot | none | Heatmap of correlations |
| bar_chart | none | Top values for categorical columns |
| time_series | none | Trend plot (requires date column) |
| box_plot | none | Outlier detection |
| insights | none | Statistics + all visualizations |

## Output Format
First 5 rows of 'sales_data':

    region    amount    date       status
0   USA       1500.50   2026-04-01 completed
1   Europe    2345.75   2026-04-02 completed
2   Asia      890.25    2026-04-03 pending

Dataset Information: sales_data
  Rows: 150
  Columns: region, amount, date, status
  Numeric: amount, quantity
  Categorical: region, status

## Dependencies
- pandas (pip: pandas)
- openpyxl (pip: openpyxl) - for Excel
- matplotlib (pip: matplotlib) - for plots
- seaborn (pip: seaborn) - for visualizations
- langchain_core.tools

## HITL
No - read-only analysis (no write operations to data)

## Chaining
Combines with:
- nlp_tool → "analyze customer reviews dataset and extract sentiment"
- web_search → "search for industry benchmarks then compare with our data"

## Known Issues
- [WIP] Visualizations (plot generation) partially implemented
- RAG search requires ChromaDB initialized (handles gracefully if missing)
- Large datasets (>100k rows) may be slow for correlation matrices
- Time series requires date-parseable column

## Test Command
python -c "
from tools.csv_analysis_tool import analyze_data
# Assumes CSV uploaded to data/uploads/
print(analyze_data.invoke({
    'dataset_name': 'sales',
    'operation': 'head',
    'params': '10'
}))
"

## Bunge Relevance
Data exploration for commodity trading analysis, supply chain optimization, and market insights.

## Internal Notes
- Datasets uploaded to data/uploads/ (.csv, .xlsx, .xls)
- DataFrame stored in memory (no persistence during session)
- Visualizations saved to data/plots/ with [PLOT_IMAGE:path] markers
- RAG search calls search_dataset() from csv_ingest_tool
- Dataset info includes numeric/categorical column lists
- Null counts per column in info operation
