import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

// Components Import
import BranchSelection from "./components/BranchSelection";
import { ParkingDashboard } from "./components/ParkingDashboard";
import { MonthlyPassForm } from "./components/MonthlyPassForm";
import { YearlyPassForm } from "./components/YearlyPassForm";
import NewEmployee from "./components/NewEmployee";
import ExistingFace from "./components/ExistingFace";

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          {/* Main Landing / Home Page */}
          <Route path="/" element={<BranchSelection />} />

          {/* Registration Pages */}
          <Route path="/new-employee" element={<NewEmployee />} />
          <Route path="/monthly-pass" element={<MonthlyPassForm />} />
          <Route path="/yearly-pass" element={<YearlyPassForm />} />

          {/* Authentication Step: Face Recognition */}
          <Route path="/existing-face" element={<ExistingFace />} />

          {/* Final Destination: Parking Dashboard */}
          <Route path="/dashboard" element={<ParkingDashboard />} />

          {/* Oru velai route thappa iruntha, home page-ku redirect panna: */}
          <Route path="*" element={<BranchSelection />} />
        </Routes>
      </div>
    </Router>
  );
}