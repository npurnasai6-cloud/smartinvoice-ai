# 🧾 SmartInvoice AI – Multi-Agent Invoice Verification System

SmartInvoice AI is a full-stack invoice verification system that automates invoice processing, data extraction, validation, error detection, and approval recommendations.

The system allows users to upload PDF invoices and automatically analyzes important invoice information such as invoice number, vendor, items, quantity, price, subtotal, GST, and total amount.

---

## 🚀 Project Overview

Manual invoice verification is time-consuming and can lead to calculation and data-entry errors, especially when organizations process a large number of invoices.

SmartInvoice AI addresses this problem by providing an automated invoice verification workflow.

The system extracts information from PDF invoices, validates the extracted data, identifies errors, generates suggestions and alerts, and provides a final approval recommendation.

### Main Workflow

```text
PDF Invoice
     ↓
React.js Frontend
     ↓
FastAPI Backend
     ↓
PyPDF Text Extraction
     ↓
Regex Data Extraction
     ↓
Invoice Reading Agent
     ↓
Verification Agent
     ↓
Suggestion Agent
     ↓
Alert Agent
     ↓
Approval Agent
     ↓
APPROVED / MANUAL_REVIEW
