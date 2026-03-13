import { useId, useState } from "react";
import api from "../api/client";
import IngestionSummaryCard from "../components/IngestionSummaryCard";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [summary, setSummary] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStage, setUploadStage] = useState("idle");
  const inputId = useId();

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file || isUploading) {
      return;
    }

    setError("");
    setMessage("");
    setSummary(null);
    setIsUploading(true);
    setUploadProgress(0);
    setUploadStage("uploading");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await api.post("/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          if (!progressEvent.total) {
            return;
          }
          const percent = Math.min(95, Math.round((progressEvent.loaded / progressEvent.total) * 100));
          setUploadProgress(percent);
          setUploadStage("uploading");
        }
      });
      setUploadStage("processing");
      setUploadProgress(100);
      setMessage(`Saved ${response.data.title}`);
      setSummary(response.data.ingestion_summary || null);
      setFile(null);
      event.target.reset();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to upload file.");
      setUploadStage("idle");
      setUploadProgress(0);
    } finally {
      setIsUploading(false);
    }
  };

  const progressLabel = uploadStage === "processing"
    ? "Processing document and updating your graph..."
    : `Uploading ${uploadProgress}%`;

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
            <label htmlFor={inputId} className={`upload-picker-label ${isUploading ? "disabled" : ""}`}>
              <span className="upload-picker-button">Choose File</span>
              <span className={`upload-picker-name ${file ? "has-file" : ""}`}>
                {file ? file.name : "Drop a PDF or TXT here, or browse from your device"}
              </span>
            </label>
            <p className="source-meta upload-picker-meta">Supported formats: PDF, TXT</p>
          </div>

          {isUploading && (
            <div className="upload-progress-card">
              <div className="row-between upload-progress-header">
                <strong>{progressLabel}</strong>
                <span className="source-meta">{uploadProgress}%</span>
              </div>
              <div className="upload-progress-track">
                <div className="upload-progress-fill" style={{ width: `${uploadProgress}%` }} />
              </div>
            </div>
          )}

          <button type="submit" disabled={!file || isUploading}>
            {isUploading ? (uploadStage === "processing" ? "Processing..." : "Uploading...") : "Upload File"}
          </button>
        </form>
        {error && <p className="error-text">{error}</p>}
        {message && <p className="success-text">{message}</p>}
      </div>

      <IngestionSummaryCard summary={summary} title="Upload Processed" />
    </div>
  );
}
