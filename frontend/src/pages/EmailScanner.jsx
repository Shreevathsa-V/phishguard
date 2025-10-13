import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function EmailScanner() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const getAuthHeaders = () => {
    const token = localStorage.getItem("access_token");
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  };

  const scanEmails = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/emails/scan`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          max_messages: 20,
          query: "in:inbox newer_than:30d",
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else if (res.status === 401) {
        localStorage.removeItem("access_token");
        setError("⚠️ Session expired. Please log in again.");
      } else {
        const errData = await res.json();
        setError(errData.detail || "Scan failed");
      }
    } catch (err) {
      console.error("Error scanning emails:", err);
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-xl font-bold mb-4">📧 Gmail Scanner</h1>
      <button
        onClick={scanEmails}
        disabled={loading}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Scanning..." : "Scan Emails"}
      </button>

      {error && (
        <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {result && !error && (
        <div className="mt-4 bg-gray-100 p-4 rounded">
          <p>✅ Scanned: {result.scanned}</p>
          <p>📦 Stored: {result.stored ?? result.emails?.length ?? 0}</p>
        </div>
      )}
    </div>
  );
}
