import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
// 1. React Router-ah import pannunga
import { useNavigate } from "react-router-dom";
import {
    ArrowLeft, ShieldCheck, Scan,
    RefreshCw, Loader2
} from "lucide-react";

export default function ExistingFace({ onBack }) {
    // 2. useNavigate hook-ai initialize pannunga
    const navigate = useNavigate();

    // Logic to handle back navigation (either via prop or router)
    const handleBack = () => {
        if (onBack) {
            onBack();
        } else {
            navigate("/");
        }
    };

    const [isScanning, setIsScanning] = useState(false);
    const [scanComplete, setScanComplete] = useState(false);
    const [stream, setStream] = useState(null);
    const [error, setError] = useState(null);
    const videoRef = useRef(null);

    const startCamera = async () => {
        try {
            setError(null);
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "user" }
            });
            setStream(mediaStream);
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }
        } catch (err) {
            setError("Camera access denied.");
        }
    };

    const stopCamera = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
    };

    /* New Verify Face Logic */
    const handleVerifyFace = async () => {
        if (!videoRef.current) return;

        setIsScanning(true);
        setError(null);

        // 1. Capture Image
        const canvas = document.createElement("canvas");
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        canvas.getContext("2d").drawImage(videoRef.current, 0, 0);

        // 2. Convert to Blob
        canvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append("image", blob, "face_scan.jpg");

            try {
                // 3. Send to Backend
                const response = await fetch("http://127.0.0.1:8000/api/verify-face/", {
                    method: "POST",
                    body: formData,
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    setScanComplete(true);
                    stopCamera();
                    // Optional: Show employee details? For now just verify.
                    setTimeout(() => navigate("/dashboard"), 1500);
                } else {
                    setError(data.error || "Verification failed. Try again.");
                    setIsScanning(false);
                }
            } catch (err) {
                setError("Network error connecting to server.");
                setIsScanning(false);
            }
        }, "image/jpeg");
    };

    useEffect(() => {
        startCamera();
        return () => stopCamera();
    }, []);

    return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="w-full max-w-[400px] bg-gray-100 rounded-[40px] shadow-[20px_20px_60px_#bebebe,-20px_-20px_60px_#ffffff] p-8">

                <div className="flex items-center justify-between mb-8">
                    {/* Back click panna home-ku poga navigate("/") kudunga */}
                    <button onClick={handleBack} className="p-3 rounded-2xl bg-gray-100 shadow-[4px_4px_10px_#b8b9be]">
                        <ArrowLeft size={20} />
                    </button>
                    <div className="text-right">
                        <h2 className="text-xl font-black text-gray-700">Identity Scan</h2>
                        <p className="text-[10px] font-bold text-blue-500 uppercase">Live Bio-Auth</p>
                    </div>
                </div>

                <div className="relative aspect-square rounded-[32px] bg-black overflow-hidden border-[6px] border-white mb-8">
                    {!scanComplete && <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover scale-x-[-1]" />}
                    {isScanning && (
                        <motion.div
                            initial={{ top: "0%" }} animate={{ top: "100%" }} transition={{ duration: 2, repeat: Infinity }}
                            className="absolute left-0 right-0 h-1 bg-blue-400 shadow-[0_0_15px_#3b82f6] z-10"
                        />
                    )}
                    <AnimatePresence>
                        {scanComplete && (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="absolute inset-0 flex flex-col items-center justify-center bg-green-500 text-white z-20">
                                <ShieldCheck size={80} />
                                <p className="text-lg font-bold mt-4">VERIFIED</p>
                            </motion.div>
                        )}

                        {/* Error Overlay */}
                        {error && (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="absolute inset-0 flex flex-col items-center justify-center bg-red-500/80 text-white z-20 backdrop-blur-sm p-4 text-center">
                                <p className="font-bold">{error}</p>
                                <button onClick={() => setError(null)} className="mt-4 px-4 py-2 bg-white text-red-500 rounded-full text-xs font-bold">Retry</button>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                <div className="space-y-4">
                    {!isScanning && !scanComplete && (
                        <button onClick={handleVerifyFace} className="w-full py-5 rounded-2xl bg-blue-600 text-white font-bold flex items-center justify-center gap-3 shadow-lg active:scale-95 transition-transform">
                            <Scan size={20} /> Start Verification
                        </button>
                    )}
                    {isScanning && (
                        <div className="w-full py-5 rounded-2xl bg-gray-200 text-gray-500 font-bold flex items-center justify-center gap-3">
                            <Loader2 className="animate-spin" /> Verifying...
                        </div>
                    )}
                    {scanComplete && (
                        <button
                            onClick={() => navigate("/dashboard")}
                            className="w-full py-5 rounded-2xl bg-white border text-gray-700 font-bold flex items-center justify-center gap-3 shadow-md hover:bg-gray-50"
                        >
                            <RefreshCw size={18} /> Continue to Dashboard
                        </button>
                    )}
                </div>
            </motion.div>
        </div>
    );
}
