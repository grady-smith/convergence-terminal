# Architecture

This document outlines the core system modules by technical function.

## Ingestion
The Ingestion module is responsible for pulling in raw data from various sources (e.g. APIs, feeds) and staging it for processing.

## Synthesis & Filtering
This module takes the raw data from the ingestion pipeline, applies the Alden Standard rules, and synthesizes it into actionable signals while filtering out noise.

## SQLite & Export Engine
Handles the storage of synthesized data in a structured format (SQLite database) and provides mechanisms to export this data into static files (e.g. JSON) for the frontend.

## Static Frontend
A static web application that reads the exported JSON data and presents the dashboard/terminal UI to the user.

## Budget/Cost Ledger
Tracks API usage and operational costs to ensure the system operates within its defined budget.
