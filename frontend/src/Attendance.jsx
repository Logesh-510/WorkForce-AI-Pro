import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  CalendarDays,
  Clock3,
  LogIn,
  LogOut,
  RefreshCw,
  Save,
  Search,
} from "lucide-react";

import {
  checkIn,
  checkOut,
  getAttendanceHistory,
  getAttendanceManagement,
  updateAttendance,
} from "./services/attendance";
import { getEmployees } from "./services/workforce";

function formatTime(value) {
  if (!value) return "—";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);

  return parsed.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDate(value) {
  if (!value) return "—";

  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return value;

  return parsed.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatHours(value) {
  if (value == null || value === "") return "—";

  const hours = Number(value);
  if (!Number.isFinite(hours)) return "—";

  return `${hours.toFixed(2)} h (${Math.round(hours * 60)} min)`;
}

function Attendance({ user }) {
  const isManager = ["ADMIN", "HR"].includes(user?.role);

  const [records, setRecords] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [savingId, setSavingId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [shiftName, setShiftName] = useState("General");
  const [refreshKey, setRefreshKey] = useState(0);

  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [employeeId, setEmployeeId] = useState("");

  const [drafts, setDrafts] = useState({});

  const today = new Date().toLocaleDateString("en-CA");
  const todaysRecord = records.find(
    (record) => record.attendance_date === today
  );

  const loadAttendance = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const fetchRecords = isManager
        ? getAttendanceManagement
        : getAttendanceHistory;

      const options = {
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        limit: 100,
      };

      if (isManager && employeeId) {
        options.employeeId = employeeId;
      }

      const data = await fetchRecords(options);
      setRecords(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Unable to load attendance.");
    } finally {
      setLoading(false);
    }
  }, [isManager, startDate, endDate, employeeId]);

  useEffect(() => {
    loadAttendance();
  }, [loadAttendance, refreshKey]);

  useEffect(() => {
    if (!isManager) return;

    getEmployees()
      .then((data) => setEmployees(Array.isArray(data) ? data : []))
      .catch((err) => {
        setError(
          err.message || "Unable to load employees for attendance filtering."
        );
      });
  }, [isManager]);

  async function performAction(action) {
    setBusy(true);
    setError("");
    setMessage("");

    try {
      const result =
        action === "check-in"
          ? await checkIn(shiftName)
          : await checkOut();

      setMessage(
        action === "check-in"
          ? "Check-in recorded successfully."
          : "Check-out recorded successfully."
      );

      if (result) {
        setRecords((previous) => [
          result,
          ...previous.filter((record) => record.id !== result.id),
        ].slice(0, 100));
      }

      setRefreshKey((value) => value + 1);
    } catch (err) {
      setError(err.message || "Attendance action failed.");
    } finally {
      setBusy(false);
    }
  }

  function updateDraft(record, field, value) {
    setDrafts((previous) => ({
      ...previous,
      [record.id]: {
        status: record.status,
        shift_name: record.shift_name || "",
        notes: record.notes || "",
        overtime_hours: String(record.overtime_hours ?? 0),
        ...previous[record.id],
        [field]: value,
      },
    }));
  }

  async function saveRecord(record) {
    const draft = drafts[record.id];
    if (!draft) return;

    const overtime = Number(draft.overtime_hours);

    if (!Number.isFinite(overtime) || overtime < 0 || overtime > 999.99) {
      setError("Overtime must be between 0 and 999.99 hours.");
      return;
    }

    setSavingId(record.id);
    setError("");
    setMessage("");

    try {
      const updated = await updateAttendance(record.id, {
        status: draft.status,
        shift_name: draft.shift_name.trim() || null,
        notes: draft.notes.trim() || null,
        overtime_hours: overtime,
      });

      setRecords((previous) =>
        previous.map((item) => item.id === updated.id ? updated : item)
      );

      setDrafts((previous) => {
        const next = { ...previous };
        delete next[record.id];
        return next;
      });

      setMessage(`Attendance record #${record.id} updated successfully.`);
    } catch (err) {
      setError(err.message || "Unable to update attendance.");
    } finally {
      setSavingId(null);
    }
  }

  const checkedIn = Boolean(todaysRecord?.check_in);
  const checkedOut = Boolean(todaysRecord?.check_out);

  const totalHours = records.reduce(
    (sum, record) => sum + Number(record.working_hours || 0),
    0
  );

  const presentDays = records.filter(
    (record) => record.status === "PRESENT"
  ).length;

  return (
    <div className="attendance-page">
      <section className="metrics-grid attendance-metrics">
        <article className="metric-card">
          <div className="metric-card-top">
            <div className="metric-icon purple">
              <CalendarDays size={20} />
            </div>
          </div>
          <p className="metric-label">Attendance records</p>
          <strong className="metric-value">
            {loading ? "..." : records.length}
          </strong>
          <p className="metric-note">Records in loaded history</p>
        </article>

        <article className="metric-card">
          <div className="metric-card-top">
            <div className="metric-icon green">
              <Activity size={20} />
            </div>
          </div>
          <p className="metric-label">Present days</p>
          <strong className="metric-value">
            {loading ? "..." : presentDays}
          </strong>
          <p className="metric-note">Present records in loaded history</p>
        </article>

        <article className="metric-card">
          <div className="metric-card-top">
            <div className="metric-icon blue">
              <Clock3 size={20} />
            </div>
          </div>
          <p className="metric-label">Recorded hours</p>
          <strong className="metric-value">
            {loading ? "..." : totalHours.toFixed(2)}
          </strong>
          <p className="metric-note">Sum of saved working hours</p>
        </article>
      </section>

      <section className="panel attendance-action-panel">
        <div className="panel-header">
          <div>
            <h3>Today's attendance</h3>
            <p>{formatDate(today)}</p>
          </div>

          <button
            className="icon-button"
            onClick={() => setRefreshKey((value) => value + 1)}
            disabled={loading || busy}
            title="Refresh attendance"
            aria-label="Refresh attendance"
          >
            <RefreshCw size={17} />
          </button>
        </div>

        <div className="attendance-status">
          <div>
            <span className="metric-label">Check-in</span>
            <strong>{formatTime(todaysRecord?.check_in)}</strong>
          </div>
          <div>
            <span className="metric-label">Check-out</span>
            <strong>{formatTime(todaysRecord?.check_out)}</strong>
          </div>
          <div>
            <span className="metric-label">Working hours</span>
            <strong>{formatHours(todaysRecord?.working_hours)}</strong>
          </div>
        </div>

        {!isManager && (
          <div className="attendance-controls">
            <label>
              Shift
              <select
                value={shiftName}
                onChange={(event) => setShiftName(event.target.value)}
                disabled={busy || checkedIn}
              >
                <option value="General">General</option>
                <option value="Morning">Morning</option>
                <option value="Evening">Evening</option>
                <option value="Night">Night</option>
              </select>
            </label>

            <div className="attendance-buttons">
              <button
                className="primary-button"
                onClick={() => performAction("check-in")}
                disabled={busy || loading || checkedIn}
              >
                <LogIn size={17} />
                {busy ? "Processing..." : "Check In"}
              </button>

              <button
                className="secondary-button"
                onClick={() => performAction("check-out")}
                disabled={busy || loading || !checkedIn || checkedOut}
              >
                <LogOut size={17} />
                Check Out
              </button>
            </div>
          </div>
        )}

        {isManager && (
          <p className="attendance-hint">
            Review workforce attendance below. Changes are saved to the
            attendance record through the management API.
          </p>
        )}

        {message && (
          <p className="attendance-feedback success-message" role="status">
            {message}
          </p>
        )}

        {error && (
          <p className="attendance-feedback error-message" role="alert">
            {error}
          </p>
        )}
      </section>

      <section className="panel attendance-history-panel">
        <div className="panel-header">
          <div>
            <h3>{isManager ? "Workforce attendance" : "My attendance history"}</h3>
            <p>
              {isManager
                ? "Filter, review, and correct workforce records."
                : "Your most recent attendance records."}
            </p>
          </div>
        </div>

        {isManager && (
          <div className="attendance-filters">
            <label>
              Employee
              <select
                value={employeeId}
                onChange={(event) => setEmployeeId(event.target.value)}
              >
                <option value="">All employees</option>
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.employee_code} (ID: {employee.id})
                    {!employee.is_active ? " — Inactive" : ""}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Start date
              <input
                type="date"
                value={startDate}
                onChange={(event) => setStartDate(event.target.value)}
              />
            </label>

            <label>
              End date
              <input
                type="date"
                value={endDate}
                onChange={(event) => setEndDate(event.target.value)}
              />
            </label>

            <button
              className="secondary-button"
              onClick={() => setRefreshKey((value) => value + 1)}
              disabled={loading}
            >
              <Search size={16} />
              Apply filters
            </button>

            <button
              className="secondary-button"
              onClick={() => {
                setEmployeeId("");
                setStartDate("");
                setEndDate("");
              }}
              disabled={loading}
            >
              Clear filters
            </button>
          </div>
        )}

        {loading ? (
          <div className="workforce-message">Loading attendance...</div>
        ) : records.length === 0 ? (
          <div className="workforce-message">
            No attendance records were found.
          </div>
        ) : (
          <div className="workforce-table-wrap">
            <table className="workforce-table">
              <thead>
                <tr>
                  {isManager && <th>EMPLOYEE ID</th>}
                  <th>DATE</th>
                  <th>SHIFT</th>
                  <th>CHECK-IN</th>
                  <th>CHECK-OUT</th>
                  <th>HOURS</th>
                  <th>STATUS</th>
                  {isManager && (
                    <>
                      <th>OVERTIME</th>
                      <th>NOTES</th>
                      <th>SAVE</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {records.map((record) => {
                  const draft = drafts[record.id] || {
                    status: record.status,
                    shift_name: record.shift_name || "",
                    notes: record.notes || "",
                    overtime_hours: String(record.overtime_hours ?? 0),
                  };

                  return (
                    <tr key={record.id}>
                      {isManager && <td>{record.employee_id}</td>}
                      <td>{formatDate(record.attendance_date)}</td>

                      <td>
                        {isManager ? (
                          <input
                            aria-label={`Shift for record ${record.id}`}
                            value={draft.shift_name}
                            maxLength={50}
                            onChange={(event) =>
                              updateDraft(record, "shift_name", event.target.value)
                            }
                          />
                        ) : (
                          record.shift_name || "—"
                        )}
                      </td>

                      <td>{formatTime(record.check_in)}</td>
                      <td>{formatTime(record.check_out)}</td>
                      <td>{formatHours(record.working_hours)}</td>

                      <td>
                        {isManager ? (
                          <select
                            aria-label={`Status for record ${record.id}`}
                            value={draft.status}
                            onChange={(event) =>
                              updateDraft(record, "status", event.target.value)
                            }
                          >
                            <option value="PRESENT">PRESENT</option>
                            <option value="ABSENT">ABSENT</option>
                            <option value="HALF_DAY">HALF_DAY</option>
                            <option value="ON_LEAVE">ON_LEAVE</option>
                          </select>
                        ) : (
                          record.status || "—"
                        )}
                      </td>

                      {isManager && (
                        <>
                          <td>
                            <input
                              type="number"
                              min="0"
                              max="999.99"
                              step="0.25"
                              aria-label={`Overtime hours for record ${record.id}`}
                              value={draft.overtime_hours}
                              onChange={(event) =>
                                updateDraft(
                                  record,
                                  "overtime_hours",
                                  event.target.value
                                )
                              }
                            />
                          </td>

                          <td>
                            <input
                              aria-label={`Notes for record ${record.id}`}
                              value={draft.notes}
                              maxLength={500}
                              onChange={(event) =>
                                updateDraft(record, "notes", event.target.value)
                              }
                            />
                          </td>

                          <td>
                            <button
                              className="secondary-button"
                              onClick={() => saveRecord(record)}
                              disabled={savingId === record.id}
                              title={`Save record ${record.id}`}
                            >
                              <Save size={15} />
                              {savingId === record.id ? "Saving..." : "Save"}
                            </button>
                          </td>
                        </>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

export default Attendance;
