const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const connectDB = require('./db');
const app = require('./app');

connectDB();

// Fixed Port: 5002 matches the target in your API Gateway
const PORT = process.env.PORT || 5002;

app.listen(PORT, () => console.log(`Authentication Service running on port ${PORT}`));