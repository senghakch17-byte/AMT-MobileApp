const express = require('express');
const mongoose = require('mongoose');
const Notification = require('../models/notification.model');
const NotificationReceipt = require('../models/notificationReceipt.model');
const authenticate = require('../middleware/authenticate');
const { deliveryFilter } = require('../services/preferences');

const router = express.Router();
router.use(authenticate);

async function accessibleFilter(user) {
  return deliveryFilter(user);
}

function receiptLookup(userId) {
  return {
    $lookup: {
      from: NotificationReceipt.collection.name,
      let: { notificationId: '$_id' },
      pipeline: [
        {
          $match: {
            $expr: {
              $and: [
                { $eq: ['$notificationId', '$$notificationId'] },
                { $eq: ['$userId', userId] },
              ],
            },
          },
        },
      ],
      as: 'receipt',
    },
  };
}

function visibleReceiptStages(userId) {
  return [
    receiptLookup(userId),
    { $set: { receipt: { $first: '$receipt' } } },
    { $match: { $or: [{ 'receipt.deletedAt': null }, { receipt: null }] } },
  ];
}

function readMatch(read) {
  if (read === 'true') return { 'receipt.readAt': { $ne: null } };
  if (read === 'false') return { $or: [{ 'receipt.readAt': null }, { receipt: null }] };
  return null;
}

function responseShape() {
  return {
    $project: {
      _id: 0,
      id: { $toString: '$_id' },
      eventId: 1,
      type: 1,
      title: 1,
      message: 1,
      data: 1,
      createdAt: 1,
      updatedAt: 1,
      expiresAt: 1,
      readAt: '$receipt.readAt',
    },
  };
}

async function findAccessibleNotification(notificationId, user) {
  const [notification] = await Notification.aggregate([
    { $match: { _id: new mongoose.Types.ObjectId(notificationId), ...(await accessibleFilter(user)) } },
    ...visibleReceiptStages(user.id),
    responseShape(),
  ]);
  return notification;
}

router.get('/', async (req, res) => {
  const skip = Math.max(Number.parseInt(req.query.skip, 10) || 0, 0);
  const limit = Math.min(Math.max(Number.parseInt(req.query.limit, 10) || 20, 1), 100);
  const filter = await accessibleFilter(req.user);
  if (req.query.type) filter.type = req.query.type;
  const read = readMatch(req.query.read);

  const pipeline = [
    { $match: filter },
    ...visibleReceiptStages(req.user.id),
  ];
  if (read) pipeline.push({ $match: read });
  pipeline.push({ $sort: { createdAt: -1 } }, { $skip: skip }, { $limit: limit }, responseShape());
  res.json(await Notification.aggregate(pipeline));
});

router.get('/unread-count', async (req, res) => {
  const [result] = await Notification.aggregate([
    { $match: await accessibleFilter(req.user) },
    ...visibleReceiptStages(req.user.id),
    { $match: readMatch('false') },
    { $count: 'unreadCount' },
  ]);
  res.json({ unreadCount: result?.unreadCount || 0 });
});

router.get('/:notificationId', async (req, res) => {
  if (!mongoose.isObjectIdOrHexString(req.params.notificationId)) {
    return res.status(404).json({ message: 'Notification not found' });
  }
  const notification = await findAccessibleNotification(req.params.notificationId, req.user);
  if (!notification) return res.status(404).json({ message: 'Notification not found' });
  return res.json(notification);
});

router.patch('/read-all', async (req, res) => {
  const notifications = await Notification.aggregate([
    { $match: await accessibleFilter(req.user) },
    ...visibleReceiptStages(req.user.id),
    { $match: readMatch('false') },
    { $project: { _id: 1 } },
  ]);
  const now = new Date();
  if (notifications.length) {
    await NotificationReceipt.bulkWrite(notifications.map(({ _id: notificationId }) => ({
      updateOne: {
        filter: { notificationId, userId: req.user.id },
        update: { $set: { readAt: now }, $setOnInsert: { deletedAt: null } },
        upsert: true,
      },
    })));
  }
  res.json({ markedRead: notifications.length });
});

router.patch('/:notificationId/read', async (req, res) => {
  if (!mongoose.isObjectIdOrHexString(req.params.notificationId)) {
    return res.status(404).json({ message: 'Notification not found' });
  }
  const notification = await findAccessibleNotification(req.params.notificationId, req.user);
  if (!notification) return res.status(404).json({ message: 'Notification not found' });
  const receipt = await NotificationReceipt.findOneAndUpdate(
    { notificationId: req.params.notificationId, userId: req.user.id },
    { $set: { readAt: new Date() }, $setOnInsert: { deletedAt: null } },
    { new: true, upsert: true, runValidators: true },
  );
  notification.readAt = receipt.readAt;
  return res.json(notification);
});

router.delete('/:notificationId', async (req, res) => {
  if (!mongoose.isObjectIdOrHexString(req.params.notificationId)) {
    return res.status(404).json({ message: 'Notification not found' });
  }
  const notification = await findAccessibleNotification(req.params.notificationId, req.user);
  if (!notification) return res.status(404).json({ message: 'Notification not found' });
  await NotificationReceipt.findOneAndUpdate(
    { notificationId: req.params.notificationId, userId: req.user.id },
    { $set: { deletedAt: new Date() } },
    { upsert: true, runValidators: true },
  );
  return res.status(204).send();
});

module.exports = router;
