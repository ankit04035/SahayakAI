import React from 'react';
import ReactDOM from 'react-dom/client';
import { UserProvider } from './context/UserContext';
import App from './App';
import './styles/index.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <UserProvider>
      <App />
    </UserProvider>
  </React.StrictMode>
);
