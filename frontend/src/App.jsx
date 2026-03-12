import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import api, { setAuthToken } from "./api/client";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import Knowledge from "./pages/Knowledge";
import Upload from "./pages/Upload";
import AskAI from "./pages/AskAI";
import Profile from "./pages/Profile";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/knowledge", label: "Knowledge" },
  { to: "/upload", label: "Upload" },
  { to: "/ask-ai", label: "Ask AI" },
  { to: "/profile", label: "Profile" }
];

function ProtectedRoute({ isAuthenticated, children }) {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);

  const loadCurrentUser = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setUser(null);
      setLoadingUser(false);
      return;
    }

    try {
      const response = await api.get("/auth/me");
      setUser(response.data);
    } catch {
      setAuthToken(null);
      setUser(null);
    } finally {
      setLoadingUser(false);
    }
  };

  useEffect(() => {
    loadCurrentUser();
  }, [location.pathname]);

  const handleAuthSuccess = async (token) => {
    setAuthToken(token);
    await loadCurrentUser();
    navigate("/dashboard");
  };

  const handleLogout = () => {
    setAuthToken(null);
    setUser(null);
    navigate("/login");
  };

  const isAuthenticated = Boolean(user);
  const isAuthPage = location.pathname === "/login" || location.pathname === "/signup";

  return (
    <div className="app-shell">
      {!isAuthPage && (
        <aside className="sidebar">
          <div>
            <h1>AI Life Architect</h1>
            <p className="muted">Personal knowledge workspace</p>
          </div>
          <nav>
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} className="nav-link">
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="sidebar-footer">
            <p>{user?.full_name || "Guest"}</p>
            <button className="secondary-button" onClick={handleLogout} type="button">
              Log Out
            </button>
          </div>
        </aside>
      )}
      <main className={isAuthPage ? "auth-layout" : "content-layout"}>
        {loadingUser ? (
          <div className="card"><p>Loading...</p></div>
        ) : (
          <Routes>
            <Route path="/" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} />
            <Route path="/login" element={<Login onSuccess={handleAuthSuccess} />} />
            <Route path="/signup" element={<Signup onSuccess={handleAuthSuccess} />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute isAuthenticated={isAuthenticated}>
                  <Dashboard user={user} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/knowledge"
              element={
                <ProtectedRoute isAuthenticated={isAuthenticated}>
                  <Knowledge />
                </ProtectedRoute>
              }
            />
            <Route
              path="/upload"
              element={
                <ProtectedRoute isAuthenticated={isAuthenticated}>
                  <Upload />
                </ProtectedRoute>
              }
            />
            <Route
              path="/ask-ai"
              element={
                <ProtectedRoute isAuthenticated={isAuthenticated}>
                  <AskAI />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute isAuthenticated={isAuthenticated}>
                  <Profile />
                </ProtectedRoute>
              }
            />
          </Routes>
        )}
      </main>
    </div>
  );
}
