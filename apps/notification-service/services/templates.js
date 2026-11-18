const templates = {
  'request.approved': {
    title: 'Request approved',
    message: 'Your request has been approved.',
  },
  'request.rejected': {
    title: 'Request rejected',
    message: 'Your request has been rejected.',
  },
  'attendance.absent': {
    title: 'Attendance marked absent',
    message: 'You were marked absent for an attendance session.',
  },
  'attendance.corrected': {
    title: 'Attendance updated',
    message: 'Your attendance record has been corrected.',
  },
  'announcement.published': {
    title: 'New announcement published',
    message: 'A new announcement has been published.',
  },
  'announcement.updated': {
    title: 'Announcement updated',
    message: 'An announcement you may be interested in was updated.',
  },
};

function createNotification(notification) {
  const template = templates[notification.type];
  if (!template) {
    throw new Error(`Unsupported notification type: ${notification.type}`);
  }

  const recipientId = typeof notification.recipient_id === 'string' ? notification.recipient_id.trim() : '';
  const recipientRole = typeof notification.recipient_role === 'string' ? notification.recipient_role.trim() : '';
  if (!recipientId && !recipientRole) {
    throw new Error('Notification requires recipient_id or recipient_role');
  }

  return {
    notificationKey: notification.notification_key,
    type: notification.type,
    recipientId: recipientId || undefined,
    recipientRole: recipientRole || undefined,
    title: template.title,
    message: template.message,
    data: notification.data || {},
  };
}

module.exports = { createNotification, templates };
