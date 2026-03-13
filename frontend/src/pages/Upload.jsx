import { useId, useState } from "react";
import api from "../api/client";
import IngestionSummaryCard from "../components/IngestionSummaryCard";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [summary, setSummary] = useState(null);
  const inputId = useId();

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      return;
    }

    setError("");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await api.post("/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setMessage(`Saved ${response.data.title}`);
      setSummary(response.data.ingestion_summary || null);
      setFile(null);
      event.target.reset();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to upload file.");
    }
  };

  return (
    <div className="stack">
      <div className="card">
        <h2>Upload PDF or TXT</h2>
        <form onSubmit={handleSubmit} className="stack">
          <div className="upload-picker-shell">
            <input
              id={inputId}
              className="upload-picker-input"
              type="file"
              accept=".pdf,.txt"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
            <label htmlFor={inputId} className="upload-picker-label">
              <span className="upload-picker-button">Choose File</span>
              <span className={`upload-picker-name ${file ? "has-file" : ""}`}>
                {file ? file.name : "Drop a PDF or TXT here, or browse from your device"}
              </span>
            </label>
            <p className="source-meta upload-picker-meta">Supported formats: PDF, TXT</p>
          </div>
          <button type="submit">Upload File</button>
        </form>
        {error && <p className="error-text">{error}</p>}
        {message && <p className="success-text">{message}</p>}
      </div>

      <IngestionSummaryCard summary={summary} title="Upload Processed" />
    </div>
  );
}
