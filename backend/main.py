from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pypdf import PdfReader
import shutil
import re

app = FastAPI()

# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "https://smartinvoice-ai-1.onrender.com",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Folder for uploaded invoices
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# --------------------------------------------------
# AGENT 1: INVOICE READING AGENT
# --------------------------------------------------

def extract_invoice_data(text):

    invoice_data = {
        "invoice_number": None,
        "date": None,
        "vendor": None,
        "customer": None,
        "items": [],
        "subtotal": None,
        "gst": None,
        "total": None,
        "due_date": None,
    }

    # Basic invoice information
    basic_patterns = {
        "invoice_number": r"Invoice Number:\s*(.+)",
        "date": r"Date:\s*(.+)",
        "vendor": r"Vendor:\s*(.+)",
        "customer": r"Customer:\s*(.+)",
        "subtotal": r"Subtotal:\s*₹?([\d,]+)",
        "gst": r"GST.*?:\s*₹?([\d,]+)",
        "total": r"Total Amount:\s*₹?([\d,]+)",
        "due_date": r"Payment Due Date:\s*(.+)",
    }

    for field, pattern in basic_patterns.items():

        match = re.search(pattern, text)

        if match:
            value = match.group(1).strip()

            if field in ["subtotal", "gst", "total"]:
                value = value.replace(",", "")
                value = int(value)

            invoice_data[field] = value

    # --------------------------------------------------
    # Extract multiple invoice items
    # --------------------------------------------------

    item_pattern = re.compile(
        r"Item:\s*(.+?)\s*"
        r"Quantity:\s*(\d+)\s*"
        r"Price:\s*₹?([\d,]+)\s*each\s*"
        r"Amount:\s*₹?([\d,]+)",
        re.IGNORECASE
    )

    matches = item_pattern.finditer(text)

    for match in matches:

        item_name = match.group(1).strip()
        quantity = int(match.group(2))
        price = int(match.group(3).replace(",", ""))
        amount = int(match.group(4).replace(",", ""))

        item = {
            "item": item_name,
            "quantity": quantity,
            "price": price,
            "amount": amount
        }

        invoice_data["items"].append(item)

    return invoice_data


# --------------------------------------------------
# AGENT 2: VERIFICATION AGENT
# --------------------------------------------------

def verify_invoice(invoice_data):

    errors = []
    warnings = []

    subtotal = invoice_data["subtotal"]
    gst = invoice_data["gst"]
    total = invoice_data["total"]

    items = invoice_data["items"]

    # --------------------------------------------------
    # Check required fields
    # --------------------------------------------------

    required_fields = [
        "invoice_number",
        "date",
        "vendor",
        "customer",
        "subtotal",
        "gst",
        "total",
    ]

    for field in required_fields:

        if invoice_data.get(field) is None:
            errors.append(f"Missing field: {field}")

    # Check whether invoice contains items
    if len(items) == 0:

        errors.append("No invoice items could be detected.")

    # --------------------------------------------------
    # Verify each item
    # --------------------------------------------------

    calculated_subtotal = 0

    for item in items:

        expected_amount = item["quantity"] * item["price"]

        if expected_amount != item["amount"]:

            errors.append(
                f"Item amount mismatch for {item['item']}. "
                f"Expected ₹{expected_amount}, "
                f"but invoice shows ₹{item['amount']}."
            )

        calculated_subtotal += item["amount"]

    # --------------------------------------------------
    # Verify total subtotal
    # --------------------------------------------------

    if subtotal is not None and len(items) > 0:

        if calculated_subtotal != subtotal:

            errors.append(
                f"Subtotal mismatch. "
                f"Expected ₹{calculated_subtotal}, "
                f"but invoice shows ₹{subtotal}."
            )

    # --------------------------------------------------
    # Verify GST
    # --------------------------------------------------

    if subtotal is not None and gst is not None:

        expected_gst = subtotal * 0.18

        if abs(expected_gst - gst) > 0.01:

            errors.append(
                f"GST mismatch. "
                f"Expected ₹{expected_gst:.2f}, "
                f"but invoice shows ₹{gst}."
            )

    # --------------------------------------------------
    # Verify total
    # --------------------------------------------------

    if subtotal is not None and gst is not None and total is not None:

        expected_total = subtotal + gst

        if expected_total != total:

            errors.append(
                f"Total mismatch. "
                f"Expected ₹{expected_total}, "
                f"but invoice shows ₹{total}."
            )

    # --------------------------------------------------
    # Final verification status
    # --------------------------------------------------

    if len(errors) == 0:

        status = "VERIFIED"

    else:

        status = "ERROR"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings
    }


