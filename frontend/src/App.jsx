import React from 'react'
import { Routes, Route } from 'react-router-dom'
import PrivateRoute from "./components/ProtectedRoute"
import UnauthenticatedOnly from "./components/UnauthenticatedOnly"
import Login from './pages/Login'

// agent pages
import AgentDashboard from './pages/Agent/AgentDashboard'
import CreateProfile from './pages/Agent/CreateProfile'
import ManageProfile from './pages/Agent/ManageProfiles'
import ViewTransactions from './pages/Agent/ViewTransactions' 

//admin pages
import AdminDashboard from './pages/AdminDashboard';
import CreateUser from './pages/CreateUser';
import ManageUsers from './pages/ManageUsers';
import ViewHistory from './pages/ViewHistory';

import Examplepage from './pages/Examplepage'
import ErrorPage from './pages/ErrorPage' 

function App() {

  return (

    <Routes>
      <Route path="/" element={
            <Login />
        } 
      />

      <Route path="/agent" element={
          <PrivateRoute requiredRole="Agent">
            <AgentDashboard />
          </PrivateRoute>
        }
      />
      <Route path="/agent/create-profile" element={<CreateProfile />} />
      <Route path="/agent/manage-profiles" element={<ManageProfile />} />    
      <Route path="/agent/view-transactions" element={<ViewTransactions />} />

      <Route path="/admin" element={
          <PrivateRoute requiredRole="Admin">
            <AdminDashboard />
          </PrivateRoute>
        } 
      />      
      <Route path="/admin/create-user" element={<CreateUser />} />
      <Route path="/admin/manage-users" element={<ManageUsers />} />
      <Route path="/admin/view-transactions" element={<ViewHistory />} />


      <Route path="/admin/example" element={<Examplepage />} />
      <Route path="*" element={<ErrorPage />} /> {/* 404 Page */}
    </Routes>
  )
}

export default App
