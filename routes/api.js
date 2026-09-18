const express = require('express');
const router = express.Router();
const healthController = require('../controllers/healthController');
const optimizationController = require('../controllers/optimizationController');
const { validateOptimizationRequest } = require('../middlewares/requestValidator');

// Challenge mandated endpoints
router.get('/health', healthController.getHealth);
router.post('/optimize-energy', validateOptimizationRequest, optimizationController.optimizeEnergy);

module.exports = router;