import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Theme } from '@carbon/react';
import AppShell from './components/Shell/AppShell';
import DashboardPage from './pages/DashboardPage';
import PatientPage from './pages/PatientPage';
import AuditLogPage from './pages/AuditLogPage';

function App() {
  return (
    <Theme theme="white">
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/patients/:id" element={<PatientPage />} />
            <Route path="/audit" element={<AuditLogPage />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </Theme>
  );
}

export default App;
