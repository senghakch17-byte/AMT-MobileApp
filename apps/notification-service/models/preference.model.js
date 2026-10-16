const mongoose = require('mongoose');

const preferenceSchema = new mongoose.Schema(
  {
    userId: { type: String, required: true, unique: true, trim: true },
    inAppEnabled: { type: Boolean, default: true },
    mutedTypes: { type: [String], default: [] },
  },
  {
    timestamps: true,
    toJSON: {
      versionKey: false,
      transform: (_doc, result) => {
        result.id = result._id.toString();
        delete result._id;
        return result;
      },
    },
  },
);

module.exports = mongoose.model('NotificationPreference', preferenceSchema);
