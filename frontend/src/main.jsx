import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import { IconContext } from 'react-icons';
import '../../css/bic-tokens.css';
import '../../css/bic-base.css';
import '../../css/bic-layout.css';
import '../../css/bic-components.css';
import '../../css/bic-utilities.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <IconContext.Provider value={{ className: 'bic-icon', attr: { 'aria-hidden': true, focusable: false } }}>
      <App />
    </IconContext.Provider>
  </React.StrictMode>
);
