const mongoose = require('mongoose');

const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGO_URI, {
      // Disables strict SSL certificate validation for local/dev or custom CA certificates
      tlsAllowInvalidCertificates: true,
      
      // Forces TLS if your connection string doesn't explicitly specify it
      tls: true,
    });
    console.log(`MongoDB Connected: ${conn.connection.host}`);
  } catch (error) {
    console.error(`Database Connection Error: ${error.message}`);
    process.exit(1);
  }
};

module.exports = connectDB;