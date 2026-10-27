
import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  CalendarDays,
  Clock3,
  LogIn,
  LogOut,
  RefreshCw,
} from "lucide-react";

import {
  checkIn,
  checkOut,
  getAttendanceHistory,
  getAttendanceManagement,
} from "./services/attendance";

function formatDateTime(value) {
  if (!value) return "—";

  const parsed = new Date(
    value.endsWith?.("Z") ? value : `${value}Z`
  );

  if (Number.isNaN(parsed.getTime())) return value;

  return parsed.toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatHours(value) {
  if (value == null) return "—";

  const hours = Number(value);
  return Number.isFinite(hours) ? `${hours.toFixed(2)} hrs` : "—";
}

export default function AttendancePage({ user }) {
  const isManager = ["ADMIN", "HR"].includes(user?.role);

  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [shiftName, setShiftName] = useState("General");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const loadAttendance = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const options = {
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        limit: 100,
      };

      const result = isManager
        ? await getAttendanceManagement(options)
        : await getAttendanceHistory(options);

      setRecords(Array.isArray(result) ? result : []);
    } catch (err) {
      setError(err.message || "Unable to load attendance history.");
    } finally {
      setLoading(false);
    }
  }, [isManager, startDate, endDate]);

  useEffect(() => {
    loadAttendance();
  }, [loadAttendance]);

  const today = new Date().toLocaleDateString("en-CA");

  const todaysRecord = records.find(
    (record) => record.attendance_date === today
  );

  async function handleAttendanceAction(action) {
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

      setRecords((previous) => {
        const withoutToday = previous.filter(
          (record) => record.id !== result.id
        );

        return [result, ...withoutToday].slice(0, 100);
      });

      await loadAttendance();
    } catch (err) {
      setError(err.message || "Unable to update attendance.");
    } finally {
      setBusy(false);
    }
  }

  const hasCheckedIn = Boolean(todaysRecord?.check_in);
  const hasCheckedOut = Boolean(todaysRecord?.check_out);

  return (
    <div className="attendance-page">
      <section className="panel attendance-action-panel">
        <div className="panel-header">
          <div>
            <h3>Daily attendance</h3>
            <p>Record your attendance and track working hours.</p>
          </div>

          <button
            type="button"
            className="attendance-refresh"
            onClick={loadAttendance}
            disabled={loading || busy}
            aria-label="Refresh attendance"
            title="Refresh attendance"
          >
            <RefreshCw size={17} />
          </button>
        </div>

        <div className="attendance-today">
          <CalendarDays size={19} />
          <span>
            {new Date().toLocaleDateString("en-IN", {
              weekday: "long",
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </span>
        </div>

        {isManager && (
          <p className="attendance-manager-note">
            Manager view: displaying attendance records for all employees.
          </p>
        )}

        <label className="attendance-field">
          <span>Shift</span>
          <select
            value={shiftName}
            onChange={(event) => setShiftName(event.target.value)}
            disabled={busy || hasCheckedIn}
          >
            <option value="General">General</option>
            <option value="Morning">Morning</option>
            <option value="Evening">Evening</option>
            <option value="Night">Night</option>
          </select>
        </label>

        <div className="attendance-action-buttons">
          <button
            type="button"
            className="attendance-button check-in-button"
            onClick={() => handleAttendanceAction("check-in")}
            disabled={busy || hasCheckedIn}
          >
            <LogIn size={18} />
            {busy && !hasCheckedIn ? "Processing..." : "Check In"}
          </button>

          <button
            type="button"
            className="attendance-button check-out-button"
            onClick={() => handleAttendanceAction("check-out")}
            disabled={busy || !hasCheckedIn || hasCheckedOut}
          >
            <LogOut size={18} />
            Check Out
          </button>
        </div>

        {hasCheckedIn && (
          <div className="attendance-status">
            <Activity size={17} />
            <span>
              Checked in at {formatDateTime(todaysRecord.check_in)}
              {hasCheckedOut ? " · Shift completed" : " · Shift in progress"}
            </span>
          </div>
        )}

        {message && (
          <p className="attendance-feedback attendance-success" role="status">
            {message}
          </p>
        )}

        {error && (
          <p className="attendance-feedback attendance-error" role="alert">
            {error}
          </p>
        )}
      </section>

      <section className="panel attendance-history-panel">
        <div className="panel-header">
          <div>
            <h3>Attendance history</h3>
            <p>
              {isManager
                ? "Review records across the workforce."
                : "Review your recent attendance records."}
            </p>
          </div>
          <Clock3 size={20} />
        </div>

        <div className="attendance-filters">
          <label className="attendance-field">
            <span>From date</span>
            <input
              type="date"
              value={startDate}
              max={endDate || undefined}
              onChange={(event) => setStartDate(event.target.value)}
            />
          </label>

          <label className="attendance-field">
            <span>To date</span>
            <input
              type="date"
              value={endDate}
              min={startDate || undefined}
              onChange={(event) => setEndDate(event.target.value)}
            />
          </label>

          <button
            type="button"
            className="attendance-filter-reset"
            onClick={() => {
              setStartDate("");
              setEndDate("");
            }}
          >
            Clear dates
          </button>
        </div>

        {loading ? (
          <p className="workforce-message">Loading attendance records...</p>
        ) : records.length === 0 ? (
          <p className="workforce-message">
            No attendance records found for this period.
          </p>
        ) : (
          <div className="workforce-table-wrap attendance-table-wrap">
            <table className="workforce-table attendance-table">
              <thead>
                <tr>
                  {isManager && <th>EMPLOYEE ID</th>}
                  <th>DATE</th>
                  <th>CHECK IN</th>
                  <th>CHECK OUT</th>
                  <th>WORKING HOURS</th>
                  <th>STATUS</th>
                  <th>SHIFT</th>
                </tr>
              </thead>

              <tbody>
                {records.map((record) => (
                  <tr key={record.id}>
                    {isManager && (
                      <td>{record.employee_id ?? "—"}</td>
                    )}
                    <td>{record.attendance_date || "—"}</td>
                    <td>{formatDateTime(record.check_in)}</td>
                    <td>{formatDateTime(record.check_out)}</td>
                    <td>{formatHours(record.working_hours)}</td>
                    <td>{record.status || "—"}</td>
                    <td>{record.shift_name || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
