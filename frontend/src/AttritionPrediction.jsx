
import { useState } from "react";
import {
  Activity,
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  LoaderCircle,
  RotateCcw,
  Send,
  ShieldAlert,
} from "lucide-react";
import { apiRequest } from "./services/api";
import "./AttritionPrediction.css";

const initialForm = {
  Age: "30",
  Department: "Research & Development",
  JobRole: "Research Scientist",
  MonthlyIncome: "5000",
  YearsAtCompany: "3",
  JobSatisfaction: "3",
  WorkLifeBalance: "3",
  OverTime: "No",
};

const departments = [
  "Sales",
  "Research & Development",
  "Human Resources",
];

const jobRoles = [
  "Sales Executive",
  "Research Scientist",
  "Laboratory Technician",
  "Manufacturing Director",
  "Healthcare Representative",
  "Manager",
  "Sales Representative",
  "Research Director",
  "Human Resources",
];

function Field({ label, name, value, onChange, children, ...props }) {
  return (
    <label className="prediction-field">
      <span>{label}</span>
      {children || (
        <input
          name={name}
          value={value}
          onChange={onChange}
          required
          {...props}
        />
      )}
    </label>
  );
}

export default function AttritionPrediction() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    const payload = {
      Age: Number(form.Age),
      Department: form.Department,
      JobRole: form.JobRole,
      MonthlyIncome: Number(form.MonthlyIncome),
      YearsAtCompany: Number(form.YearsAtCompany),
      JobSatisfaction: Number(form.JobSatisfaction),
      WorkLifeBalance: Number(form.WorkLifeBalance),
      OverTime: form.OverTime,
    };

    try {
      const data = await apiRequest("/api/v1/predictions/attrition", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setResult(data);
    } catch (err) {
      setError(err.message || "Prediction failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function resetForm() {
    setForm(initialForm);
    setResult(null);
    setError("");
  }

  return (
    <div className="prediction-page">
      <section className="prediction-hero">
        <div className="prediction-hero-icon">
          <BrainCircuit size={25} />
        </div>
        <div>
          <span className="prediction-eyebrow">WORKFORCE INTELLIGENCE</span>
          <h2>Attrition Prediction</h2>
          <p>
            Analyze employee-related factors using your trained machine
            learning model.
          </p>
        </div>
        <span className="prediction-model-status">
          <span /> MODEL READY
        </span>
      </section>

      <div className="prediction-layout">
        <section className="panel prediction-form-panel">
          <div className="prediction-section-heading">
            <div>
              <h3>Employee Assessment</h3>
              <p>Enter the required details to generate a prediction.</p>
            </div>
            <Activity size={21} />
          </div>

          <form onSubmit={handleSubmit}>
            <div className="prediction-form-grid">
              <Field
                label="Age"
                name="Age"
                type="number"
                min="18"
                max="100"
                value={form.Age}
                onChange={handleChange}
              />

              <Field label="Department" name="Department">
                <select
                  name="Department"
                  value={form.Department}
                  onChange={handleChange}
                >
                  {departments.map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </Field>

              <Field label="Job Role" name="JobRole">
                <select
                  name="JobRole"
                  value={form.JobRole}
                  onChange={handleChange}
                >
                  {jobRoles.map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </Field>

              <Field
                label="Monthly Income"
                name="MonthlyIncome"
                type="number"
                min="0"
                max="10000000"
                step="0.01"
                value={form.MonthlyIncome}
                onChange={handleChange}
              />

              <Field
                label="Years at Company"
                name="YearsAtCompany"
                type="number"
                min="0"
                max="80"
                value={form.YearsAtCompany}
                onChange={handleChange}
              />

              <Field label="Job Satisfaction" name="JobSatisfaction">
                <select
                  name="JobSatisfaction"
                  value={form.JobSatisfaction}
                  onChange={handleChange}
                >
                  <option value="1">1 — Low</option>
                  <option value="2">2 — Medium</option>
                  <option value="3">3 — High</option>
                  <option value="4">4 — Very High</option>
                </select>
              </Field>

              <Field label="Work-Life Balance" name="WorkLifeBalance">
                <select
                  name="WorkLifeBalance"
                  value={form.WorkLifeBalance}
                  onChange={handleChange}
                >
                  <option value="1">1 — Poor</option>
                  <option value="2">2 — Fair</option>
                  <option value="3">3 — Good</option>
                  <option value="4">4 — Excellent</option>
                </select>
              </Field>

              <Field label="Overtime" name="OverTime">
                <select
                  name="OverTime"
                  value={form.OverTime}
                  onChange={handleChange}
                >
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                </select>
              </Field>
            </div>

            {error && (
              <div className="prediction-error" role="alert">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            <div className="prediction-actions">
              <button
                type="button"
                className="prediction-reset-btn"
                onClick={resetForm}
                disabled={loading}
              >
                <RotateCcw size={16} /> Reset
              </button>
              <button
                type="submit"
                className="prediction-submit-btn"
                disabled={loading}
              >
                {loading ? (
                  <><LoaderCircle size={17} className="prediction-spinner" /> Analyzing...</>
                ) : (
                  <><Send size={16} /> Generate Prediction</>
                )}
              </button>
            </div>
          </form>
        </section>

        <section className="panel prediction-result-panel">
          <div className="prediction-section-heading">
            <div>
              <h3>Prediction Results</h3>
              <p>Model output and estimated risk.</p>
            </div>
            <ShieldAlert size={21} />
          </div>

          {!result ? (
            <div className="prediction-empty">
              <div className="prediction-empty-icon">
                <BrainCircuit size={32} />
              </div>
              <h4>Awaiting Assessment</h4>
              <p>
                Complete the employee assessment and select Generate
                Prediction to see the model output here.
              </p>
            </div>
          ) : (
            <div className="prediction-result-content">
              <div className={`prediction-risk risk-${result.risk_level.toLowerCase()}`}>
                <span className="prediction-risk-label">PREDICTED RISK</span>
                <strong>{result.risk_level}</strong>
              </div>

              <div className="prediction-probability">
                <div>
                  <span>Attrition Probability</span>
                  <strong>
                    {(result.attrition_probability * 100).toFixed(1)}%
                  </strong>
                </div>
                <div className="prediction-progress">
                  <span
                    style={{
                      width: `${Math.min(100, Math.max(0, result.attrition_probability * 100))}%`,
                    }}
                  />
                </div>
              </div>

              <div className="prediction-classification">
                {result.prediction === "Yes" ? (
                  <AlertCircle size={19} />
                ) : (
                  <CheckCircle2 size={19} />
                )}
                <div>
                  <strong>
                    {result.prediction === "Yes"
                      ? "Attrition predicted"
                      : "Attrition not predicted"}
                  </strong>
                  <p>Model: {result.model}</p>
                </div>
              </div>

              <div className="prediction-disclaimer">
                <ShieldAlert size={17} />
                <p>{result.disclaimer}</p>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
