const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const bcrypt = require('bcryptjs');
const connectDB = require('./db');
const Person = require('./person.schema');

async function provisionAdmin() {
  const { ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_MOBILE } = process.env;
  if (!ADMIN_NAME || !ADMIN_EMAIL || !ADMIN_PASSWORD || !ADMIN_MOBILE) {
    throw new Error('Set ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD, and ADMIN_MOBILE');
  }

  await connectDB();
  if (await Person.findOne({ emailid: ADMIN_EMAIL })) throw new Error('Admin email already exists');
  await new Person({
    name: ADMIN_NAME,
    emailid: ADMIN_EMAIL,
    pass: await bcrypt.hash(ADMIN_PASSWORD, 10),
    mobile: ADMIN_MOBILE,
    role: 'admin',
  }).save();
  console.log(`Admin provisioned: ${ADMIN_EMAIL}`);
}

provisionAdmin().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});