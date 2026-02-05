import React, { useEffect, useState } from 'react';
import { attendanceAPI } from '../utils/api.js';
import toast from 'react-hot-toast';

export default function AttendanceSessions({ unitId, onSelectSession, onClose }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    attendanceAPI
      .listSessions(unitId)
      .then((res) => setSessions(res.data || []))
      .catch(() => {
        toast.error('Failed to load sessions');
        setSessions([]);
      })
      .finally(() => setLoading(false));
  }, [unitId]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
      <div className="card w-full max-w-2xl">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Attendance Sessions</h2>
          <button className="btn-secondary" onClick={onClose}>Close</button>
        </div>
        {loading ? (
          <div className="text-sm">Loading sessions...</div>
        ) : sessions.length === 0 ? (
          <div className="text-sm">No sessions yet.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className="text-left">Unit</th>
                <th className="text-left">Date</th>
                <th className="text-left">Status</th>
                <th className="text-left">Totals</th>
                <th className="text-left">Action</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => (
                <tr key={s.id}>
                  <td>{s.unit_name || s.unit_id}</td>
                  <td>{new Date(s.session_date).toLocaleString()}</td>
                  <td>{s.status}</td>
                  <td>
                    P:{s.totals?.present || 0} / A:{s.totals?.absent || 0} / U:{s.totals?.unknown || 0}
                  </td>
                  <td>
                    <button
                      className="btn-primary"
                      onClick={() => onSelectSession(s.id)}
                      disabled={s.status !== 'completed'}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
