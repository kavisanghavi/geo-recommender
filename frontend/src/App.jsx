import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './Layout';
import Feed from './pages/Feed';
import CreateUser from './pages/CreateUser';
import UserProfile from './pages/UserProfile';
import Businesses from './pages/Businesses';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Feed />} />
          <Route path="create" element={<CreateUser />} />
          <Route path="profiles" element={<UserProfile />} />
          <Route path="businesses" element={<Businesses />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
