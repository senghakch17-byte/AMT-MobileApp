const express = require('express');

const controller = require('../controllers/attendance.controller');
const { authenticate, requireAdmin } = require('../middleware/auth.middleware');

const router = express.Router();

router.get('/health', (req, res) => res.json({ status: 'ok' }));
router.use(authenticate);
router.post('/check-in', controller.checkIn);
router.post('/check-out', controller.checkOut);
router.get('/me', controller.listMine);
router.get('/', requireAdmin, controller.listAll);
router.patch('/:id', requireAdmin, controller.updateAttendance);

module.exports = router;
