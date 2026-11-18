async function publishNotification(announcement) {
  const baseUrl = process.env.NOTIFICATION_SERVICE_URL;
  const apiKey = process.env.INTERNAL_API_KEY;
  if (!baseUrl || !apiKey) {
    console.warn('[Attendance] Notification announcement skipped: producer configuration is missing');
    return;
  }

  try {
    const response = await fetch(`${baseUrl.replace(/\/$/, '')}/internal/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-internal-api-key': apiKey },
      body: JSON.stringify(announcement),
      signal: AbortSignal.timeout(3000),
    });
    if (!response.ok) console.warn(`[Attendance] Notification announcement was not queued: ${response.status}`);
  } catch (error) {
    console.warn('[Attendance] Notification announcement was not queued:', error.message);
  }
}

module.exports = { publishNotification };
