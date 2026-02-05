import React, { useRef, useState } from 'react';
import Webcam from 'react-webcam';
import toast from 'react-hot-toast';

const POSES = [
  { type: 'center', desc: 'Look straight ahead' },
  { type: 'tilt_down', desc: 'Tilt your head down' },
  { type: 'turn_right', desc: 'Turn your head right' },
  { type: 'turn_left', desc: 'Turn your head left' },
];

export default function LivenessDetection({ onComplete, onError }) {
  const webcamRef = useRef(null);
  const [poseIdx, setPoseIdx] = useState(0);
  const [countdown, setCountdown] = useState(3);
  const [recording, setRecording] = useState(false);
  const [frames, setFrames] = useState([]);
  const [progress, setProgress] = useState([false, false, false, false]);

  const startPose = () => {
    setCountdown(3);
    setRecording(false);
    let cd = 3;
    const cdInterval = setInterval(() => {
      setCountdown(cd);
      cd--;
      if (cd < 0) {
        clearInterval(cdInterval);
        setRecording(true);
        captureFrames();
      }
    }, 1000);
  };

  const captureFrames = () => {
    let poseFrames = [];
    let elapsed = 0;
    const interval = setInterval(() => {
      if (webcamRef.current) {
        const imageSrc = webcamRef.current.getScreenshot();
        poseFrames.push({
          pose_type: POSES[poseIdx].type,
          frame_data: imageSrc,
          timestamp: Date.now(),
        });
      }
      elapsed += 100;
      if (elapsed >= 2000) {
        clearInterval(interval);
        setFrames(prev => [...prev, ...poseFrames]);
        setProgress(prev => {
          const next = [...prev];
          next[poseIdx] = true;
          return next;
        });
        if (poseIdx < POSES.length - 1) {
          setPoseIdx(poseIdx + 1);
          setTimeout(startPose, 500);
        } else {
          onComplete([...frames, ...poseFrames]);
        }
        setRecording(false);
      }
    }, 100);
  };

  React.useEffect(() => {
    if (poseIdx === 0) startPose();
    // eslint-disable-next-line
  }, [poseIdx]);

  return (
    <div className="flex flex-col items-center">
      <div className="mb-4">
        <Webcam
          audio={false}
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          width={640}
          height={480}
          videoConstraints={{ width: 640, height: 480 }}
        />
      </div>
      <div className="text-xl font-bold mb-2">{POSES[poseIdx].desc}</div>
      <div className="flex gap-2 mb-2">
        {progress.map((done, idx) => (
          <span key={idx} className={`w-4 h-4 rounded-full ${done ? 'bg-blue-600' : 'bg-gray-300'}`}></span>
        ))}
      </div>
      <div className="mb-2">
        {recording ? (
          <span className="text-red-600 font-bold">● Recording...</span>
        ) : (
          <span className="text-lg">Countdown: {countdown}</span>
        )}
      </div>
      <div className="mb-2">
        <ul className="text-sm">
          <li>✔ Good lighting</li>
          <li>✔ Remove glasses/hats</li>
          <li>✔ Face camera directly</li>
        </ul>
      </div>
    </div>
  );
}
