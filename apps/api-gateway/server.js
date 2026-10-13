const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const app = require('./app');

const PORT = process.env.PORT || 4000;

app.listen(PORT, () => {
  console.log(`API Gateway Service is running on PORT: ${PORT}`);
});
