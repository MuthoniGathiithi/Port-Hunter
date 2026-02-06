import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { supabase } from "../utils/supabaseClient";
import { Lock, Eye, EyeOff, ArrowLeft } from "lucide-react";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => {
    const { data: authListener } = supabase.auth.onAuthStateChange((event) => {
      if (event === "PASSWORD_RECOVERY") {
        setError("");
      }
    });
    return () => {
      authListener?.subscription?.unsubscribe?.();
    };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess(false);
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      const { error } = await supabase.auth.updateUser({ password });
      if (error) {
        setError(error.message);
      } else {
        setSuccess(true);
        setTimeout(() => navigate("/login"), 1500);
      }
    } catch (err) {
      setError("Something went wrong. Please try again.");
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
    contentWrapper: { width: "100%", maxWidth: "28rem" },
    card: {
      backgroundColor: "#ffffff",
      borderRadius: "1.25rem",
      boxShadow: "0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.1), 0 20px 25px rgba(0,0,0,0.05)",
      padding: "3rem 2.5rem",
      border: "1px solid rgba(226,232,240,0.8)",
    },
    header: { textAlign: "center", marginBottom: "2.5rem" },
    brandTitle: { fontSize: "0.875rem", fontWeight: 600, color: "#475569", marginBottom: "0.75rem", letterSpacing: "0.14em", textTransform: "uppercase", fontFamily: FONT },
    title: { fontSize: "2rem", fontWeight: 700, color: "#0f172a", marginBottom: "0.5rem", letterSpacing: "-0.03em", fontFamily: FONT },
    subtitle: { fontSize: "0.95rem", fontWeight: 400, color: "#64748b", lineHeight: "1.6", fontFamily: FONT },
    formContainer: { display: "flex", flexDirection: "column", gap: "1.25rem" },
    formGroup: { display: "flex", flexDirection: "column" },
    label: { fontSize: "0.875rem", fontWeight: 500, color: "#475569", marginBottom: "0.375rem", fontFamily: FONT },
    inputWrapper: { position: "relative", display: "flex", alignItems: "center" },
    inputIcon: { position: "absolute", left: "1rem", width: "1.25rem", height: "1.25rem", color: "#94a3b8" },
    input: {
      width: "100%",
      padding: "0.875rem 3rem 0.875rem 3rem",
      border: "1px solid #e2e8f0",
      borderRadius: "0.625rem",
      fontSize: "1rem",
      outline: "none",
      backgroundColor: "#ffffff",
      color: "#0f172a",
      fontFamily: FONT,
      boxSizing: "border-box",
    },
    inputError: { borderColor: "#ef4444", backgroundColor: "#fffafb" },
    toggleButton: {
      position: "absolute",
      right: "0.75rem",
      background: "none",
      border: "none",
      cursor: "pointer",
      padding: "0.25rem",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "#94a3b8",
    },
    toggleIcon: { width: "1.1rem", height: "1.1rem" },
    errorText: { marginTop: "0.375rem", fontSize: "0.875rem", fontWeight: 500, color: "#ef4444", fontFamily: FONT },
    submitButton: { width: "100%", backgroundColor: "#000", color: "#fff", padding: "0.875rem 1rem", borderRadius: "0.625rem", fontWeight: 700, border: "none", cursor: "pointer", fontSize: "1.0625rem", boxShadow: "0 4px 6px rgba(15,23,42,0.1)", fontFamily: FONT },
    submitButtonDisabled: { opacity: 0.7, cursor: "not-allowed" },
    successMessage: { padding: "0.9rem", backgroundColor: "#d1fae5", color: "#065f46", borderRadius: "0.75rem", fontWeight: 700, textAlign: "center" },
    footer: { textAlign: "center", marginTop: "2rem" },
    backLink: { display: "inline-flex", alignItems: "center", gap: "0.5rem", fontSize: "0.95rem", fontWeight: 600, color: "#0f172a", textDecoration: "none", fontFamily: FONT },
  };

  return (
    <div style={styles.container}>
      <div style={styles.contentWrapper}>
        <div style={styles.card}>
          <div style={styles.header}>
            <h1 style={styles.brandTitle}>Port Hunter</h1>
            <h2 style={styles.title}>Set New Password</h2>
            <p style={styles.subtitle}>Enter a new password for your account.</p>
          </div>
          {success ? (
            <div style={styles.successMessage}>Password updated. Redirecting to sign in...</div>
          ) : (
            <form onSubmit={handleSubmit} style={styles.formContainer}>
              <div style={styles.formGroup}>
                <label style={styles.label}>New password</label>
                <div style={styles.inputWrapper}>
                  <Lock style={styles.inputIcon} />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter new password"
                    style={{ ...styles.input, ...(error && styles.inputError) }}
                  />
                  <button type="button" onClick={() => setShowPassword((s) => !s)} style={styles.toggleButton}>
                    {showPassword ? <EyeOff style={styles.toggleIcon} /> : <Eye style={styles.toggleIcon} />}
                  </button>
                </div>
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Confirm password</label>
                <div style={styles.inputWrapper}>
                  <Lock style={styles.inputIcon} />
                  <input
                    type={showConfirm ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    style={{ ...styles.input, ...(error && styles.inputError) }}
                  />
                  <button type="button" onClick={() => setShowConfirm((s) => !s)} style={styles.toggleButton}>
                    {showConfirm ? <EyeOff style={styles.toggleIcon} /> : <Eye style={styles.toggleIcon} />}
                  </button>
                </div>
                {error && <p style={styles.errorText}>{error}</p>}
              </div>
              <button type="submit" disabled={loading} style={{ ...styles.submitButton, ...(loading && styles.submitButtonDisabled) }}>
                {loading ? "Updating..." : "Update Password"}
              </button>
            </form>
          )}
          <div style={styles.footer}>
            <Link to="/login" style={styles.backLink}>
              <ArrowLeft size={16} />
              <span>Back to sign in</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
