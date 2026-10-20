const express = require('express');
const { internalApiKey } = require('../config');
const eventConsumer = require('../services/eventConsumer');
const { templates } = require('../services/templates');

const router = express.Router();

router.post('/events', async (req, res) => {
  if (!internalApiKey || req.get('x-internal-api-key') !== internalApiKey) {
    return res.status(401).json({ message: 'Invalid internal API key' });
  }

  const { event_id: eventId, type, recipient_id: recipientId, recipient_role: recipientRole, data } = req.body || {};
  if (typeof eventId !== 'string' || !eventId.trim() || !templates[type]) {
    return res.status(400).json({ message: 'event_id and a supported type are required' });
  }
  if ((!recipientId || typeof recipientId !== 'string') && (!recipientRole || typeof recipientRole !== 'string')) {
    return res.status(400).json({ message: 'recipient_id or recipient_role is required' });
  }
  if (data !== undefined && (typeof data !== 'object' || Array.isArray(data) || data === null)) {
    return res.status(400).json({ message: 'data must be an object' });
  }

  const streamId = await eventConsumer.publishEvent({
    event_id: eventId.trim(),
    type,
    recipient_id: recipientId?.trim(),
    recipient_role: recipientRole?.trim(),
    data: data || {},
  });
  res.status(202).json({ status: 'queued', streamId });
});

module.exports = router;
