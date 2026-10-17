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
  'event.published': {
    title: 'New event published',
    message: 'A new event has been published.',
  },
  'event.updated': {
    title: 'Event updated',
    message: 'An event you may be interested in was updated.',
  },
};

function createNotification(event) {
  const template = templates[event.type];
  if (!template) {
    throw new Error(`Unsupported notification event type: ${event.type}`);
  }

  const recipientId = typeof event.recipient_id === 'string' ? event.recipient_id.trim() : '';
  const recipientRole = typeof event.recipient_role === 'string' ? event.recipient_role.trim() : '';
  if (!recipientId && !recipientRole) {
    throw new Error('Notification event requires recipient_id or recipient_role');
  }

  return {
    eventId: event.event_id,
    type: event.type,
    recipientId: recipientId || undefined,
    recipientRole: recipientRole || undefined,
    title: template.title,
    message: template.message,
    data: event.data || {},
  };
}

module.exports = { createNotification, templates };
