const express = require("express");
const app = express();
const cors = require("cors");
const pool = require("./database.js");
const fs = require('fs').promises;
const path = require('path');

const PORT = 5000;

app.use(cors());
app.use(express.json());

const routes = {
    candidates: "/house_data"
};

async function createGetRoute(route, sqlFile) {
    try {
        // Read the SQL query from file
        const query = await fs.readFile(
            path.join(__dirname, sqlFile), 
            'utf8'
        );
        
        app.get(route, async(req, res) => {
            try {
                const result = await pool.query(query);
                res.json(result.rows);
            } catch (error) {
                console.error(error.message);
                res.status(500).json({ error: error.message });
            }
        });
    } catch (error) {
        console.error(`Error reading SQL file: ${error.message}`);
    }
}

createGetRoute(routes.candidates, "upload_csv.sql");

app.listen(PORT, () => { 
    console.log(`server has started on PORT ${PORT}`)
});