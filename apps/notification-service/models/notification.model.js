const mongoose = require('mongoose');

const notificationSchema = new mongoose.Schema(
  {
    recipientId: { type: String, trim: true, index: true },
    recipientRole: { type: String, trim: true, index: true },
    eventId: { type: String, required: true, trim: true },
    type: { type: String, required: true, trim: true, index: true },
    title: { type: String, required: true, maxlength: 160 },
    message: { type: String, required: true, maxlength: 1000 },
    data: { type: mongoose.Schema.Types.Mixed, default: {} },
    expiresAt: { type: Date, default: null },
  },
  {
    timestamps: true,
    toJSON: {
      virtuals: true,
      versionKey: false,
      transform: (_doc, result) => {
        result.id = result._id.toString();
        delete result._id;
        return result;
      },
    },
  },
);

notificationSchema.index({ recipientId: 1, eventId: 1 }, {
  unique: true,
  partialFilterExpression: { recipientId: { $type: 'string' } },
});
notificationSchema.index({ recipientRole: 1, eventId: 1 }, {
  unique: true,
  partialFilterExpression: { recipientRole: { $type: 'string' } },
});
notificationSchema.index({ recipientId: 1, createdAt: -1 });
notificationSchema.index({ recipientRole: 1, createdAt: -1 });
notificationSchema.index({ expiresAt: 1 }, { expireAfterSeconds: 0, sparse: true });

module.exports = mongoose.model('Notification', notificationSchema);
