import { useState, useEffect } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
// Correct Lucide import. We use AlertTriangle throughout for consistency.
import { AlertTriangle, Mail, Shield, Zap, RefreshCw } from 'lucide-react'; 

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// This is a simple string and should NOT be the source of the error, 
// but we keep it here as intended for styling.
const IconStyle = "h-5 w-5 mr-3";

export default function Dashboard() {
  const { user, setUser } = useOutletContext();
  const navigate = useNavigate();
  
  const [text, setText] = useState("");
  const [qcScore, setQcScore] = useState(null);
  const [qcLabel, setQcLabel] = useState(null);
  const [emails, setEmails] = useState([]);
  const [stats, setStats] = useState({ scanned: 0, phishing: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) {
      navigate("/login");
    } else {
      loadRecentEmails();
      loadOverallStats();
    }
  }, [user, navigate]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem("access_token");
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  };

  const handleApiError = (response) => {
    if (response.status === 401) {
      localStorage.removeItem("access_token");
      if (setUser) setUser(null); 
      navigate("/login");
      throw new Error("Session expired. Please log in again.");
    }
  };

  const loadOverallStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/emails/stats`, {
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        const statsData = await response.json();
        setStats({
          scanned: statsData.total_scanned,
          phishing: statsData.total_phishing,
        });
      } else {
        handleApiError(response);
      }
    } catch (error) {
      console.error("Failed to load overall stats:", error);
    }
  };

  const loadRecentEmails = async () => {
    try {
      const response = await fetch(`${API_BASE}/emails/latest?limit=20`, {
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        const emailsData = await response.json();
        setEmails(Array.isArray(emailsData) ? emailsData : []);
      } else {
        handleApiError(response);
      }
    } catch (error) {
      console.error("Failed to load emails:", error);
      setError(error.message);
    }
  };

  const analyze = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ text }),
      });

      if (response.ok) {
        const data = await response.json();
        setQcScore(Number(data.score ?? 0));
        setQcLabel(Number(data.label ?? 0));
      } else {
        handleApiError(response);
      }
    } catch (error) {
      console.error("Prediction failed:", error);
      setError(error.message || "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  const scanGmail = async () => {
    if (!user?.gmail_connected) {
      alert("Please connect your Gmail account first.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/emails/scan`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          max_messages: 20,
          query: "in:inbox",
        }),
      });

      if (response.ok) {
        const scanResult = await response.json();
        loadOverallStats(); 
        await loadRecentEmails();
        alert(
          `✅ Scan completed!\n📧 Scanned: ${scanResult.scanned}\n🚨 Phishing detected: ${scanResult.phishing_detected}`
        );
      } else {
        handleApiError(response);
      }
    } catch (error) {
      console.error("Gmail scan failed:", error);
      setError(error.message || "Gmail scan failed");
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="grid gap-8">
      {/* --- Error Alert --- */}
      {error && (
        <div className="flex items-center bg-red-50 border-l-4 border-red-500 text-red-800 p-4 rounded-lg shadow-sm">
          <AlertTriangle className="h-5 w-5 mr-3 flex-shrink-0" />
          <p className="flex-grow">{error}</p>
          <button
            onClick={() => setError("")}
            className="ml-4 text-red-500 hover:text-red-700 font-bold"
          >
            &times;
          </button>
        </div>
      )}

      {/* --- Stats Cards (Enhanced Styling) --- */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6 flex items-center justify-between transition hover:shadow-xl">
          <div>
            <div className="text-sm font-medium text-gray-500">Emails Scanned (Total)</div>
            <div className="text-4xl font-extrabold text-gray-900 mt-1">{stats.scanned}</div>
          </div>
          <Mail className="h-10 w-10 text-blue-500 opacity-30" />
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 flex items-center justify-between transition hover:shadow-xl">
          <div>
            <div className="text-sm font-medium text-gray-500">Phishing Detected (Total)</div>
            <div className="text-4xl font-extrabold text-red-600 mt-1">{stats.phishing}</div>
          </div>
          <AlertTriangle className="h-10 w-10 text-red-500 opacity-30" />
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 flex items-center justify-between transition hover:shadow-xl">
          <div>
            <div className="text-sm font-medium text-gray-500">Gmail Status</div>
            <div
              className={`text-base font-bold mt-2 flex items-center ${
                user.gmail_connected ? "text-green-600" : "text-orange-600"
              }`}
            >
              <Shield className={`h-5 w-5 mr-2 ${user.gmail_connected ? "text-green-500" : "text-orange-500"}`} />
              {user.gmail_connected ? "Connected" : "Not Connected"}
            </div>
          </div>
          <Zap className="h-10 w-10 text-green-500 opacity-30" />
        </div>
      </section>

      {/* --- Quick Check Section --- */}
      <section className="bg-white rounded-xl shadow-lg p-6 border-t-4 border-blue-500">
        <h2 className="font-bold text-xl text-gray-800 mb-4 flex items-center">
          {/* Usage is correct: component followed by text */}
          <Zap className={IconStyle} /> Quick Check Analyzer
        </h2>
        <form onSubmit={analyze} className="space-y-4">
          <textarea
            className="w-full border border-gray-300 rounded-lg p-4 h-40 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition shadow-inner"
            placeholder="Paste the suspicious email body or snippet here to analyze for phishing..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <button
              type="submit"
              className="flex items-center px-6 py-2 rounded-full bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50 transition shadow-md"
              disabled={loading || !text.trim()}
            >
              {loading ? "Analyzing..." : "Analyze Text"}
            </button>
            
            {qcScore !== null && (
              <div
                className={`px-4 py-2 rounded-full font-bold text-sm shadow-md flex items-center ${
                  qcLabel
                    ? "bg-red-50 text-red-700 border border-red-300"
                    : "bg-green-50 text-green-700 border border-green-300"
                }`}
              >
                {qcLabel ? (
                  <>
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    <span className="text-red-900">PHISHING RISK</span>
                  </>
                ) : (
                  <>
                    <Shield className="h-4 w-4 mr-2" />
                    <span className="text-green-900">SAFE</span>
                  </>
                )}
                <span className="ml-3 text-gray-600 font-normal">Score: {qcScore.toFixed(4)}</span>
              </div>
            )}
          </div>
        </form>
      </section>

      {/* --- Recent Emails Section --- */}
      <section className="bg-white rounded-xl shadow-lg p-6 border-t-4 border-green-500">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6">
          <h2 className="font-bold text-xl text-gray-800 flex items-center mb-3 sm:mb-0">
            {/* Usage is correct: component followed by text */}
            <Mail className={IconStyle} /> Recent Gmail Scan History
          </h2>
          <button
            className="flex items-center px-5 py-2 rounded-full bg-green-600 text-white font-semibold hover:bg-green-700 disabled:opacity-50 transition shadow-md"
            onClick={scanGmail}
            disabled={loading || !user.gmail_connected}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            {loading ? "Scanning..." : "Scan Gmail"}
          </button>
        </div>

        {!user.gmail_connected && (
          <div className="mb-4 p-4 bg-yellow-50 border border-yellow-300 text-yellow-800 rounded-lg flex items-center shadow-sm">
            <AlertTriangle className="h-5 w-5 mr-3 flex-shrink-0" />
            Please **Connect your Gmail account** via the header button to enable email scanning.
          </div>
        )}

        <div className="space-y-4">
          {emails.length > 0 ? (
            emails.map((email) => (
              <div key={email.id} className="border border-gray-200 rounded-lg p-4 transition hover:shadow-md hover:border-blue-300 flex justify-between items-start bg-gray-50">
                <div className="flex-1 min-w-0 pr-4">
                  <div className="font-semibold text-base text-gray-900 truncate">
                    {email.subject || "(No Subject)"}
                  </div>
                  <div className="text-sm text-gray-600 mt-1 font-medium">{email.sender}</div>
                  <div className="text-sm text-gray-500 mt-2 line-clamp-2 italic">
                    {email.snippet}
                  </div>
                  <div className="text-xs text-gray-400 mt-3">
                    Scanned: {new Date(email.created_at).toLocaleString()}
                  </div>
                </div>
                
                <div className="flex flex-col items-end flex-shrink-0">
                  <div
                    className={`px-3 py-1 rounded-full text-xs font-bold shadow-sm ${
                      email.label === 1
                        ? "bg-red-500 text-white"
                        : "bg-green-500 text-white"
                    }`}
                  >
                    {email.label === 1 ? "PHISHING" : "SAFE"}
                  </div>
                  <div className="text-xs text-gray-500 mt-1 font-mono">
                    Score: {email.score.toFixed(4)}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12 text-gray-500 border border-dashed border-gray-300 rounded-lg bg-gray-50">
              <div className="text-5xl mb-3">📭</div>
              <p className="text-lg font-semibold">No Scan History</p>
              <p className="text-sm mt-1">Connect Gmail and click "Scan Gmail" to get started.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}