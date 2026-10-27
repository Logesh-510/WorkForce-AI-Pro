
import { apiRequest } from "./api";

export async function getEmployees() {
  return apiRequest("/api/v1/employees/?skip=0&limit=100");
}

export async function getDepartments() {
  return apiRequest("/api/v1/departments/");
}
