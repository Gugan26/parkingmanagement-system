import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  User, Mail, Hash, ArrowLeft, CheckCircle,
  ChevronRight, Phone, Fingerprint, Loader2, Camera, VideoOff
} from "lucide-react";

export default function NewEmployee() {
  const navigate = useNavigate();
  const videoRef = useRef(null);

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [stream, setStream] = useState(null);

  // Photo capture pannurathukana States
  const [photo, setPhoto] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    employee_id: "",
    age: "",
    vehicle_number: "",
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // Webcam Start
  const startWebcam = async () => {
    setPreviewUrl(null); // Retake pannum pothu preview clear panna
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      });
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setStream(mediaStream);
    } catch (err) {
      alert("Camera access denied or not found.");
    }
  };

  // Photo Capture Logic
  const capturePhoto = () => {
    if (videoRef.current) {
      const canvas = document.createElement("canvas");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(videoRef.current, 0, 0);

      canvas.toBlob((blob) => {
        setPhoto(blob); // Database-ku anupa (File)
        setPreviewUrl(URL.createObjectURL(blob)); // UI-la preview kaata
        stopWebcam();
      }, "image/jpeg");
    }
  };

  const stopWebcam = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  };

  const nextStep = () => {
    stopWebcam();
    setStep((p) => p + 1);
  };

  const prevStep = () => {
    stopWebcam();
    setStep((p) => p - 1);
  };

  // Final Submit with Image
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // FormData object creation
    const data = new FormData();
    Object.keys(formData).forEach((key) => {
      data.append(key, formData[key]);
    });

    // Capture panna photo-va add panrom
    if (photo) {
      data.append("profile_pic", photo, "employee_photo.jpg");
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/api/new-employee/", {
        method: "POST",
        // Note: Content-Type header poda koodathu
        body: data,
      });

      if (response.ok) {
        navigate("/dashboard");
      } else {
        alert("Submission failed");
      }
    } catch (error) {
      alert("Server error!");
    } finally {
      setLoading(false);
    }
  };

  // Styles
  const inputStyle = "w-full px-4 py-2.5 rounded-xl bg-gray-100 border border-gray-200 focus:ring-2 focus:ring-yellow-500 transition-all outline-none text-sm text-gray-700 font-medium shadow-inner";
  const labelStyle = "flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1.5 ml-1";
  const neumorphicCard = "w-full max-w-[380px] bg-gray-100 rounded-[32px] shadow-[15px_15px_40px_#cbcbcb,-15px_-15px_40px_#ffffff] p-6";

  return (
    <div className="min-h-screen bg-gray-100 p-4 flex justify-center items-center font-sans">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className={neumorphicCard}>

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <button
            type="button"
            onClick={() => step > 1 ? prevStep() : navigate(-1)}
            className="p-2.5 rounded-xl bg-gray-100 shadow-[4px_4px_10px_#b8b9be,-4px_-4px_10px_#ffffff] hover:text-yellow-600 active:shadow-inner transition-all"
          >
            <ArrowLeft size={18} />
          </button>
          <div className="text-right">
            <p className="text-[9px] font-black uppercase tracking-widest text-yellow-600">Step {step} of 3</p>
            <h2 className="text-lg font-extrabold text-gray-800 tracking-tight">Onboarding</h2>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {[1, 2, 3].map((s) => (
            <div key={s} className={`h-1.5 rounded-full transition-all duration-500 ${step === s ? "w-8 bg-yellow-400" : "w-1.5 bg-gray-300"}`} />
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          <AnimatePresence mode="wait">
            {/* STEP 1: Personal Info */}
            {step === 1 && (
              <motion.div key="step1" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="space-y-4">
                <div>
                  <label className={labelStyle}><User size={12} /> Name</label>
                  <input name="name" value={formData.name} onChange={handleChange} placeholder="John Doe" required className={inputStyle} />
                </div>
                <div>
                  <label className={labelStyle}><Mail size={12} /> Email</label>
                  <input type="email" name="email" value={formData.email} onChange={handleChange} placeholder="john@company.com" required className={inputStyle} />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={labelStyle}><Phone size={12} /> Phone</label>
                    <input type="tel" name="phone" value={formData.phone} onChange={handleChange} placeholder="987..." required className={inputStyle} />
                  </div>
                  <div>
                    <label className={labelStyle}><Fingerprint size={12} /> Adhar Number</label>
                    <input name="employee_id" value={formData.employee_id} onChange={handleChange} placeholder="E-01" required className={inputStyle} />
                  </div>
                </div>
                <button type="button" onClick={nextStep} className="w-full py-3.5 mt-2 rounded-xl bg-gray-800 text-white text-sm font-bold flex items-center justify-center gap-2 hover:bg-black transition-all shadow-lg">
                  Next: Verification <ChevronRight size={16} />
                </button>
              </motion.div>
            )}

            {/* STEP 2: Identity Verification (Corrected with Capture) */}
            {step === 2 && (
              <motion.div key="step2" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="space-y-4">
                <label className={labelStyle}><Camera size={12} /> Identity Scan</label>
                <div className="relative overflow-hidden rounded-2xl bg-black aspect-video flex items-center justify-center border-4 border-white shadow-inner">
                  {previewUrl ? (
                    <img src={previewUrl} className="w-full h-full object-cover" alt="Captured" />
                  ) : (
                    <>
                      {!stream && (
                        <div className="text-center">
                          <p className="text-gray-500 text-[10px] uppercase font-bold px-4">Camera Preview Off</p>
                        </div>
                      )}
                      <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
                    </>
                  )}
                  {stream && <div className="absolute inset-0 border-2 border-dashed border-yellow-400/30 rounded-2xl animate-pulse" />}
                </div>

                <div className="flex gap-3">
                  {!stream && !previewUrl ? (
                    <button type="button" onClick={startWebcam} className="flex-1 py-3 rounded-xl bg-white border border-gray-200 text-gray-700 text-xs font-bold flex items-center justify-center gap-2 shadow-sm">
                      <Camera size={14} /> Open Camera
                    </button>
                  ) : stream ? (
                    <button type="button" onClick={capturePhoto} className="flex-1 py-3 rounded-xl bg-yellow-400 text-gray-900 text-xs font-bold flex items-center justify-center gap-2 shadow-sm">
                      <CheckCircle size={14} /> Capture Photo
                    </button>
                  ) : (
                    <button type="button" onClick={startWebcam} className="flex-1 py-3 rounded-xl bg-gray-200 text-gray-700 text-xs font-bold flex items-center justify-center gap-2 shadow-sm">
                      <VideoOff size={14} /> Retake
                    </button>
                  )}
                </div>

                <button
                  type="button"
                  onClick={nextStep}
                  className="w-full py-3.5 mt-2 rounded-xl bg-gray-800 text-white text-sm font-bold flex items-center justify-center gap-2 shadow-lg"
                >
                  Confirm & Continue <ChevronRight size={16} />
                </button>
              </motion.div>
            )}

            {/* STEP 3: Final Info */}
            {step === 3 && (
              <motion.div key="step3" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="space-y-4">
                <div>
                  <label className={labelStyle}>Age</label>
                  <input type="number" name="age" value={formData.age} onChange={handleChange} placeholder="25" required className={inputStyle} />
                </div>
                <div>
                  <label className={labelStyle}><Hash size={12} /> Vehicle No.</label>
                  <input name="vehicle_number" value={formData.vehicle_number} onChange={handleChange} placeholder="TN 01 AB..." required className={inputStyle} />
                </div>

                <div className="pt-2">
                  <button
                    disabled={loading}
                    type="submit"
                    className="w-full py-4 rounded-xl font-black text-xs text-gray-900 uppercase tracking-widest bg-yellow-400 shadow-[0_8px_15px_rgba(250,204,21,0.3)] flex items-center justify-center gap-2 disabled:bg-gray-300"
                  >
                    {loading ? <Loader2 className="animate-spin" size={18} /> : <CheckCircle size={18} />}
                    {loading ? "Processing..." : "Complete Registration"}
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </form>
      </motion.div>
    </div>
  );
}