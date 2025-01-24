const path = require('path');
require('dotenv').config({path: path.resolve(__dirname, "../.env")})
const { Pool } = require('pg');

const pool = new Pool({
    database: process.env.DB,
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    port: parseInt(process.env.DB_PORT),
    password: String(process.env.DB_PASSWORD),
});

module.exports = pool;