import React, { useRef, useState } from 'react';
import Webcam from 'react-webcam';
import { attendanceAPI } from '../utils/api.js';
import toast from 'react-hot-toast';
import { compressImage } from '../utils/image.js';

export default function AttendanceCapture({ unitId, onComplete, onCancel }) {
  const webcamRef = useRef(null);
  const [photos, setPhotos] = useState([]);
  const [processing, setProcessing] = useState(false);

  const handleCapture = async () => {
    if (webcamRef.current) {
      let img = webcamRef.current.getScreenshot();
      img = await compressImage(img, 1280);
      setPhotos([...photos, img]);
    }
  };

  const handleRetake = () => {
    setPhotos(photos.slice(0, -1));
  };

  const handleSubmit = async () => {
    setProcessing(true);
    try {
      const res = await attendanceAPI.create({ unit_id: unitId, classroom_photos: photos });
      const sessionId = res.data.id;
      const poll = setInterval(async () => {
        const statusRes = await attendanceAPI.getStatus(sessionId);
        if (statusRes.data.status === 'completed') {
          clearInterval(poll);
          const details = await attendanceAPI.getSessionDetails(sessionId);
          onComplete(details.data);
        }
      }, 2000);
    } catch (err) {
      toast.error('Failed to submit attendance');
      setProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
      <div className="card w-full max-w-lg">
        <h2 className="text-xl font-bold mb-4">Capture Classroom Photos</h2>
        <Webcam
          audio={false}
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          width={640}
          height={480}
        />
        <div className="flex gap-2 mt-4">
          <button className="btn-primary" onClick={handleCapture}>Capture Photo</button>
          <button className="btn-secondary" onClick={handleRetake} disabled={photos.length === 0}>Retake Last</button>
        </div>
        <div className="mt-2">Photo {photos.length + 1} of 3</div>
        <div className="flex gap-2 mt-2">
          {photos.map((img, idx) => (
            <img key={idx} src={img} alt={`Photo ${idx + 1}`} className="w-24 h-16 object-cover rounded" />
          ))}
        </div>
        <button className="btn-primary w-full mt-4" onClick={handleSubmit} disabled={photos.length < 2 || processing}>Submit</button>
        <button className="btn-secondary w-full mt-2" onClick={onCancel}>Cancel</button>
        {processing && <div className="mt-2">Processing attendance...</div>}
      </div>
    </div>
  );
}
