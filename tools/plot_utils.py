"""Visualization utilities for CSV data analysis."""

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import seaborn as sns
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

PLOTS_DIR = Path(__file__).parent.parent / "data" / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# Configure matplotlib
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def _detect_numeric_cols(df: pd.DataFrame) -> list[str]:
    """Detect numeric columns."""
    return df.select_dtypes(include=['int64', 'float64']).columns.tolist()

def _detect_categorical_cols(df: pd.DataFrame) -> list[str]:
    """Detect categorical columns (limit to 10 unique values)."""
    categorical = []
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() <= 20:
            categorical.append(col)
    return categorical

def _detect_date_cols(df: pd.DataFrame) -> list[str]:
    """Detect date/datetime columns."""
    date_cols = []
    for col in df.columns:
        try:
            pd.to_datetime(df[col], errors='raise')
            date_cols.append(col)
        except:
            pass
    return date_cols

def _detect_outliers(df: pd.DataFrame, col: str) -> bool:
    """Check if column has outliers using IQR method."""
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    outliers = df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)]
    return len(outliers) > 0

class PlotGenerator:
    """Generate visualization plots for CSV data."""

    def __init__(self, df: pd.DataFrame, dataset_name: str):
        self.df = df
        self.dataset_name = dataset_name
        self.plots = {}

    def generate_all_plots(self) -> dict:
        """Generate all available plots."""
        try:
            numeric_cols = _detect_numeric_cols(self.df)
            categorical_cols = _detect_categorical_cols(self.df)
            date_cols = _detect_date_cols(self.df)

            # Generate histograms for numeric columns
            if numeric_cols:
                self._generate_histograms(numeric_cols)

            # Generate correlation heatmap
            if len(numeric_cols) > 1:
                self._generate_correlation_heatmap(numeric_cols)

            # Generate bar charts for categorical columns
            if categorical_cols:
                self._generate_bar_charts(categorical_cols)

            # Generate time series if date column exists
            if date_cols and numeric_cols:
                self._generate_time_series(date_cols[0], numeric_cols[0])

            # Generate box plots if outliers detected
            cols_with_outliers = [col for col in numeric_cols if _detect_outliers(self.df, col)]
            if cols_with_outliers:
                self._generate_box_plots(cols_with_outliers)

            return {
                "status": "ok",
                "plots": self.plots,
                "plot_count": len(self.plots)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _generate_histograms(self, numeric_cols: list[str]):
        """Generate distribution histograms for numeric columns."""
        n_cols = len(numeric_cols)
        n_rows = (n_cols + 1) // 2

        _, axes = plt.subplots(n_rows, 2, figsize=(10, 4*n_rows))
        if n_rows == 1 and n_cols == 1:
            axes_list: list[Axes] = [axes[0]]  # type: ignore[assignment]
        elif n_rows == 1:
            axes_list: list[Axes] = list(axes)  # type: ignore[assignment]
        else:
            axes_list: list[Axes] = [ax for ax in axes.flatten()]  # type: ignore[assignment]

        for idx, col in enumerate(numeric_cols):
            ax: Axes = axes_list[idx]
            self.df[col].hist(bins=30, ax=ax, edgecolor='black', alpha=0.7)
            ax.set_title(f'Distribution of {col}', fontsize=12, fontweight='bold')
            ax.set_xlabel(col)
            ax.set_ylabel('Frequency')
            ax.grid(True, alpha=0.3)

        # Hide empty subplots
        for idx in range(len(numeric_cols), len(axes_list)):
            axes_list[idx].set_visible(False)

        plt.tight_layout()
        filename = f"{self.dataset_name}_histograms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = PLOTS_DIR / filename
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()

        self.plots['histograms'] = {
            'title': 'Distribution Histograms',
            'file': filename,
            'path': str(filepath),
            'cols': numeric_cols
        }

    def _generate_correlation_heatmap(self, numeric_cols: list[str]):
        """Generate correlation heatmap."""
        corr_matrix = self.df[numeric_cols].corr()

        _, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                    center=0, square=True, ax=ax, cbar_kws={'label': 'Correlation'})
        ax.set_title(f'Correlation Matrix - {self.dataset_name}', fontsize=14, fontweight='bold')
        plt.tight_layout()

        filename = f"{self.dataset_name}_correlation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = PLOTS_DIR / filename
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()

        self.plots['correlation'] = {
            'title': 'Correlation Heatmap',
            'file': filename,
            'path': str(filepath),
            'cols': numeric_cols
        }

    def _generate_bar_charts(self, categorical_cols: list[str]):
        """Generate top values bar charts for categorical columns."""
        n_cols = min(len(categorical_cols), 4)  # Limit to 4 charts
        n_rows = (n_cols + 1) // 2

        _, axes = plt.subplots(n_rows, 2, figsize=(10, 4*n_rows))
        if n_rows == 1 and n_cols == 1:
            axes_list: list[Axes] = [axes[0]]  # type: ignore[assignment]
        elif n_rows == 1:
            axes_list: list[Axes] = list(axes)  # type: ignore[assignment]
        else:
            axes_list: list[Axes] = [ax for ax in axes.flatten()]  # type: ignore[assignment]

        for idx, col in enumerate(categorical_cols[:n_cols]):
            ax: Axes = axes_list[idx]
            top_values = self.df[col].value_counts().head(10)
            top_values.plot(kind='bar', ax=ax, color='steelblue', edgecolor='black')
            ax.set_title(f'Top Values in {col}', fontsize=12, fontweight='bold')
            ax.set_xlabel(col)
            ax.set_ylabel('Count')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3, axis='y')

        # Hide empty subplots
        for idx in range(n_cols, len(axes_list)):
            axes_list[idx].set_visible(False)

        plt.tight_layout()
        filename = f"{self.dataset_name}_bar_charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = PLOTS_DIR / filename
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()

        self.plots['bar_charts'] = {
            'title': 'Top Values by Category',
            'file': filename,
            'path': str(filepath),
            'cols': categorical_cols[:n_cols]
        }

    def _generate_time_series(self, date_col: str, value_col: str):
        """Generate time series trend plot."""
        try:
            df_sorted = self.df.copy()
            df_sorted[date_col] = pd.to_datetime(df_sorted[date_col])
            df_sorted = df_sorted.sort_values(date_col)

            _, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df_sorted[date_col], df_sorted[value_col], marker='o', linewidth=2, markersize=6)
            ax.set_title(f'{value_col} Over Time', fontsize=14, fontweight='bold')
            ax.set_xlabel(date_col)
            ax.set_ylabel(value_col)
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()

            filename = f"{self.dataset_name}_timeseries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = PLOTS_DIR / filename
            plt.savefig(filepath, dpi=100, bbox_inches='tight')
            plt.close()

            self.plots['time_series'] = {
                'title': 'Time Series Trend',
                'file': filename,
                'path': str(filepath),
                'date_col': date_col,
                'value_col': value_col
            }
        except Exception as e:
            logger.warning(f"Failed to generate time series plot: {e}")

    def _generate_box_plots(self, numeric_cols: list[str]):
        """Generate box plots for columns with outliers."""
        n_cols = len(numeric_cols)
        n_rows = (n_cols + 1) // 2

        _, axes = plt.subplots(n_rows, 2, figsize=(10, 4*n_rows))
        if n_rows == 1 and n_cols == 1:
            axes_list: list[Axes] = [axes[0]]  # type: ignore[assignment]
        elif n_rows == 1:
            axes_list: list[Axes] = list(axes)  # type: ignore[assignment]
        else:
            axes_list: list[Axes] = [ax for ax in axes.flatten()]  # type: ignore[assignment]

        for idx, col in enumerate(numeric_cols):
            ax: Axes = axes_list[idx]
            ax.boxplot(self.df[col].dropna(), vert=True)
            ax.set_title(f'Box Plot: {col}', fontsize=12, fontweight='bold')
            ax.set_ylabel(col)
            ax.grid(True, alpha=0.3)

        # Hide empty subplots
        for idx in range(len(numeric_cols), len(axes_list)):
            axes_list[idx].set_visible(False)

        plt.tight_layout()
        filename = f"{self.dataset_name}_boxplots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = PLOTS_DIR / filename
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()

        self.plots['box_plots'] = {
            'title': 'Box Plots (Outlier Detection)',
            'file': filename,
            'path': str(filepath),
            'cols': numeric_cols
        }

if __name__ == "__main__":
    print("Plot Utilities Module")
    print(f"Plots will be saved to: {PLOTS_DIR}")
