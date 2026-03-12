import { useState } from "react";
import api from "../api/client";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      return;
    }
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" }
    });
    setMessage(`Saved ${response.data.title}`);
    setFile(null);
    event.target.reset();
  };

  return (
    <div className="card">
      <h2>Upload PDF or TXT</h2>
      <form onSubmit={handleSubmit} className="stack">
        <input type="file" accept=".pdf,.txt" onChange={(event) => setFile(event.target.files?.[0] || null)} />
        <button type="submit">Upload File</button>
      </form>
      {message && <p className="success-text">{message}</p>}
    </div>
  );
}
