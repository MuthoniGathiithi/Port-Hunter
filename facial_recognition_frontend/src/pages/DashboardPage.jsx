import React, { useEffect, useState } from 'react';
import { unitsAPI } from '../utils/api.js';
import toast from 'react-hot-toast';
import AttendanceCapture from '../components/AttendanceCapture.jsx';
import AttendanceReport from '../components/AttendanceReport.jsx';
import { useAuthStore } from '../store/authStore.js';
import { useNavigate } from 'react-router-dom';
import AttendanceSessions from '../components/AttendanceSessions.jsx';

export default function DashboardPage() {
  const { logout } = useAuthStore();
  const navigate = useNavigate();
  const [units, setUnits] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [unitName, setUnitName] = useState('');
  const [unitCode, setUnitCode] = useState('');
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [attendanceResults, setAttendanceResults] = useState(null);
  const [showSessions, setShowSessions] = useState(false);
  const [sessionsUnitId, setSessionsUnitId] = useState(null);

  useEffect(() => {
    unitsAPI.getAll()
      .then(res => setUnits(res.data))
      .catch(() => setUnits([]));
  }, []);

  const handleCreateUnit = async (e) => {
    e.preventDefault();
    try {
      await unitsAPI.create({ unit_name: unitName, unit_code: unitCode });
      toast.success('Unit created!');
      setShowModal(false);
      setUnitName('');
      setUnitCode('');
      unitsAPI.getAll().then(res => setUnits(res.data));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create unit');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <nav className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button
          className="btn-secondary"
          onClick={() => {
            logout();
            navigate('/login');
          }}
        >
          Logout
        </button>
      </nav>
      <button className="btn-primary mb-4" onClick={() => setShowModal(true)}>Create Unit</button>
      {units.length === 0 ? (
        <div className="card">No units yet. Create your first unit!</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {units.map(unit => (
            <div key={unit.id} className="card">
              <div className="font-bold text-lg">{unit.unit_name} ({unit.unit_code})</div>
              <div>Students: {unit.student_count}</div>
              <div>Sessions: {unit.session_count}</div>
              <div className="mt-2">
                <span className="text-xs">Registration Link:</span>
                <input className="input-field" value={`${window.location.origin}/student-register/${unit.registration_token}`} readOnly />
                <button className="btn-secondary mt-1" onClick={() => navigator.clipboard.writeText(`${window.location.origin}/student-register/${unit.registration_token}`)}>Copy</button>
              </div>
              <button className="btn-primary mt-2" onClick={() => setSelectedUnit(unit)}>Take Attendance</button>
              <button
                className="btn-secondary mt-2"
                onClick={() => {
                  setSessionsUnitId(unit.id);
                  setShowSessions(true);
                }}
              >
                View Sessions
              </button>
            </div>
          ))}
        </div>
      )}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
          <form className="card w-full max-w-md" onSubmit={handleCreateUnit}>
            <h2 className="text-xl font-bold mb-4">Create Unit</h2>
            <input className="input-field mb-3" type="text" placeholder="Unit Name" value={unitName} onChange={e => setUnitName(e.target.value)} required />
            <input className="input-field mb-3" type="text" placeholder="Unit Code" value={unitCode} onChange={e => setUnitCode(e.target.value)} required />
            <button className="btn-primary w-full mb-2" type="submit">Create</button>
            <button className="btn-secondary w-full" type="button" onClick={() => setShowModal(false)}>Cancel</button>
          </form>
        </div>
      )}
      {selectedUnit && (
        <AttendanceCapture unitId={selectedUnit.id} onComplete={setAttendanceResults} onCancel={() => setSelectedUnit(null)} />
      )}
      {attendanceResults && (
        <AttendanceReport sessionData={attendanceResults} onClose={() => setAttendanceResults(null)} />
      )}
      {showSessions && (
        <AttendanceSessions
          unitId={sessionsUnitId}
          onClose={() => setShowSessions(false)}
          onSelectSession={async (id) => {
            try {
              const { attendanceAPI } = await import('../utils/api.js');
              const res = await attendanceAPI.getSessionDetails(id);
              setAttendanceResults(res.data);
              setShowSessions(false);
            } catch {
              toast.error('Failed to load session details');
            }
          }}
        />
      )}
    </div>
  );
}