# --------------------------------------------------
# AGENT 3: SUGGESTION AGENT
# --------------------------------------------------

def generate_suggestions(verification_result):

    suggestions = []

    if verification_result["status"] == "VERIFIED":

        suggestions.append(
            "Invoice passed all verification checks. "
            "It can proceed to the next stage."
        )

    else:

        for error in verification_result["errors"]:

            if "Item amount mismatch" in error:

                suggestions.append(
                    "Check the quantity and unit price of the "
                    "affected item with the vendor."
                )

            elif "Subtotal mismatch" in error:

                suggestions.append(
                    "Check all line-item amounts and correct "
                    "the invoice subtotal."
                )

            elif "GST mismatch" in error:

                suggestions.append(
                    "Verify the GST percentage and GST amount "
                    "with the vendor."
                )

            elif "Total mismatch" in error:

                suggestions.append(
                    "Verify the subtotal and GST before approving "
                    "the invoice payment."
                )

            elif "Missing field" in error:

                suggestions.append(
                    "Request the missing invoice information "
                    "from the vendor."
                )

            elif "No invoice items" in error:

                suggestions.append(
                    "Review the invoice manually because "
                    "no line items could be detected."
                )

            else:

                suggestions.append(
                    "Review the invoice manually before approval."
                )

    return suggestions
# --------------------------------------------------
# AGENT 4: ALERT AGENT
# --------------------------------------------------

def generate_alert(verification_result):

    if verification_result["status"] == "VERIFIED":

        return {
            "level": "NONE",
            "message": "Invoice verified successfully.",
            "action": "No action required."
        }

    errors = verification_result["errors"]

    # Critical issues
    critical_keywords = [
        "Total mismatch",
        "Subtotal mismatch",
        "GST mismatch",
        "Item amount mismatch"
    ]

    is_critical = any(
        any(keyword in error for keyword in critical_keywords)
        for error in errors
    )

    if is_critical:

        return {
            "level": "CRITICAL",
            "message": "Invoice requires immediate attention.",
            "action": "DO NOT APPROVE PAYMENT until the invoice is verified."
        }

    return {
        "level": "WARNING",
        "message": "Invoice contains issues that require review.",
        "action": "Review the invoice before approval."
    }
# --------------------------------------------------
# AGENT 5: APPROVAL AGENT
# --------------------------------------------------

def generate_approval(verification_result, alert):

    if verification_result["status"] == "VERIFIED":

        return {
            "decision": "APPROVED",
            "reason": "Invoice passed all verification checks.",
            "next_action": "Invoice can proceed for payment."
        }

    else:

        return {
            "decision": "MANUAL_REVIEW",
            "reason": "Invoice contains verification errors.",
            "next_action": "Do not approve payment until the issues are resolved."
        }
# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "SmartInvoice AI Backend is running!"
    }


# --------------------------------------------------
# UPLOAD INVOICE
# --------------------------------------------------

@app.post("/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)):

    # Save invoice
    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:

        shutil.copyfileobj(file.file, buffer)

    # Read PDF
    reader = PdfReader(str(file_path))

    extracted_text = ""

    for page in reader.pages:

        text = page.extract_text()

        if text:

            extracted_text += text + "\n"

    # Agent 1: Extract invoice information
    invoice_data = extract_invoice_data(extracted_text)

    # Agent 2: Verify invoice
    verification_result = verify_invoice(invoice_data)

    # Agent 3: Generate suggestions
    suggestions = generate_suggestions(verification_result)

    alert = generate_alert(verification_result)

    approval = generate_approval(
    verification_result,
    alert
)

    return {
        "message": "Invoice processed successfully!",
        "filename": file.filename,
        "invoice_data": invoice_data,
        "verification": verification_result,
        "suggestions": suggestions,
        "alert": alert,
        "approval": approval
    }