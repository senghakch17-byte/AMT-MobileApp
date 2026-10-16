const NotificationPreference = require('../models/preference.model');

async function getPreference(userId) {
  return NotificationPreference.findOne({ userId });
}

async function deliveryFilter(user) {
  const preference = await getPreference(user.id);
  if (preference?.inAppEnabled === false) return { _id: { $exists: false } };

  const filter = { $or: [{ recipientId: user.id }, { recipientRole: user.role }] };
  if (preference?.mutedTypes.length) filter.type = { $nin: preference.mutedTypes };
  return filter;
}

async function allowsDirectDelivery(notification) {
  if (!notification.recipientId) return true;
  const preference = await getPreference(notification.recipientId);
  return preference?.inAppEnabled !== false && !preference?.mutedTypes.includes(notification.type);
}

module.exports = { allowsDirectDelivery, deliveryFilter, getPreference };
