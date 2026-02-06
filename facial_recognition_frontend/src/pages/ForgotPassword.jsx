import { Link } from "react-router-dom";
import { useState } from "react";
import { supabase } from "../utils/supabaseClient";
import { Mail, ArrowLeft } from "lucide-react";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess(false);
    if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      setError("Please enter a valid email");
      return;
    }
    setLoading(true);
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      });
      if (error) {
        setError(error.message);
      } else {
        setSuccess(true);
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
    },
    header: { textAlign: "center", marginBottom: "2.5rem" },
    brandTitle: { fontSize: "0.875rem", fontWeight: "600", color: "#475569", marginBottom: "0.75rem", letterSpacing: "0.14em", textTransform: "uppercase", fontFamily: FONT },
    title: { fontSize: "2rem", fontWeight: "700", color: "#0f172a", marginBottom: "0.5rem", letterSpacing: "-0.03em", fontFamily: FONT },
    subtitle: { fontSize: "0.95rem", fontWeight: "400", color: "#64748b", lineHeight: "1.6", fontFamily: FONT },
    formContainer: { display: "flex", flexDirection: "column", gap: "1.5rem" },
    formGroup: { display: "flex", flexDirection: "column" },
    label: { fontSize: "0.875rem", fontWeight: "500", color: "#475569", marginBottom: "0.375rem", fontFamily: FONT },
    inputWrapper: { position: "relative", display: "flex", alignItems: "center" },
    inputIcon: { position: "absolute", left: "1rem", width: "1.25rem", height: "1.25rem", color: "#94a3b8" },
    input: {
      width: "100%",
      padding: "0.875rem 1rem 0.875rem 3rem",
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
    errorText: { marginTop: "0.375rem", fontSize: "0.875rem", fontWeight: "500", color: "#ef4444", fontFamily: FONT },
    submitButton: { width: "100%", backgroundColor: "#000", color: "#fff", padding: "0.875rem 1rem", borderRadius: "0.625rem", fontWeight: "600", border: "none", cursor: "pointer", fontSize: "1.0625rem", boxShadow: "0 4px 6px rgba(15,23,42,0.1)", fontFamily: FONT },
    submitButtonDisabled: { opacity: 0.7, cursor: "not-allowed" },
    successContainer: { textAlign: "center", padding: "1rem 0" },
    successIcon: { 
      width: "4rem", 
      height: "4rem", 
      borderRadius: "50%", 
      backgroundColor: "#d1fae5", 
      color: "#065f46", 
      display: "flex", 
      alignItems: "center", 
      justifyContent: "center", 
      fontSize: "2rem", 
      fontWeight: "bold",
      margin: "0 auto 1.5rem"
    },
    successTitle: { fontSize: "1.5rem", fontWeight: "700", color: "#0f172a", marginBottom: "0.75rem", fontFamily: FONT },
    successText: { fontSize: "0.95rem", color: "#64748b", marginBottom: "0.5rem", fontFamily: FONT },
    successSubtext: { fontSize: "0.875rem", color: "#94a3b8", lineHeight: "1.5", fontFamily: FONT },
    footer: { textAlign: "center", marginTop: "2rem" },
    backLink: { 
      display: "inline-flex", 
      alignItems: "center", 
      gap: "0.5rem", 
      fontSize: "0.95rem", 
      fontWeight: "600", 
      color: "#0f172a", 
      textDecoration: "none",
      fontFamily: FONT
    },
  };

  return (
    <div style={styles.container}>
      <div style={styles.contentWrapper}>
        <div style={styles.card}>
          <div style={styles.header}>
            <h1 style={styles.brandTitle}>Port Hunter</h1>
            <h2 style={styles.title}>Reset Password</h2>
            <p style={styles.subtitle}>
              Enter your email and we'll send you a link to reset your password
            </p>
          </div>
          {!success ? (
            <form onSubmit={handleSubmit} style={styles.formContainer}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Email address</label>
                <div style={styles.inputWrapper}>
                  <Mail style={styles.inputIcon} />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value)
                      setError("")
                    }}
                    placeholder="you@example.com"
                    style={{ ...styles.input, ...(error && styles.inputError) }}
                  />
                </div>
                {error && <p style={styles.errorText}>{error}</p>}
              </div>
              <button
                type="submit"
                disabled={loading}
                style={{ ...styles.submitButton, ...(loading && styles.submitButtonDisabled) }}
              >
                {loading ? "Sending..." : "Send Reset Link"}
              </button>
            </form>
          ) : (
            <div style={styles.successContainer}>
              <div style={styles.successIcon}>✓</div>
              <h3 style={styles.successTitle}>Check your email</h3>
              <p style={styles.successText}>
                We've sent a password reset link to <strong>{email}</strong>
              </p>
              <p style={styles.successSubtext}>
                Click the link in the email to reset your password. The link will expire in 1 hour.
              </p>
            </div>
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
