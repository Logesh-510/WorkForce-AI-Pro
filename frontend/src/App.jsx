
import { useEffect, useState } from "react";
import {
  Activity,
  BrainCircuit,
  Building2,
  CalendarCheck,
  CircleHelp,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  Users,
  X,
} from "lucide-react";

import "./App.css";
import Login from "./Login";
import WorkforceTable from "./WorkforceTable";
import { apiRequest } from "./services/api";
import { logoutUser } from "./services/auth";
import {
  getDepartments,
  getEmployees,
} from "./services/workforce";
import AttritionPrediction from "./AttritionPrediction";
import Attendance from "./Attendance";

const navigation = [
  { label: "Dashboard", icon: LayoutDashboard },
  { label: "Employees", icon: Users },
  { label: "Departments", icon: Building2 },
  { label: "Attendance", icon: CalendarCheck },
  { label: "Attrition Prediction", icon: BrainCircuit },
];

const MODEL_METRICS = {
  accuracy: "72.0%",
  recall: "64.4%",
  precision: "31.7%",
  evaluationRecords: "368",
};

function App() {
  const [activePage, setActivePage] = useState("Dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [search, setSearch] = useState("");

  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [dataLoading, setDataLoading] = useState(false);
  const [dataError, setDataError] = useState("");

  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  // Employee table columns
  const employeeColumns = [
    {
      key: "employee_code",
      label: "EMPLOYEE CODE",
      value: (row) => row.employee_code,
    },
    {
      key: "department",
      label: "DEPARTMENT",
      value: (row) => row.department,
    },
    {
      key: "job_title",
      label: "JOB TITLE",
      value: (row) => row.job_title,
    },
    {
      key: "employment_type",
      label: "EMPLOYMENT TYPE",
      value: (row) => row.employment_type,
    },
    {
      key: "annual_salary",
      label: "ANNUAL SALARY",
      value: (row) => row.annual_salary,
      render: (row) => {
        const salary = Number(row.annual_salary);

        return Number.isFinite(salary)
          ? salary.toLocaleString("en-IN", {
              style: "currency",
              currency: "INR",
              maximumFractionDigits: 0,
            })
          : row.annual_salary ?? "—";
      },
    },
    {
      key: "status",
      label: "STATUS",
      value: (row) => (row.is_active ? "Active" : "Inactive"),
    },
  ];

  // Department table columns
  const departmentColumns = [
    {
      key: "name",
      label: "DEPARTMENT",
      value: (row) => row.name,
    },
    {
      key: "code",
      label: "CODE",
      value: (row) => row.code,
    },
    {
      key: "description",
      label: "DESCRIPTION",
      value: (row) => row.description,
    },
    {
      key: "status",
      label: "STATUS",
      value: (row) => (row.is_active ? "Active" : "Inactive"),
    },
  ];

  // Restore and verify the current login session
  useEffect(() => {
    let cancelled = false;

    async function checkSession() {
      const token = sessionStorage.getItem("access_token");

      if (!token) {
        setAuthLoading(false);
        return;
      }

      try {
        const currentUser = await apiRequest("/api/v1/auth/me");

        if (cancelled) return;

        if (currentUser?.is_active) {
          setUser(currentUser);
        } else {
          logoutUser();
        }
      } catch {
        if (!cancelled) {
          logoutUser();
        }
      } finally {
        if (!cancelled) {
          setAuthLoading(false);
        }
      }
    }

    checkSession();

    return () => {
      cancelled = true;
    };
  }, []);

  // Load real employee and department data after authentication
  useEffect(() => {
    if (!user) return undefined;

    let cancelled = false;

    async function loadWorkforceData() {
      setDataLoading(true);
      setDataError("");

      try {
        const [employeeData, departmentData] = await Promise.all([
          getEmployees(),
          getDepartments(),
        ]);

        if (cancelled) return;

        if (
          !Array.isArray(employeeData) ||
          !Array.isArray(departmentData)
        ) {
          throw new Error(
            "The API returned an unexpected data format."
          );
        }

        setEmployees(employeeData);
        setDepartments(departmentData);
      } catch (error) {
        if (!cancelled) {
          setDataError(
            error.message || "Unable to load workforce data."
          );
        }
      } finally {
        if (!cancelled) {
          setDataLoading(false);
        }
      }
    }

    loadWorkforceData();

    return () => {
      cancelled = true;
    };
  }, [user]);

  function handleLogin(loggedInUser) {
    setUser(loggedInUser);
    setActivePage("Dashboard");
    setSearch("");
  }

  function handleLogout() {
    logoutUser();
    setUser(null);
    setEmployees([]);
    setDepartments([]);
    setDataError("");
    setDataLoading(false);
    setSearch("");
    setSidebarOpen(false);
    setActivePage("Dashboard");
  }

  function navigateTo(page) {
    setActivePage(page);
    setSearch("");
    setSidebarOpen(false);
  }

  const activeEmployees = employees.filter(
    (employee) => employee.is_active
  ).length;

  // Authentication loading screen
  if (authLoading) {
    return (
      <div className="auth-loading">
        <Activity size={28} />
        <p>Loading your secure workspace...</p>
      </div>
    );
  }

  // Login screen
  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="app-shell">
      <aside
        className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}
      >
        <div className="brand">
          <div className="brand-icon">
            <Activity size={23} />
          </div>

          <div>
            <h2>
              WorkForce<span>AI</span>
            </h2>
            <p>WORKFORCE INTELLIGENCE</p>
          </div>

          <button
            className="icon-button close-sidebar"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>

        <div className="nav-heading">WORKSPACE</div>

        <nav className="navigation">
          {navigation.map(({ label, icon: Icon }) => (
            <button
              key={label}
              className={`nav-item ${
                activePage === label ? "active" : ""
              }`}
              onClick={() => navigateTo(label)}
            >
              <Icon size={19} />
              <span>{label}</span>

              {label === "Attrition Prediction" && (
                <span className="new-badge">ML</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="security-card">
            <ShieldCheck size={21} />
            <div>
              <strong>Security first</strong>
              <p>Role-based access control</p>
            </div>
          </div>

          <button
            className={`nav-item ${
              activePage === "Settings" ? "active" : ""
            }`}
            onClick={() => navigateTo("Settings")}
          >
            <Settings size={19} />
            <span>Settings</span>
          </button>

          <button
            className={`nav-item ${
              activePage === "Help & Support" ? "active" : ""
            }`}
            onClick={() => navigateTo("Help & Support")}
          >
            <CircleHelp size={19} />
            <span>Help &amp; Support</span>
          </button>

          <div className="sidebar-footer">
            WORKFORCE AI PRO · V1.0
          </div>
        </div>
      </aside>

      {sidebarOpen && (
        <button
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close navigation overlay"
        />
      )}

      <main className="main-area">
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={22} />
          </button>

          <div className="breadcrumb">
            Workspace <span>/</span> <strong>{activePage}</strong>
          </div>

          <div className="topbar-right">
            <label className="search-box">
              <Search size={17} />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search workspace..."
                aria-label="Search workspace"
              />
              <kbd>⌘ K</kbd>
            </label>

            <div className="profile">
              <div className="avatar">
                {(user.full_name || user.email || "U")
                  .charAt(0)
                  .toUpperCase()}
              </div>

              <div className="profile-info">
                <strong>{user.full_name || user.email}</strong>
                <span>
                  {(user.role || "USER").replace("_", " ")}
                </span>
              </div>

              <button
                className="icon-button"
                onClick={handleLogout}
                aria-label="Sign out"
                title="Sign out"
              >
                <LogOut size={17} />
              </button>
            </div>
          </div>
        </header>

        <section className="page-content">
          {/* Shared page heading */}
          <div className="welcome-row">
            <div>
              <div className="eyebrow">
                <span className="status-dot" />
                WORKFORCE INTELLIGENCE PLATFORM
              </div>

              <h1>
                {activePage === "Dashboard"
                  ? "People analytics, simplified."
                  : activePage}
              </h1>

              <p className="page-description">
                {activePage === "Dashboard"
                  ? "A clearer view of your workforce. Better decisions start here."
                  : activePage === "Employees"
                    ? "Explore employee records from your workforce API."
                    : activePage === "Departments"
                      ? "View your organisation's department directory."
                      : activePage === "Attendance"
                        ? "Track daily attendance, working hours, and attendance history."
                        : activePage === "Attrition Prediction"
                          ? "Explore experimental AI-assisted attrition estimates."
                          : "Your workforce intelligence workspace."}
              </p>
            </div>

            <div className="date-pill">
              <Activity size={16} />
              <span>HR Intelligence</span>
            </div>
          </div>

          {/* Dashboard */}
          {activePage === "Dashboard" && (
            <>
              <div className="notice-banner">
                <div className="notice-icon">
                  <BrainCircuit size={21} />
                </div>

                <div className="notice-copy">
                  <strong>AI-powered workforce insights</strong>
                  <p>
                    Explore attrition predictions and workforce patterns
                    in one workspace. Predictions are experimental and
                    should not determine employment decisions.
                  </p>
                </div>

                <button
                  className="notice-action"
                  onClick={() =>
                    navigateTo("Attrition Prediction")
                  }
                >
                  Explore AI <span>→</span>
                </button>
              </div>

              <div className="section-heading">
                <div>
                  <h2>Workforce overview</h2>
                  <p>
                    {dataLoading
                      ? "Synchronising workforce data..."
                      : "Live counts from your workforce API."}
                  </p>
                </div>

                <span className="demo-label">
                  {dataLoading
                    ? "SYNCING DATA"
                    : dataError
                      ? "API ERROR"
                      : "LIVE WORKFORCE DATA"}
                </span>
              </div>

              {dataError && (
                <div className="workforce-message workforce-error">
                  Unable to load workforce data: {dataError}
                </div>
              )}

              <div className="metrics-grid">
                <MetricCard
                  icon={Users}
                  label="Total employees"
                  value={
                    dataLoading
                      ? "..."
                      : employees.length.toLocaleString("en-IN")
                  }
                  note="Live employee API records"
                  color="purple"
                />

                <MetricCard
                  icon={Activity}
                  label="Active employees"
                  value={
                    dataLoading
                      ? "..."
                      : activeEmployees.toLocaleString("en-IN")
                  }
                  note="Records marked active"
                  color="orange"
                />

                <MetricCard
                  icon={Building2}
                  label="Departments"
                  value={
                    dataLoading
                      ? "..."
                      : departments.length.toLocaleString("en-IN")
                  }
                  note="Live department API records"
                  color="blue"
                />

                <MetricCard
                  icon={BrainCircuit}
                  label="Prediction model"
                  value="Ready"
                  note="Logistic Regression"
                  color="green"
                />
              </div>

              <div className="content-grid">
                <section className="panel model-panel">
                  <div className="panel-header">
                    <div>
                      <h3>Attrition intelligence</h3>
                      <p>
                        IBM benchmark dataset · Held-out evaluation
                      </p>
                    </div>
                    <span className="model-tag">ML MODEL</span>
                  </div>

                  <div className="model-score">
                    <div className="score-ring">
                      <div>
                        <strong>{MODEL_METRICS.accuracy}</strong>
                        <span>Accuracy</span>
                      </div>
                    </div>

                    <div className="score-description">
                      <strong>Logistic Regression</strong>
                      <p>
                        Evaluated on a held-out portion of the public
                        IBM HR benchmark dataset. These are model
                        evaluation results, not live workforce statistics.
                      </p>
                      <span className="caution">
                        Prototype · Not production validated
                      </span>
                    </div>
                  </div>

                  <div className="metric-divider" />

                  <div className="model-stats">
                    <div>
                      <span>Attrition recall</span>
                      <strong>{MODEL_METRICS.recall}</strong>
                    </div>
                    <div>
                      <span>Attrition precision</span>
                      <strong>{MODEL_METRICS.precision}</strong>
                    </div>
                    <div>
                      <span>Evaluation records</span>
                      <strong>{MODEL_METRICS.evaluationRecords}</strong>
                    </div>
                  </div>
                </section>

                <section className="panel actions-panel">
                  <div className="panel-header">
                    <div>
                      <h3>Quick actions</h3>
                      <p>Continue your workflow</p>
                    </div>
                  </div>

                  <button
                    className="action-row"
                    onClick={() =>
                      navigateTo("Attrition Prediction")
                    }
                  >
                    <div className="action-icon purple-bg">
                      <BrainCircuit size={20} />
                    </div>
                    <div>
                      <strong>Run attrition prediction</strong>
                      <p>Explore an individual model estimate</p>
                    </div>
                    <span className="action-arrow">→</span>
                  </button>

                  <button
                    className="action-row"
                    onClick={() => navigateTo("Employees")}
                  >
                    <div className="action-icon blue-bg">
                      <Users size={20} />
                    </div>
                    <div>
                      <strong>Explore employees</strong>
                      <p>Open the employee workspace</p>
                    </div>
                    <span className="action-arrow">→</span>
                  </button>

                  <div className="action-note">
                    <ShieldCheck size={17} />
                    <span>
                      Secure session active · Signed in as{" "}
                      {(user.role || "USER").replace("_", " ")}
                    </span>
                  </div>
                </section>
              </div>
            </>
          )}

          {/* Employees */}
          {activePage === "Employees" && (
            <WorkforceTable
              title="Employees"
              description="Employee records retrieved from your workforce API."
              columns={employeeColumns}
              rows={employees}
              loading={dataLoading}
              error={dataError}
              search={search}
              onSearchChange={setSearch}
              emptyMessage="No employee records are available."
            />
          )}

          {/* Departments */}
          {activePage === "Departments" && (
            <WorkforceTable
              title="Departments"
              description="Department records retrieved from your workforce API."
              columns={departmentColumns}
              rows={departments}
              loading={dataLoading}
              error={dataError}
              search={search}
              onSearchChange={setSearch}
              emptyMessage="No department records are available."
            />
          )}

          {/* Attendance */}
          {activePage === "Attendance" && <Attendance />}

          {/* Attrition prediction */}
          {activePage === "Attrition Prediction" && (
            <AttritionPrediction />
          )}

          {/* Settings placeholder */}
          {activePage === "Settings" && (
            <section className="panel">
              <div className="panel-header">
                <div>
                  <h3>Settings</h3>
                  <p>Workspace preferences</p>
                </div>
              </div>
              <p className="workforce-message">
                Settings will be implemented in a future step.
              </p>
            </section>
          )}

          {/* Help placeholder */}
          {activePage === "Help & Support" && (
            <section className="panel">
              <div className="panel-header">
                <div>
                  <h3>Help &amp; Support</h3>
                  <p>WorkForce AI Pro assistance</p>
                </div>
              </div>
              <p className="workforce-message">
                For now, check the API health endpoint and backend logs
                when troubleshooting connection issues.
              </p>
            </section>
          )}

          {/* Shared footer */}
          <footer className="page-footer">
            <span>© 2026 WorkForce AI Pro</span>
            <span>Built for responsible workforce intelligence</span>
          </footer>
        </section>
      </main>
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, note, color }) {
  return (
    <article className="metric-card">
      <div className="metric-card-top">
        <div className={`metric-icon ${color}`}>
          <Icon size={20} />
        </div>
        <span className="metric-indicator" />
      </div>

      <p className="metric-label">{label}</p>
      <strong className="metric-value">{value}</strong>
      <p className="metric-note">{note}</p>
    </article>
  );
}

export default App;
