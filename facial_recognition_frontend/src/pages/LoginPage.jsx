import { Link } from "react-router-dom";
import { useState } from "react";
import { supabase } from "../utils/supabaseClient";
import { Eye, EyeOff } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function LoginPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [infoMessage, setInfoMessage] = useState("");

  const validateForm = () => {
    const newErrors = {};
    if (!formData.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      newErrors.email = "Please enter a valid email";
    }
    if (!formData.password) {
      newErrors.password = "Password is required";
    }
    return newErrors;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: "" }));
    setInfoMessage("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setInfoMessage("");
    setErrors({});
    const newErrors = validateForm();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: formData.email,
        password: formData.password,
      });
      if (error) {
        if (error.message.includes("Email not confirmed")) {
          setErrors({ general: "Please verify your email before signing in." });
        } else if (error.message.includes("Invalid login credentials")) {
          setErrors({ general: "Invalid email or password" });
        } else {
          setErrors({ general: error.message });
        }
      } else if (data.user && !data.user.email_confirmed_at) {
        setErrors({ general: "Please verify your email before signing in. Check your inbox." });
      } else {
        navigate("/dashboard");
      }
    } catch (err) {
      setErrors({ general: "Something went wrong. Please try again." });
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const FONT = "'Inter', sans-serif";
  const styles = {
    container: {
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      backgroundColor: "#f1f5f9",
      padding: "1.5rem",
      fontFamily: FONT,
    },
    contentWrapper: {
      width: "100%",
      maxWidth: "28rem",
    },
    card: {
      backgroundColor: "#ffffff",
      borderRadius: "1.25rem",
      boxShadow: "0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.1), 0 20px 25px rgba(0,0,0,0.05)",
      padding: "3rem 2.5rem",
      border: "1px solid rgba(226,232,240,0.8)",
      transition: "all 0.4s ease",
    },
    header: { textAlign: "center", marginBottom: "2.5rem" },
    brandTitle: { fontSize: "0.875rem", fontWeight: "600", color: "#475569", marginBottom: "0.75rem", letterSpacing: "0.14em", textTransform: "uppercase", fontFamily: FONT },
    title: { fontSize: "2rem", fontWeight: "700", color: "#0f172a", marginBottom: "0.5rem", letterSpacing: "-0.03em", fontFamily: FONT },
    subtitle: { fontSize: "0.95rem", fontWeight: "400", color: "#64748b", lineHeight: "1.6", maxWidth: "100%", margin: "0 auto", fontFamily: FONT },
    formContainer: { display: "flex", flexDirection: "column", gap: "1.5rem" },
    formGroup: { display: "flex", flexDirection: "column" },
    label: { fontSize: "0.875rem", fontWeight: "500", color: "#475569", marginBottom: "0.375rem", fontFamily: FONT },
    forgotLink: { fontSize: "0.875rem", fontWeight: "500", color: "#0f172a", textDecoration: "none", fontFamily: FONT },
    input: {
      width: "100%",
      padding: "0.875rem 1rem",
      border: "1px solid #e2e8f0",
      borderRadius: "0.625rem",
      fontSize: "1rem",
      outline: "none",
      transition: "all 0.2s ease",
      backgroundColor: "#ffffff",
      color: "#0f172a",
      fontFamily: FONT,
      boxSizing: "border-box",
    },
    inputError: { borderColor: "#ef4444", backgroundColor: "#fffafb" },
    toggleButton: { position: "absolute", top: "50%", right: "0.75rem", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", padding: "0.25rem", display: "flex", alignItems: "center", justifyContent: "center", color: "#94a3b8" },
    toggleIcon: { width: "1.25rem", height: "1.25rem" },
    errorText: { marginTop: "0.375rem", fontSize: "0.875rem", fontWeight: "500", color: "#ef4444", fontFamily: FONT },
    infoText: { marginTop: "0.375rem", fontSize: "0.875rem", fontWeight: "500", color: "#0369a1", fontFamily: FONT },
    submitButton: { width: "100%", backgroundColor: "#000", color: "#fff", padding: "0.875rem 1rem", borderRadius: "0.625rem", fontWeight: "600", border: "none", cursor: "pointer", fontSize: "1.0625rem", marginTop: "0.5rem", boxShadow: "0 4px 6px rgba(15,23,42,0.1)", fontFamily: FONT },
    submitButtonDisabled: { opacity: 0.7, cursor: "not-allowed" },
    footer: { textAlign: "center", fontSize: "0.95rem", color: "#64748b", marginTop: "2.5rem", fontFamily: FONT },
    signupLink: { fontWeight: "600", color: "#0f172a", textDecoration: "none", marginLeft: "0.25rem", fontFamily: FONT },
  };

  return (
    <div style={styles.container}>
      <div style={styles.contentWrapper}>
        <div style={styles.card}>
          <div style={styles.header}>
            <h1 style={styles.brandTitle}>Port Hunter</h1>
            <h2 style={styles.title}>Welcome back</h2>
            <p style={styles.subtitle}>Enter your credentials to access your account</p>
          </div>
          <div style={styles.formContainer}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Email address</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="you@example.com"
                style={{ ...styles.input, ...(errors.email && styles.inputError) }}
              />
              {errors.email && <p style={styles.errorText}>{errors.email}</p>}
            </div>
            <div style={styles.formGroup}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.375rem" }}>
                <label style={styles.label}>Password</label>
                <Link to="/forgot-password" style={styles.forgotLink}>Forgot password?</Link>
              </div>
              <div style={{ position: "relative" }}>
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Enter your password"
                  style={{ ...styles.input, ...(errors.password && styles.inputError), paddingRight: "3rem" }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={styles.toggleButton}
                >
                  {showPassword ? <EyeOff style={styles.toggleIcon} /> : <Eye style={styles.toggleIcon} />}
                </button>
              </div>
              {errors.password && <p style={styles.errorText}>{errors.password}</p>}
            </div>
            {infoMessage && <p style={styles.infoText}>{infoMessage}</p>}
            {errors.general && <p style={styles.errorText}>{errors.general}</p>}
            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading}
              style={{ ...styles.submitButton, ...(loading && styles.submitButtonDisabled) }}
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </div>
          <p style={styles.footer}>
            Don't have an account?{" "}
            <Link to="/register" style={styles.signupLink}>
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
