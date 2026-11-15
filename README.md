# Supply Chain – Analytics & Performance Application

## Project Overview

Supply Chain is an end-to-end supply chain analytics application built using Azure Blob Storage and Databricks.

The project ingests supply chain data, processes it through the Medallion Architecture (Bronze, Silver, Gold), performs data quality validations, quarantines invalid records, and generates business-ready analytics.

The application provides an interactive dashboard for monitoring supply chain performance and operational metrics. It also allows users to trigger and monitor the Databricks data pipeline.

## Architecture

Azure Blob Storage → Databricks Notebooks → Bronze → Silver → Quarantine → Gold → Supply Chain 360 App

## Technologies Used

- **Azure Blob Storage** – Raw CSV data storage
- **Databricks Free Edition** – Data engineering and processing
- **PySpark** – Data transformation and validation
- **Delta Lake** – Storage for Bronze, Silver, Quarantine, and Gold tables
- **Databricks Workflows** – Pipeline orchestration
- **Streamlit** – Interactive application and dashboard
- **Python** – Application development
- **Plotly** – Interactive visualizations
- **GitHub** – Source code management

## Source Datasets

The project uses four supply chain datasets:

- Suppliers
- Products
- Shipments
- Shipment Events

## Data Engineering Pipeline

### 1. Bronze Layer
- Ingest raw CSV files from Azure Blob Storage.
- Load data into Delta tables.
- Capture ingestion timestamps and source file details.

### 2. Silver Layer
- Clean and standardize data.
- Remove duplicate records.
- Validate supplier, product, shipment, and event references.
- Identify invalid dates, quantities, prices, and shipment totals.
- Separate invalid records into quarantine tables.

### 3. Gold Layer
Create business-ready analytical tables:

- `gold_supplier_performance`
- `gold_shipment_analytics`
- `gold_product_analytics`
- `gold_delivery_performance`
- `gold_inventory_reorder`
- `gold_monthly_supply_chain`

## Application Features

The Supply Chain 360 application is designed to provide:

### Executive Overview
- Total shipments and shipment value
- Supplier and product performance
- Shipment status distribution
- Monthly shipment trends
- On-time delivery performance

### Operational Analysis
- Supplier-wise shipment analysis
- Product and category analysis
- Delivery performance by transport mode
- Shipment-level details and filters
- Inventory reorder analysis

### Pipeline Monitoring
- Trigger the Databricks pipeline from the application.
- View the pipeline run ID.
- Monitor job execution status.
- Refresh analytical data after pipeline execution.

## Repository Structure

```text
supply-chain/
│
├── app.py
├── requirements.txt
├── app.yaml
└── README.md
```

## Deployment

The application is intended to be deployed using Databricks Apps.

1. Connect this GitHub repository to Databricks Apps.
2. Configure the required Databricks Job and SQL Warehouse resources.
3. Configure the application permissions to access the Gold tables.
4. Deploy the application.
5. Open the deployed application to explore analytics and monitor pipeline execution.

## Security

- Do not store passwords, personal access tokens, or SAS tokens in source code.
- Use Databricks App resources and supported authentication mechanisms.
- Grant only the permissions required by the application.

## Project Goal

To build an end-to-end supply chain analytics solution that combines cloud data ingestion, data engineering, data quality management, pipeline orchestration, and interactive business intelligence in one application.
