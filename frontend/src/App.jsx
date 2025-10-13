import { Outlet, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      checkUserAuth(token);
    } else {
      setLoading(false);
    }
  }, []);

  const checkUserAuth = async (token) => {
    try {
      const response = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        localStorage.removeItem("access_token");
      }
    } catch (error) {
      console.error("Auth check failed:", error);
      localStorage.removeItem("access_token");
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
    navigate("/");
  };

  const initiateGoogleAuth = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("Please log in first");
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/auth/google`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        // redirect instead of opening new tab
        window.location.href = data.auth_url;
      } else {
        alert("Failed to initiate Google authentication");
      }
    } catch (error) {
      console.error("Google auth error:", error);
      alert("Google authentication failed");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-5xl mx-auto py-6 px-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">🛡️ PhishGuard Pro</h1>
            <p className="text-gray-500">Smart Gmail phishing detector</p>
          </div>

          <div className="flex items-center gap-4">
            {user ? (
              <>
                <span className="text-sm text-gray-600">
                  Hello, {user.full_name || user.username || user.email}
                </span>
                <button
                  onClick={initiateGoogleAuth}
                  className={`px-4 py-2 rounded-lg border ${
                    user.gmail_connected
                      ? "border-green-500 text-green-500 hover:bg-green-50"
                      : "border-blue-500 text-blue-500 hover:bg-blue-50"
                  }`}
                >
                  {user.gmail_connected ? "Gmail Connected ✓" : "Connect Gmail"}
                </button>
                <button
                  onClick={logout}
                  className="px-4 py-2 rounded-lg bg-red-500 text-white hover:bg-red-600"
                >
                  Logout
                </button>
              </>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => navigate("/login")}
                  className="px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50"
                >
                  Login
                </button>
                <button
                  onClick={() => navigate("/register")}
                  className="px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600"
                >
                  Register
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-4">
        <Outlet context={{ user, setUser }} />
      </main>
    </div>
  );
}
