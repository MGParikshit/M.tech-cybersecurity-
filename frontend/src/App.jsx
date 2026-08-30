import { useState } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];

    setResult(null);
    setError("");

    if (!selectedFile) {
      setFile(null);
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith(".exe")) {
      setError("Please select a .exe file.");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  const analyzeFile = async () => {
    if (!file) {
      setError("Please select an EXE file first.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      // Read EXE bytes
      const buffer = await file.arrayBuffer();
      const bytes = new Uint8Array(buffer);

      // Create exactly 1024 pixel values
      // by taking the first 1024 bytes.
      const pixels = new Array(1024).fill(0);

      for (let i = 0; i < Math.min(bytes.length, 1024); i++) {
        pixels[i] = bytes[i];
      }

      // Send file + pixels to FastAPI
      const formData = new FormData();

      formData.append("file", file);
      formData.append("pixels", JSON.stringify(pixels));

      const response = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Analysis failed.");
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Unable to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setResult(null);
    setError("");
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Malware Analysis</h1>
          <p>AI-Powered PE Malware Detection</p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          Backend Connected
        </div>
      </header>

      <main className="container">
        <section className="hero">
          <div className="hero-icon">🛡️</div>
          <h2>Malware Detection System</h2>
          <p>
            Upload a Windows executable file and analyze it using the
            trained CNN malware detection model.
          </p>
        </section>

        <section className="upload-card">
          <h3>Upload Executable</h3>

          <label className="drop-zone">
            <input
              type="file"
              accept=".exe"
              onChange={handleFileChange}
            />

            <div className="upload-icon">📁</div>

            {file ? (
              <>
                <strong>{file.name}</strong>
                <span>
                  {(file.size / 1024).toFixed(2)} KB
                </span>
              </>
            ) : (
              <>
                <strong>Choose an EXE file</strong>
                <span>Only Windows .exe files are supported</span>
              </>
            )}
          </label>

          {error && <div className="error">{error}</div>}

          <div className="buttons">
            <button
              className="analyze-btn"
              onClick={analyzeFile}
              disabled={!file || loading}
            >
              {loading ? "Analyzing..." : "Analyze File"}
            </button>

            <button className="reset-btn" onClick={reset}>
              Reset
            </button>
          </div>
        </section>

        {result && (
          <section className="result-card">
            <h3>Analysis Result</h3>

            <div
              className={`prediction ${
                result.prediction === "Malware"
                  ? "malware"
                  : "benign"
              }`}
            >
              <div className="result-icon">
                {result.prediction === "Malware" ? "⚠️" : "✓"}
              </div>

              <div>
                <span>Prediction</span>
                <strong>{result.prediction}</strong>
              </div>
            </div>

            <div className="details">
              <div className="detail">
                <span>Filename</span>
                <strong>{result.filename}</strong>
              </div>

              <div className="detail">
                <span>File Size</span>
                <strong>
                  {(result.file_size / 1024).toFixed(2)} KB
                </strong>
              </div>

              <div className="detail">
                <span>Probability</span>
                <strong>
                  {(result.probability * 100).toFixed(2)}%
                </strong>
              </div>

              <div className="detail">
                <span>Confidence</span>
                <strong>
                  {(result.confidence * 100).toFixed(2)}%
                </strong>
              </div>
            </div>

            <div className="hash">
              <span>MD5</span>
              <code>{result.md5}</code>
            </div>

            <div className="hash">
              <span>SHA-256</span>
              <code>{result.sha256}</code>
            </div>
          </section>
        )}
      </main>

      <footer>
        M.Tech Cyber Security • CNN-Based Malware Detection
      </footer>
    </div>
  );
}

export default App;
