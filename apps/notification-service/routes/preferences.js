const express = require('express');
const NotificationPreference = require('../models/preference.model');
const authenticate = require('../middleware/authenticate');
const { templates } = require('../services/templates');

const router = express.Router();
router.use(authenticate);

router.get('/me', async (req, res) => {
  const preference = await NotificationPreference.findOne({ userId: req.user.id });
  res.json(preference || { userId: req.user.id, inAppEnabled: true, mutedTypes: [] });
});

router.patch('/me', async (req, res) => {
  const { inAppEnabled, mutedTypes } = req.body || {};
  if (inAppEnabled !== undefined && typeof inAppEnabled !== 'boolean') {
    return res.status(400).json({ message: 'inAppEnabled must be a boolean' });
  }
  if (mutedTypes !== undefined) {
    if (!Array.isArray(mutedTypes) || mutedTypes.some((type) => typeof type !== 'string' || !templates[type])) {
      return res.status(400).json({ message: 'mutedTypes must contain supported notification types' });
    }
  }
  if (inAppEnabled === undefined && mutedTypes === undefined) {
    return res.status(400).json({ message: 'Provide inAppEnabled or mutedTypes' });
  }

  const updates = {};
  if (inAppEnabled !== undefined) updates.inAppEnabled = inAppEnabled;
  if (mutedTypes !== undefined) updates.mutedTypes = [...new Set(mutedTypes)];
  const preference = await NotificationPreference.findOneAndUpdate(
    { userId: req.user.id },
    { $set: updates, $setOnInsert: { userId: req.user.id } },
    { new: true, upsert: true, runValidators: true },
  );
  return res.json(preference);
});

module.exports = router;
