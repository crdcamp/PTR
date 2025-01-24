const express = require("express");
const app = express();
const cors = require("cors");
const pool = require("./database.js")
const PORT = 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Routes for access to specific tables in db
const routes = {
    house_trades: "/house_trades"
};

// Function to streamline requests
function createGetRoute(route, query) {
    app.get(route, async(req, res) => {
        try {
            const result = await pool.query(query);
            res.json(result.rows);
        } catch (error) {
            console.error(error.message);
        }
    });
}

// Register routes
createGetRoute(routes.house_trades, "SELECT * FROM house_trades");

app.listen(PORT, () => {
    console.log(`server has started on PORT ${PORT}`)
});