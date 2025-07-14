import React, { useState } from "react";
import axios from "axios";
import "./index.css";

function App() {
  const [url, setUrl] = useState("");
  const [query, setQuery] = useState("");
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const handleScrape = async () => {
    try {
      setLoading(true);
      const res = await axios.post("http://localhost:8000/scrape", { url });
      setResponse(res.data.message || res.data.error);
    } catch (err) {
      setResponse("Scrape error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!file) return alert("Please select a file.");
    const formData = new FormData();
    formData.append("file", file);
    try {
      setLoading(true);
      const res = await axios.post("http://localhost:8000/upload", formData);
      setResponse(res.data.message || res.data.error);
    } catch (err) {
      setResponse("Upload error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleQuery = async () => {
    try {
      setLoading(true);
      const res = await axios.post("http://localhost:8000/query", { query });
      setResponse(res.data.answer || res.data.error);
    } catch (err) {
      setResponse("Query error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1 className="app-title">Q/A Assistant</h1>

      <div className="card">
        <h2>Scrape URL</h2>
        <input
          type="text"
          placeholder="Enter URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button onClick={handleScrape}>Scrape</button>
      </div>

      <div className="card">
        <h2>Upload PDF / CSV / JSON</h2>
        <input
          type="file"
          accept=".pdf,.csv,.json"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button onClick={handleFileUpload}>Upload & Embed</button>
      </div>

      <div className="card">
        <h2>Ask a Question</h2>
        <input
          type="text"
          placeholder="Enter your question"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button onClick={handleQuery}>Ask</button>
      </div>

      <div className="response-box">
        {loading ? <p>Loading...</p> : <pre>{response}</pre>}
      </div>
    </div>
  );
}

export default App;
