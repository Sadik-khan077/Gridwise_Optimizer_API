exports.getHealth = (req, res) => {
    // Required shape from BUP CSE Fest specification
    res.status(200).json({ status: "ok" });
};