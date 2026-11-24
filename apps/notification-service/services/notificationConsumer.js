const { createClient } = require('redis');
const Notification = require('../models/notification.model');
const {
  redisConsumerGroup,
  redisConsumerName,
  redisStreamKey,
  redisUrl,
} = require('../config');
const { createNotification } = require('./templates');
const { allowsDirectDelivery } = require('./preferences');

const publisher = createClient({ url: redisUrl });
const consumer = createClient({ url: redisUrl });
let running = false;

for (const client of [publisher, consumer]) {
  client.on('error', (error) => console.error('[Notification] Redis error:', error.message));
}

async function connect(client) {
  if (!client.isOpen) {
    await client.connect();
  }
}

async function publishNotification(notification) {
  await connect(publisher);
  return publisher.xAdd(redisStreamKey, '*', {
    notification_key: notification.notification_key,
    type: notification.type,
    recipient_id: notification.recipient_id || '',
    recipient_role: notification.recipient_role || '',
    data: JSON.stringify(notification.data || {}),
  });
}

function parseMessage(message) {
  let data = {};
  if (message.data) {
    try {
      data = JSON.parse(message.data);
    } catch (_error) {
      const error = new Error('Notification data is not valid JSON');
      error.name = 'InvalidNotificationMessage';
      throw error;
    }
  }
  return { ...message, data };
}

async function storeMessage(message) {
  let notification;
  try {
    notification = createNotification(parseMessage(message));
  } catch (error) {
    error.name = 'InvalidNotificationMessage';
    throw error;
  }
  try {
    if (!(await allowsDirectDelivery(notification))) return;
    await Notification.create(notification);
  } catch (error) {
    // Redis delivers at least once. A duplicate notification is already stored and can be acknowledged.
    if (error?.code !== 11000) throw error;
  }
}

async function processBatches(batches) {
  for (const batch of batches || []) {
    for (const entry of batch.messages) {
      try {
        await storeMessage(entry.message);
        await consumer.xAck(redisStreamKey, redisConsumerGroup, entry.id);
      } catch (error) {
        if (error.name === 'InvalidNotificationMessage') {
          // Poison messages cannot become valid on retry, so acknowledge them after logging.
          console.error('[Notification] Discarding notification:', entry.id, error.message);
          await consumer.xAck(redisStreamKey, redisConsumerGroup, entry.id);
          continue;
        }
        // Leave transient storage failures pending. They are retried before new stream messages.
        throw error;
      }
    }
  }
}

function hasMessages(batches) {
  return batches?.some((batch) => batch.messages?.length > 0) || false;
}

async function ensureConsumerGroup() {
  try {
    await consumer.xGroupCreate(redisStreamKey, redisConsumerGroup, '0', { MKSTREAM: true });
  } catch (error) {
    if (!error.message.includes('BUSYGROUP')) throw error;
  }
}

async function consume() {
  while (running) {
    try {
      // Retry pending deliveries first; Redis Streams provides at-least-once delivery.
      const pending = await consumer.xReadGroup(
        redisConsumerGroup,
        redisConsumerName,
        [{ key: redisStreamKey, id: '0' }],
        { COUNT: 25 },
      );
      if (hasMessages(pending)) {
        await processBatches(pending);
        continue;
      }

      const batches = await consumer.xReadGroup(
        redisConsumerGroup,
        redisConsumerName,
        [{ key: redisStreamKey, id: '>' }],
        { COUNT: 25, BLOCK: 5000 },
      );

      await processBatches(batches);
    } catch (error) {
      if (running) {
        console.error('[Notification] Redis consumer failed:', error.message);
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
    }
  }
}

async function startConsumer() {
  await connect(consumer);
  await ensureConsumerGroup();
  running = true;
  void consume();
  console.log(`[Notification] Consuming Redis stream ${redisStreamKey}`);
}

async function stopConsumer() {
  running = false;
  await Promise.all([publisher, consumer].map(async (client) => {
    if (client.isOpen) await client.quit();
  }));
}

function redisReady() {
  return consumer.isReady;
}

module.exports = { hasMessages, publishNotification, redisReady, startConsumer, stopConsumer };
