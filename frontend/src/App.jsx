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
import BrainMap from "./pages/BrainMap";

const navItems = [
  { to: "/dashboard", label: "Dashboard", shortLabel: "DB" },
  { to: "/knowledge", label: "Knowledge", shortLabel: "KN" },
  { to: "/brain-map", label: "Brain Map", shortLabel: "BM" },
  { to: "/upload", label: "Upload", shortLabel: "UP" },
  { to: "/ask-ai", label: "Ask AI", shortLabel: "AI" },
  { to: "/profile", label: "Profile", shortLabel: "PR" }
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
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

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
        <aside className={`sidebar ${sidebarCollapsed ? "collapsed" : ""}`}>
          <div className="sidebar-header">
            <div>
              <h1>{sidebarCollapsed ? "AI" : "AI Life Architect"}</h1>
              {!sidebarCollapsed && <p className="muted">Personal knowledge workspace</p>}
            </div>
            <button
              type="button"
              className="sidebar-toggle"
              onClick={() => setSidebarCollapsed((current) => !current)}
              aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              <span className={`sidebar-toggle-icon ${sidebarCollapsed ? "right" : "left"}`} />
            </button>
          </div>
          <nav>
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className="nav-link"
                title={sidebarCollapsed ? item.label : undefined}
              >
                {sidebarCollapsed ? <span className="nav-badge">{item.shortLabel}</span> : item.label}
              </NavLink>
            ))}
          </nav>
          <div className="sidebar-footer">
            {!sidebarCollapsed && <p>{user?.full_name || "Guest"}</p>}
            <button className="secondary-button" onClick={handleLogout} type="button">
              {sidebarCollapsed ? "Out" : "Log Out"}
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
              path="/brain-map"
              element={
                <ProtectedRoute isAuthenticated={isAuthenticated}>
                  <BrainMap />
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
