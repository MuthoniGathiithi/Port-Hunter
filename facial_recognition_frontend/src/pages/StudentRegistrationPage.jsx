import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { registrationAPI } from '../utils/api.js';
import LivenessDetection from '../components/LivenessDetection.jsx';
import toast from 'react-hot-toast';

export default function StudentRegistrationPage() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [unitId, setUnitId] = useState(null);
  const [error, setError] = useState(null);
  const [fullName, setFullName] = useState('');
  const [admissionNumber, setAdmissionNumber] = useState('');
  const [frames, setFrames] = useState([]);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    registrationAPI.verifyToken(token)
      .then(res => {
        if (res.data.valid) {
          setUnitId(res.data.unit_id);
        } else {
          setError(res.data.error || 'Invalid or expired token');
        }
      })
      .catch(() => setError('Invalid or expired token'));
  }, [token]);

  const handleFormSubmit = (e) => {
    e.preventDefault();
    registrationAPI.start({ full_name: fullName, admission_number: admissionNumber, unit_id: unitId })
      .then(() => setStep(3))
      .catch(err => toast.error(err.response?.data?.detail || 'Registration failed'));
  };

  const handleLivenessComplete = async (frames) => {
    setProcessing(true);
    try {
      const res = await registrationAPI.checkLiveness({ frames, unit_id: unitId, admission_number: admissionNumber });
      await registrationAPI.complete({ unit_id: unitId, admission_number: admissionNumber, embeddings: res.data.embeddings });
      toast.success('Registration complete!');
      setStep(4);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Liveness check failed');
      setProcessing(false);
    }
  };

  if (error) return <div className="flex flex-col items-center justify-center min-h-screen"><div className="card">{error}</div></div>;
  if (!unitId) return <div className="flex flex-col items-center justify-center min-h-screen"><div className="card">Verifying token...</div></div>;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
      {step === 1 && (
        <div className="card w-full max-w-md">
          <h2 className="text-2xl font-bold mb-4">Student Registration</h2>
          <form onSubmit={handleFormSubmit}>
            <input className="input-field mb-3" type="text" placeholder="Full Name" value={fullName} onChange={e => setFullName(e.target.value)} required />
            <input className="input-field mb-3" type="text" placeholder="Admission Number" value={admissionNumber} onChange={e => setAdmissionNumber(e.target.value)} required />
            <button className="btn-primary w-full" type="submit">Next</button>
          </form>
        </div>
      )}
      {step === 3 && (
        <LivenessDetection onComplete={handleLivenessComplete} onError={err => toast.error(err)} />
      )}
      {processing && <div className="card mt-6">Processing registration...</div>}
      {step === 4 && (
        <div className="card w-full max-w-md text-center">
          <h2 className="text-2xl font-bold mb-4">Registration Complete!</h2>
          <button className="btn-primary" onClick={() => navigate('/login')}>Go to Login</button>
        </div>
      )}
    </div>
  );
}
