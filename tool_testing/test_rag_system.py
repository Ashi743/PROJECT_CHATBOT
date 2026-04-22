#!/usr/bin/env python3
"""
Test suite for RAG CSV/Excel Analysis System
Tests both ingestion and analysis tools separately
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, "..")

import pandas as pd
from tools.csv_ingest_tool import ingest_file, list_datasets, get_dataset_info, search_dataset, delete_dataset
from tools.csv_analysis_tool import analyze_data

class RAGSystemTester:
    """Test RAG system with sample data"""

    def __init__(self):
        self.test_results = []
        self.test_data_path = Path("test_sample_sales.csv")

    def create_sample_data(self):
        """Create sample CSV for testing"""
        print("\n" + "="*60)
        print("Creating Sample Data")
        print("="*60)

        # Create diverse sample data
        data = {
            'Date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'] * 4,
            'Region': ['North', 'South', 'East', 'West', 'Central'] * 4,
            'Product': ['Widget', 'Gadget', 'Doohickey', 'Thingamajig', 'Whatsit'] * 4,
            'Sales': [1000, 1500, 1200, 800, 1100, 950, 1600, 1300, 1400, 900,
                      1050, 1550, 1250, 850, 1150, 1000, 1500, 1200, 800, 1100],
            'Quantity': [10, 15, 12, 8, 11, 9, 16, 13, 14, 9,
                         10, 15, 12, 8, 11, 10, 15, 12, 8, 11],
            'Quarter': ['Q1', 'Q1', 'Q1', 'Q1', 'Q1'] * 4
        }

        df = pd.DataFrame(data)
        csv_path = Path(__file__).parent.parent / "data" / "uploads" / self.test_data_path.name
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(csv_path, index=False)
        print(f"✓ Created sample data: {csv_path}")
        print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
        return df

    def test_ingestion(self):
        """Test ingestion tool"""
        print("\n" + "="*60)
        print("Test 1: CSV Ingestion")
        print("="*60)

        df = self.create_sample_data()

        # Test file ingestion
        csv_path = Path(__file__).parent.parent / "data" / "uploads" / self.test_data_path.name
        with open(csv_path, 'rb') as f:
            file_bytes = f.read()

        result = ingest_file(
            file_bytes=file_bytes,
            file_name=self.test_data_path.name,
            dataset_name="sales_data",
            user_description="Q1 2024 Sales Data by Region"
        )

        print(f"\nIngestion Result:")
        print(f"  Status: {result['status']}")
        print(f"  Message: {result['message']}")
        print(f"  Rows: {result.get('rows')}")
        print(f"  Columns: {result.get('columns')}")
        print(f"  Chunks Created: {result.get('chunks_created')}")
        print(f"  Numeric Columns: {result.get('numeric_columns')}")
        print(f"  Categorical Columns: {result.get('categorical_columns')}")

        if result['status'] == 'ok':
            self.test_results.append(("Ingestion", "PASS"))
            return True
        else:
            self.test_results.append(("Ingestion", "FAIL"))
            return False

    def test_dataset_info(self):
        """Test getting dataset info"""
        print("\n" + "="*60)
        print("Test 2: Dataset Metadata")
        print("="*60)

        info = get_dataset_info("sales_data")

        if "error" in info:
            print(f"Error: {info['error']}")
            self.test_results.append(("Dataset Info", "FAIL"))
            return False

        print(f"\nDataset Information:")
        print(f"  Name: {info.get('dataset_name')}")
        print(f"  Rows: {info.get('rows')}")
        print(f"  Columns: {info.get('columns')}")
        print(f"  Numeric: {info.get('numeric_columns')}")
        print(f"  Categorical: {info.get('categorical_columns')}")
        print(f"  Description: {info.get('user_description')}")
        print(f"  Ingested: {info.get('ingested_at')}")

        self.test_results.append(("Dataset Info", "PASS"))
        return True

    def test_analysis_operations(self):
        """Test analysis tool operations"""
        print("\n" + "="*60)
        print("Test 3: Analysis Operations")
        print("="*60)

        operations = [
            ("shape", "", "Dataset shape"),
            ("describe", "", "Statistical summary"),
            ("columns", "", "Column list"),
            ("head", "5", "First 5 rows"),
            ("groupby_sum", "Region,Sales", "Sum by region"),
            ("value_counts", "Region", "Region distribution"),
        ]

        for op, params, desc in operations:
            print(f"\n  {desc} ({op})...")
            result = analyze_data("sales_data", op, params)

            if result and not result.startswith("Error"):
                print(f"  ✓ Success")
                self.test_results.append((f"Analysis: {op}", "PASS"))
            else:
                print(f"  ✗ Failed: {result}")
                self.test_results.append((f"Analysis: {op}", "FAIL"))

    def test_rag_search(self):
        """Test RAG semantic search"""
        print("\n" + "="*60)
        print("Test 4: RAG Semantic Search")
        print("="*60)

        query = "high performing regions"
        print(f"\nSearching for: '{query}'")

        result = analyze_data("sales_data", "rag_search", query)

        if result and not result.startswith("Error"):
            print(f"✓ Search returned results")
            print(f"\nFirst 200 chars of result:")
            print(result[:200] + "...")
            self.test_results.append(("RAG Search", "PASS"))
        else:
            print(f"✗ Search failed: {result}")
            self.test_results.append(("RAG Search", "FAIL"))

    def test_list_datasets(self):
        """Test listing datasets"""
        print("\n" + "="*60)
        print("Test 5: List Datasets")
        print("="*60)

        datasets = list_datasets()
        print(f"\nAvailable datasets: {datasets}")

        if "sales_data" in datasets:
            print("✓ sales_data found")
            self.test_results.append(("List Datasets", "PASS"))
        else:
            print("✗ sales_data not found")
            self.test_results.append(("List Datasets", "FAIL"))

    def cleanup(self):
        """Clean up test data"""
        print("\n" + "="*60)
        print("Cleanup")
        print("="*60)

        result = delete_dataset("sales_data")
        print(f"\nDelete result: {result['message']}")

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*70)
        print(" RAG CSV/Excel Analysis System - Test Suite")
        print("="*70)

        try:
            self.test_ingestion()
            self.test_dataset_info()
            self.test_list_datasets()
            self.test_analysis_operations()
            self.test_rag_search()

            print("\n" + "="*60)
            print("Test Summary")
            print("="*60)

            for test_name, result in self.test_results:
                status_icon = "✓" if result == "PASS" else "✗"
                print(f"  {status_icon} {test_name}: {result}")

            passed = sum(1 for _, r in self.test_results if r == "PASS")
            total = len(self.test_results)
            print(f"\nResult: {passed}/{total} tests passed")

        finally:
            self.cleanup()

if __name__ == "__main__":
    tester = RAGSystemTester()
    tester.run_all_tests()
