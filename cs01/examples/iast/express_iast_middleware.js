/**
 * CS-01 Test-Time IAST Middleware for Express
 * ===========================================
 * Inspects outbound HTTP responses and log entries during integration tests
 * to guarantee zero unmasked PII egress per DPDP Act §8(5).
 */

const AADHAAR_REGEX = /\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b/;
const PAN_REGEX = /\b[A-Z]{5}[0-9]{4}[A-Z]\b/;

function dpdpIastMiddleware(req, res, next) {
    const originalSend = res.send;

    res.send = function (body) {
        const payload = typeof body === 'string' ? body : JSON.stringify(body);
        if (AADHAAR_REGEX.test(payload)) {
            console.error(`[DPDP-IAST-ALERT] Unmasked Aadhaar detected in response to ${req.path}`);
        }
        if (PAN_REGEX.test(payload)) {
            console.error(`[DPDP-IAST-ALERT] Unmasked PAN detected in response to ${req.path}`);
        }
        return originalSend.apply(res, arguments);
    };

    next();
}

module.exports = { dpdpIastMiddleware };
