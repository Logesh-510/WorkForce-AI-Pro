
import { apiRequest } from "./api";

export async function checkIn(shiftName = "General") {
  return apiRequest("/api/v1/attendance/check-in", {
    method: "POST",
    body: JSON.stringify({ shift_name: shiftName }),
  });
}

export async function checkOut() {
  return apiRequest("/api/v1/attendance/check-out", {
    method: "POST",
  });
}

function buildAttendanceParams({
  startDate,
  endDate,
  employeeId,
  skip = 0,
  limit = 20,
} = {}) {
  const params = new URLSearchParams();

  if (startDate) params.set("start_date", startDate);
  if (endDate) params.set("end_date", endDate);
  if (employeeId != null && employeeId !== "") {
    params.set("employee_id", String(employeeId));
  }

  params.set("skip", String(skip));
  params.set("limit", String(limit));

  return params.toString();
}

export async function getAttendanceHistory(options = {}) {
  const params = buildAttendanceParams(options);

  return apiRequest(
    `/api/v1/attendance/history?${params}`,
    { method: "GET" }
  );
}

export async function getAttendanceManagement(options = {}) {
  const params = buildAttendanceParams(options);

  return apiRequest(
    `/api/v1/attendance/management?${params}`,
    { method: "GET" }
  );
}

export async function updateAttendance(attendanceId, updates) {
  return apiRequest(
    `/api/v1/attendance/management/${attendanceId}`,
    {
      method: "PATCH",
      body: JSON.stringify(updates),
    }
  );
}
