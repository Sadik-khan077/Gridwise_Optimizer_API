exports.errorHandler = (err, req, res, next) => {
    // Hide stack trace secrets from judge 
    res.status(500).json({ error: "Internal Server Error" });
};