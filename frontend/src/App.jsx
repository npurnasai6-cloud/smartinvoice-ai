import { useState } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];

    if (selectedFile) {
  const allowedTypes = [
    "application/pdf",
    "image/jpeg",
    "image/png",
  ];

  if (!allowedTypes.includes(selectedFile.type)) {
    setFile(null);
    setMessage("❌ Please upload a PDF, JPG, or PNG file.");
    return;
  }
      setFile(selectedFile);
      setResult(null);
      setMessage("");
    }
  };

  const uploadInvoice = async () => {
    if (!file) {
      setMessage("Please select an invoice first.");
      return;
    }

    setLoading(true);
    setMessage("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
  const response = await fetch(
    "http://127.0.0.1:8000/upload-invoice",
  {
    method: "POST",
    body: formData,
  }
);

if (!response.ok) {
  throw new Error("Upload failed");
}

const data = await response.json();

if (!data.invoice_data) {
  throw new Error("Invoice could not be processed.");
}

      setResult(data);
      setMessage("Invoice analyzed successfully!");
    } catch (error) {
  if (error.message === "Invoice could not be processed.") {
    setMessage("❌ Unable to read the invoice. Please check the file.");
  } else {
    setMessage("❌ Unable to connect to the backend.");
  }
}
     finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">

      {/* Header */}
      <header className="header">
        <div>
          <h1>🧾 SmartInvoice AI</h1>
          <p>AI-Powered Invoice Verification System</p>
        </div>
      </header>

      <main className="main">

        {/* Upload Card */}
        <section className="upload-card">

          <h2>Upload Your Invoice</h2>

          <p>
            Upload a PDF invoice and let SmartInvoice AI
            analyze it automatically.
          </p>

          <div className="upload-area">

            <div className="upload-icon">
              📄
            </div>

            <input
              type="file"
              id="invoiceFile"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileChange}
            />

            <label htmlFor="invoiceFile">
              Choose Invoice
            </label>

            {file && (
              <p className="selected-file">
                📎 {file.name}
              </p>
            )}

            <button
              onClick={uploadInvoice}
              disabled={loading}
            >
              {loading
                ? "⏳ Analyzing..."
                : "🚀 Upload & Analyze"}
            </button>

          </div>

          {message && (
            <div className="message">
              {message}
            </div>
          )}

        </section>

        {/* Results */}
        {result && (

          <section className="results">

            <h2>📊 Invoice Analysis</h2>

            {/* Invoice Summary */}
            <div className="summary-grid">

              <div className="summary-card">
                <span>Invoice Number</span>
                <strong>
                  {result.invoice_data.invoice_number}
                </strong>
              </div>

              <div className="summary-card">
                <span>Vendor</span>
                <strong>
                  {result.invoice_data.vendor}
                </strong>
              </div>

              <div className="summary-card">
                <span>Subtotal</span>
                <strong>
                  ₹{result.invoice_data.subtotal?.toLocaleString("en-IN")}
                </strong>
              </div>

              <div className="summary-card">
                <span>Total Amount</span>
                <strong>
                  ₹{result.invoice_data.total?.toLocaleString("en-IN")}
                </strong>
              </div>

            </div>

            {/* Items */}
            <div className="panel">

              <h3>📦 Invoice Items</h3>

              <div className="table-wrapper">

                <table>

                  <thead>
                    <tr>
                      <th>Item</th>
                      <th>Quantity</th>
                      <th>Price</th>
                      <th>Amount</th>
                    </tr>
                  </thead>

                  <tbody>

                    {result.invoice_data.items?.map(
                      (item, index) => (

                        <tr key={index}>

                          <td>{item.item}</td>

                          <td>{item.quantity}</td>

                          <td>
                            ₹{item.price?.toLocaleString("en-IN")}
                          </td>

                          <td>
                            ₹{item.amount?.toLocaleString("en-IN")}
                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>

            </div>

            {/* Agents */}
            <div className="agents-grid">

              {/* Verification */}
              <div className="agent-card">

                <h3>🔍 Verification Agent</h3>

                <div
                  className={
                    result.verification.status === "VERIFIED"
                      ? "status success"
                      : "status error"
                  }
                >
                  {result.verification.status === "VERIFIED"
                    ? "✓ VERIFIED"
                    : "✕ ERROR"}
                </div>

                {result.verification.errors.length > 0 && (

                  <ul>

                    {result.verification.errors.map(
                      (error, index) => (
                        <li key={index}>{error}</li>
                      )
                    )}

                  </ul>

                )}

                {result.verification.errors.length === 0 && (
                  <p>
                    All invoice calculations passed verification.
                  </p>
                )}

              </div>

              {/* Suggestions */}
              <div className="agent-card">

                <h3>💡 Suggestion Agent</h3>

                <ul>

                  {result.suggestions.map(
                    (suggestion, index) => (
                      <li key={index}>
                        {suggestion}
                      </li>
                    )
                  )}

                </ul>

              </div>

              {/* Alert */}
              <div className="agent-card">

                <h3>🔔 Alert Agent</h3>

                <div
                  className={
                    result.alert.level === "NONE"
                      ? "status success"
                      : "status error"
                  }
                >
                  {result.alert.level}
                </div>

                <p>
                  {result.alert.message}
                </p>

                <strong>
                  {result.alert.action}
                </strong>

              </div>

            </div>

            {/* Approval */}
            <div className="approval-card">

              <h3>✅ Approval Agent</h3>

              <div className="approval-decision">
                {result.approval.decision}
              </div>

              <p>
                <strong>Reason:</strong>{" "}
                {result.approval.reason}
              </p>

              <p>
                <strong>Next Action:</strong>{" "}
                {result.approval.next_action}
              </p>

            </div>

          </section>

        )}

      </main>

      <footer>
        SmartInvoice AI • Intelligent Invoice Verification
      </footer>

    </div>
  );
}

export default App;