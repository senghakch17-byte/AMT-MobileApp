const mongoose = require('mongoose');

const notificationReceiptSchema = new mongoose.Schema(
  {
    notificationId: {
      type: mongoose.Schema.Types.ObjectId,
      required: true,
      ref: 'Notification',
      immutable: true,
    },
    userId: { type: String, required: true, trim: true, immutable: true },
    readAt: { type: Date, default: null },
    deletedAt: { type: Date, default: null },
  },
  { timestamps: true },
);

notificationReceiptSchema.index({ notificationId: 1, userId: 1 }, { unique: true });
notificationReceiptSchema.index({ userId: 1, readAt: 1 });
notificationReceiptSchema.index({ userId: 1, deletedAt: 1 });

module.exports = mongoose.model('NotificationReceipt', notificationReceiptSchema);