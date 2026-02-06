import React from "react";
import { Link, useNavigate } from "react-router-dom";

export default function LandingPage() {
  const navigate = useNavigate();
  return (
    <div
      style={{
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        backgroundColor: "#000",
        minHeight: "100vh",
        margin: 0,
        padding: 0,
      }}
    >
      {/* Animated grid lines */}
      <style>{`
        @keyframes blobPulse {
          0% { transform: translate(-50%,-40%) scale(1); opacity:0.9 }
          50% { transform: translate(-50%,-40%) scale(1.05); opacity:0.95 }
          100% { transform: translate(-50%,-40%) scale(1); opacity:0.9 }
        }
        .hero-section { padding: 120px 24px 80px; text-align: center; background: transparent; position: relative; overflow: hidden; }
        .hero-title { font-size: 3rem; font-weight: 800; color: #fff; margin: 0 0 24px 0; line-height: 1.1; letter-spacing: -2px; }
        .hero-subtitle { font-size: 1.25rem; color: #e5e7eb; margin: 0 0 40px 0; font-weight: 400; line-height: 1.6; max-width: 700px; margin-left: auto; margin-right: auto; }
        .hero-buttons { display: flex; gap: 16px; justify-content: center; margin-bottom: 60px; flex-wrap: wrap; }
        .btn-primary, .btn-secondary { padding: 14px 36px; border-radius: 8px; font-size: 1rem; font-weight: 600; border: none; cursor: pointer; transition: all 0.2s; }
        .btn-primary { background: #fff; color: #000; }
        .btn-primary:hover { background: #e5e7eb; }
        .btn-secondary { background: #1f2937; color: #fff; }
        .btn-secondary:hover { background: #374151; }
        .mockup-grid { background: rgba(255,255,255,0.01); border: 1px solid #222; border-radius: 16px; padding: 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.18); display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 32px; }
        @media (max-width: 1024px) { .hero-title { font-size: 2.2rem; } .mockup-grid { grid-template-columns: 1fr; padding: 20px; } }
        @media (max-width: 640px) { .hero-title { font-size: 1.5rem; } .mockup-grid { padding: 10px; gap: 10px; } }
      `}</style>

      <section className="hero-section">
        {/* Grid lines background */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundImage:
              "linear-gradient(#222 1px, transparent 1px), linear-gradient(90deg, #222 1px, transparent 1px)",
            backgroundSize: "40px 40px",
            opacity: 0.4,
            zIndex: 0,
          }}
        ></div>

        {/* Hero content */}
        <div style={{ maxWidth: "900px", margin: "0 auto", position: "relative", zIndex: 1 }}>
          <h1 className="hero-title">Identi Facial Recognition</h1>
          <p className="hero-subtitle">
            Automated attendance and registration using facial recognition and liveness detection.
          </p>
          <div className="hero-buttons">
            <Link to="/login" className="btn-primary">Lecturer Login</Link>
            <Link to="/register" className="btn-secondary">Lecturer Register</Link>
          </div>
          {/* Mockup grid for future content */}
          <div className="mockup-grid">
            <div style={{ color: '#fff', opacity: 0.7, textAlign: 'center' }}>Fast & Secure Attendance</div>
            <div style={{ color: '#fff', opacity: 0.7, textAlign: 'center' }}>AI-Powered Face Recognition</div>
            <div style={{ color: '#fff', opacity: 0.7, textAlign: 'center' }}>Liveness Detection</div>
          </div>
        </div>
      </section>
    </div>
  );
}
