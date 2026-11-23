const express = require('express');
const app = express();
app.use(express.json());

app.post('/api/contact', (req, res) => {
    const { email, message } = req.body;
    console.log("Contact submission received");
    res.json({ status: "received" });
});

module.exports = app;
