import React from 'react';
import Notification from './Notification';
import { useNotificationContext } from '../contexts/NotificationContext';

const NotificationContainer: React.FC = () => {
  const { notifications, removeNotification } = useNotificationContext();

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map((notification) => (
        <Notification
          key={notification.id}
          id={notification.id}
          type={notification.type}
          title={notification.title}
          message={notification.message}
          onClose={removeNotification}
          duration={notification.duration}
        />
      ))}
    </div>
  );
};

export default NotificationContainer; 