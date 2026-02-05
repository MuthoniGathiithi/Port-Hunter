import React, { useState } from 'react';
import { authAPI } from '../utils/api.js';
import toast from 'react-hot-toast';
import { Link, useNavigate } from 'react-router-dom';

function validatePassword(password) {
  return password.length >= 8 && /[A-Z]/.test(password) && /\d/.test(password);
}

export default function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validatePassword(password)) {
      toast.error('Password must be at least 8 characters, include an uppercase letter and a digit.');
      return;
    }
    if (password !== confirm) {
      toast.error('Passwords do not match.');
      return;
    }
    try {
      await authAPI.register({ full_name: fullName, email, password });
      toast.success('Registration successful!');
      navigate('/login');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed');
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
      <form className="card w-full max-w-md" onSubmit={handleSubmit}>
        <h2 className="text-2xl font-bold mb-4">Lecturer Registration</h2>
        <input className="input-field mb-3" type="text" placeholder="Full Name" value={fullName} onChange={e => setFullName(e.target.value)} required />
        <input className="input-field mb-3" type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
        <input className="input-field mb-3" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
        <input className="input-field mb-3" type="password" placeholder="Confirm Password" value={confirm} onChange={e => setConfirm(e.target.value)} required />
        <button className="btn-primary w-full mb-2" type="submit">Register</button>
        <div className="text-center">
          <Link to="/login" className="text-blue-600 hover:underline">Login</Link>
        </div>
      </form>
    </div>
  );
}
