const express = require('express');
const cors = require('cors');
const apiRoutes = require('./routes/api');

const app = express();

app.use(cors());
app.use(express.json());

// Routes
app.use('/', apiRoutes);

// Controlled internal error handler to prevent exposing secrets or stack traces[cite: 1]
app.use((err, req, res, next) => {
  console.error(err.message); // Log safely internally
  res.status(500).json({ error: "Internal server error" });
});

module.exports = app;