import React, { useEffect, useState, useSyncExternalStore } from 'react';
import { Button } from './index';

let messages = [];
let nextId = 0;
const listeners = new Set();
const subscribe = listener => { listeners.add(listener); return () => listeners.delete(listener); };
const snapshot = () => messages;
const publish = () => listeners.forEach(listener => listener());
const dismiss = id => { messages = messages.filter(message => message.id !== id); publish(); };
function notify(tone, text) {
  messages = [...messages, { id: ++nextId, tone, text: typeof text === 'string' ? text : 'The operation could not be completed.' }];
  publish();
}
export const toast = {
  success: text => notify('success', text),
  error: text => notify('danger', text),
  warning: text => notify('warning', text),
  info: text => notify('info', text),
};

function Notification({ message }) {
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    if (paused || message.tone === 'danger') return;
    const timeout = setTimeout(() => dismiss(message.id), 5000);
    return () => clearTimeout(timeout);
  }, [message.id, message.tone, paused]);
  return <div className={`bic-alert bic-alert-${message.tone} bic-notification`}
    role={message.tone === 'danger' ? 'alert' : 'status'}
    onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}
    onFocus={() => setPaused(true)} onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget)) setPaused(false); }}>
    <span>{message.text}</span>
    <Button variant="secondary" size="sm" aria-label="Dismiss notification" onClick={() => dismiss(message.id)}>Close</Button>
  </div>;
}
export function Notifications() {
  const notifications = useSyncExternalStore(subscribe, snapshot);
  return <div className="bic-notifications" aria-label="Notifications">
    {notifications.map(message => <Notification key={message.id} message={message} />)}
  </div>;
}
