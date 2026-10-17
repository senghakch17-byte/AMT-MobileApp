const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const connectDB = require('./db');
const app = require('./app');

connectDB();

// Fixed Port: Set to 5001 to align with your API Gateway configuration
const PORT = process.env.PORT || 5001;
app.listen(PORT, () => console.log(`Register Service running on port ${PORT}`));