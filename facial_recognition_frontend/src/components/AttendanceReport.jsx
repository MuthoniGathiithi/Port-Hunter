import React from 'react';

export default function AttendanceReport({ sessionData, onClose }) {
  const { unit_name, session_date, totals, present = [], absent = [], unknown = [], classroom_photos = [] } = sessionData;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
      <div className="card w-full max-w-2xl overflow-y-auto max-h-screen">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-xl font-bold">Attendance Report</h2>
            <div>{unit_name} | {session_date}</div>
          </div>
          <button className="btn-secondary" onClick={onClose}>Close</button>
        </div>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="card bg-green-100">Present: {totals?.present || 0}</div>
          <div className="card bg-gray-100">Absent: {totals?.absent || 0}</div>
          <div className="card bg-red-100">Unknown: {totals?.unknown || 0}</div>
        </div>
        <div className="mb-4">
          <h3 className="font-bold">Present Students</h3>
          <table className="w-full text-sm">
            <thead><tr><th>Name</th><th>Admission #</th><th>Confidence</th></tr></thead>
            <tbody>
              {present.map(s => (
                <tr key={s.id}><td>{s.full_name}</td><td>{s.admission_number}</td><td>{(s.confidence_score * 100).toFixed(1)}%</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mb-4">
          <h3 className="font-bold">Absent Students</h3>
          <table className="w-full text-sm">
            <thead><tr><th>Name</th><th>Admission #</th></tr></thead>
            <tbody>
              {absent.map(s => (
                <tr key={s.id}><td>{s.full_name}</td><td>{s.admission_number}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mb-4">
          <h3 className="font-bold text-red-600">Unknown Faces</h3>
          <div className="grid grid-cols-4 gap-2">
            {unknown.map(face => (
              <div key={face.id} className="border-4 border-red-500 p-1 relative">
                <img src={face.cropped_face_url} alt="Unknown Face" className="w-32 h-32 object-cover" />
                <span className="absolute top-1 left-1 bg-red-600 text-white text-xs px-2 py-1 rounded">UNKNOWN</span>
                <div className="text-xs text-center mt-1">{(face.confidence_score * 100).toFixed(1)}%</div>
              </div>
            ))}
          </div>
        </div>
        <div className="mb-4">
          <h3 className="font-bold">Classroom Photos</h3>
          <div className="flex gap-2">
            {classroom_photos.map((img, idx) => (
              <img key={idx} src={img} alt={`Classroom ${idx + 1}`} className="w-32 h-24 object-cover rounded" />
            ))}
          </div>
        </div>
        {/* Export to CSV button can be added here */}
      </div>
    </div>
  );
}
