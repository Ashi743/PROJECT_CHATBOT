from langchain_core.tools import tool
import pandas as pd
from pathlib import Path
import json
from tools.csv_ingest_tool import search_dataset, get_dataset_info

UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"

@tool
def analyze_data(dataset_name: str, operation: str, params: str = "") -> str:
    """
    Analyze CSV/Excel data using pandas with RAG support. The LLM uses this to answer questions about datasets.

    Args:
        dataset_name: Name of the dataset to analyze (e.g., 'sales_data')
        operation: Type of analysis. Valid options:
            - 'head' → Show first N rows (param: N, default 5)
            - 'tail' → Show last N rows (param: N, default 5)
            - 'describe' → Statistical summary of numeric columns
            - 'info' → Column names, data types, null counts
            - 'shape' → Number of rows and columns
            - 'columns' → List all column names
            - 'dtypes' → Data types of all columns
            - 'value_counts' → Count unique values (param: column_name)
            - 'groupby_sum' → Group by and sum (param: "group_col,value_col")
            - 'groupby_mean' → Group by and average (param: "group_col,value_col")
            - 'groupby_count' → Group by and count (param: "group_col")
            - 'filter' → Filter rows (param: "column==value" or "column>10")
            - 'correlation' → Correlation matrix of numeric columns
            - 'unique' → Count of unique values per column
            - 'sort' → Sort by column, show top rows (param: "column,desc,N")
            - 'null_count' → Count null values per column
            - 'sample' → Show random N rows (param: N, default 5)
            - 'rag_search' → RAG-based semantic search (param: "your natural language query")
            - 'dataset_info' → Get metadata about dataset
            - 'visualize' → Generate all plots (histograms, heatmap, bar charts, time series, box plots)
            - 'histogram' → Distribution histogram for numeric columns
            - 'correlation_plot' → Correlation heatmap
            - 'bar_chart' → Top values for categorical columns
            - 'time_series' → Time series trend plot
            - 'box_plot' → Box plots for outlier detection
            - 'insights' → Complete data insights (statistics + all visualizations)

    Returns:
        Formatted string result of the analysis

    Examples:
        - analyze_data(dataset_name='sales', operation='head', params='10')
        - analyze_data(dataset_name='sales', operation='describe')
        - analyze_data(dataset_name='sales', operation='rag_search', params='high performing regions')
        - analyze_data(dataset_name='sales', operation='groupby_sum', params='region,amount')
    """
    try:
        # Find the file
        file_path = None
        for ext in ['.csv', '.xlsx', '.xls']:
            candidate = UPLOAD_DIR / f"{dataset_name}{ext}"
            if candidate.exists():
                file_path = candidate
                break

        if not file_path and operation not in ['dataset_info', 'rag_search', 'visualize', 'histogram', 'correlation_plot', 'bar_chart', 'time_series', 'box_plot', 'insights']:
            return f"[ERROR] Dataset '{dataset_name}' not found in uploads. Available files: {list(UPLOAD_DIR.glob('*'))}"

        # Load dataframe for all operations except dataset_info, rag_search, and visualizations
        df = None
        visualization_ops = ['visualize', 'histogram', 'correlation_plot', 'bar_chart', 'time_series', 'box_plot', 'insights']
        if operation not in ['dataset_info', 'rag_search'] + visualization_ops:
            if file_path and file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            elif file_path:
                df = pd.read_excel(file_path)
        elif operation in visualization_ops:
            if file_path and file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            elif file_path:
                df = pd.read_excel(file_path)

        # Check if dataframe was loaded for operations that require it
        if operation not in ['dataset_info', 'rag_search'] and df is None:
            return f"[ERROR] Could not load dataset '{dataset_name}'"

        # Execute operation
        if operation == 'head' and df is not None:
            n = int(params) if params else 5
            return f"First {n} rows of '{dataset_name}':\n\n{df.head(n).to_string()}"

        elif operation == 'tail' and df is not None:
            n = int(params) if params else 5
            return f"Last {n} rows of '{dataset_name}':\n\n{df.tail(n).to_string()}"

        elif operation == 'describe':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            desc = df.describe()
            summary = f"**Statistical Summary of '{dataset_name}':**\n\n"
            for col in desc.columns:
                summary += f"**{col}:** Count={int(desc[col]['count'])} | Mean={desc[col]['mean']:.2f} | Std={desc[col]['std']:.2f} | Min={desc[col]['min']:.2f} | Max={desc[col]['max']:.2f}\n"
            summary += f"\n💡 **For better insights with visualizations, ask me to 'visualize {dataset_name}' or 'show plots for {dataset_name}'**"
            return summary

        elif operation == 'info':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            info_str = f"Dataset: {dataset_name}\nShape: {df.shape}\nColumns:\n"
            for col in df.columns:
                info_str += f"  {col}: {df[col].dtype} (nulls: {df[col].isnull().sum()})\n"
            return info_str

        elif operation == 'shape':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            rows, cols = df.shape
            return f"Dataset '{dataset_name}': {rows} rows, {cols} columns"

        elif operation == 'columns':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            return f"Columns in '{dataset_name}':\n" + ", ".join(df.columns.tolist())

        elif operation == 'dtypes':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            return f"Data types in '{dataset_name}':\n{df.dtypes.to_string()}"

        elif operation == 'value_counts':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            if not params:
                return "[ERROR] value_counts requires column name as param"
            if params not in df.columns:
                return f"[ERROR] Column '{params}' not found. Available: {df.columns.tolist()}"
            counts = df[params].value_counts()
            return f"Value counts for '{params}' in '{dataset_name}':\n{counts.to_string()}"

        elif operation == 'groupby_sum':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            parts = params.split(',')
            if len(parts) != 2:
                return "[ERROR] groupby_sum requires 'group_col,value_col'"
            group_col, value_col = parts[0].strip(), parts[1].strip()
            if group_col not in df.columns or value_col not in df.columns:
                return f"[ERROR] Columns not found. Available: {df.columns.tolist()}"
            result = df.groupby(group_col)[value_col].sum()
            return f"Sum by {group_col} in '{dataset_name}':\n{result.to_string()}"

        elif operation == 'groupby_mean':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            parts = params.split(',')
            if len(parts) != 2:
                return "[ERROR] groupby_mean requires 'group_col,value_col'"
            group_col, value_col = parts[0].strip(), parts[1].strip()
            if group_col not in df.columns or value_col not in df.columns:
                return f"[ERROR] Columns not found. Available: {df.columns.tolist()}"
            result = df.groupby(group_col)[value_col].mean()
            return f"Mean by {group_col} in '{dataset_name}':\n{result.to_string()}"

        elif operation == 'groupby_count':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            if not params:
                return "[ERROR] groupby_count requires column name as param"
            if params not in df.columns:
                return f"[ERROR] Column '{params}' not found. Available: {df.columns.tolist()}"
            result = df.groupby(params).size()
            return f"Count by {params} in '{dataset_name}':\n{result.to_string()}"

        elif operation == 'filter':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            try:
                filtered = df.query(params)
                return f"Filtered results (first 10):\n{filtered.head(10).to_string()}"
            except Exception as e:
                return f"Error in filter query: {str(e)}"

        elif operation == 'correlation':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            numeric_df = df.select_dtypes(include=['number'])
            if numeric_df.empty:
                return "No numeric columns found for correlation"
            corr = numeric_df.corr()
            return f"Correlation matrix:\n{corr.to_string()}"

        elif operation == 'unique':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            unique_counts = df.nunique()
            return f"Unique values per column in '{dataset_name}':\n{unique_counts.to_string()}"

        elif operation == 'sort':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            parts = params.split(',') if params else []
            if len(parts) < 1:
                return "[ERROR] sort requires 'column' or 'column,asc/desc,N'"
            col = parts[0].strip()
            if col not in df.columns:
                return f"[ERROR] Column '{col}' not found. Available: {df.columns.tolist()}"
            ascending = True if (len(parts) < 2 or parts[1].strip().lower() == 'asc') else False
            n = int(parts[2]) if len(parts) >= 3 else 10
            sorted_df = df.sort_values(col, ascending=ascending).head(n)
            return f"Top {n} rows sorted by {col}:\n{sorted_df.to_string()}"

        elif operation == 'null_count':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            nulls = df.isnull().sum()
            return f"Null values per column in '{dataset_name}':\n{nulls.to_string()}"

        elif operation == 'sample':
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            n = int(params) if params else 5
            sample = df.sample(min(n, len(df)))
            return f"{n} random rows from '{dataset_name}':\n{sample.to_string()}"

        elif operation == 'rag_search':
            if not params:
                return "[ERROR] rag_search requires a search query as param"
            results = search_dataset(dataset_name, params, n_results=5)
            if not results or 'error' in results[0]:
                return f"No results found for query: '{params}'"

            output = f"RAG Search Results for '{params}' in '{dataset_name}':\n\n"
            for i, result in enumerate(results, 1):
                if 'error' in result:
                    return f"Search error: {result['error']}"
                output += f"Result {i}:\n{result['document']}\n\n"
            return output

        elif operation == 'dataset_info':
            info = get_dataset_info(dataset_name)
            if 'error' in info:
                return f"[ERROR] {info['error']}"
            info_str = f"Dataset Information: {dataset_name}\n"
            info_str += f"  Rows: {info.get('rows')}\n"
            info_str += f"  Columns: {', '.join(info.get('columns', []))}\n"
            info_str += f"  Numeric: {', '.join(info.get('numeric_columns', []))}\n"
            info_str += f"  Categorical: {', '.join(info.get('categorical_columns', []))}\n"
            if info.get('user_description'):
                info_str += f"  Description: {info['user_description']}\n"
            return info_str

        elif operation in ['visualize', 'histogram', 'correlation_plot', 'bar_chart', 'time_series', 'box_plot', 'insights']:
            if df is None:
                return f"[ERROR] Could not load dataset '{dataset_name}'"
            try:
                from tools.plot_utils import PlotGenerator

                generator = PlotGenerator(df, dataset_name)
                result = generator.generate_all_plots()

                if result["status"] == "ok":
                    plots_info = result["plots"]

                    # For 'insights' operation, include statistics too
                    if operation == 'insights':
                        output = f"## Data Insights for '{dataset_name}'\n\n"
                        output += f"**Dataset Shape:** {len(df):,} rows × {len(df.columns)} columns\n\n"

                        # Add quick stats
                        output += "### Key Statistics\n"
                        desc = df.describe()
                        for col in desc.columns:
                            output += f"\n**{col}:** Mean={desc[col]['mean']:.2f}, Std={desc[col]['std']:.2f}, Range=[{desc[col]['min']:.2f}, {desc[col]['max']:.2f}]\n"

                        output += "\n### Visualizations\n"
                    else:
                        output = f"Generated {len(plots_info)} visualization(s) for '{dataset_name}':\n\n"

                    for plot_type, plot_meta in plots_info.items():
                        output += f"📊 **{plot_meta['title']}**\n\n"

                    output += "---\n"

                    # Embed plot paths so frontend can detect and display them
                    for plot_type, plot_meta in plots_info.items():
                        output += f"[PLOT_IMAGE:{plot_meta['path']}]\n"

                    return output
                else:
                    return f"Error generating plots: {result.get('message', 'Unknown error')}"
            except Exception as e:
                return f"Error generating visualizations: {str(e)}"

        else:
            return f"Unknown operation: '{operation}'. Valid: head, tail, describe, info, shape, columns, dtypes, value_counts, groupby_sum, groupby_mean, groupby_count, filter, correlation, unique, sort, null_count, sample, rag_search, dataset_info, visualize, histogram, correlation_plot, bar_chart, time_series, box_plot, insights"

    except Exception as e:
        return f"Error analyzing data: {str(e)}"

if __name__ == "__main__":
    print("CSV Analysis Tool with RAG Support")
    print("This tool is used by the LLM to analyze CSV/Excel datasets with semantic search.")
