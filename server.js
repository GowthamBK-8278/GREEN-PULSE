const express = require('express');
const twilio = require('twilio');
const app = express();
app.use(express.json());

// Replace with your Twilio Credentials
const client = new twilio('AC_YOUR_SID', 'YOUR_AUTH_TOKEN');
const tempOtpStore = {}; // In production, use Redis for 5-min expiration

// ROUTE: Send OTP
app.post('/api/send-otp', (req, res) => {
    const { phone } = req.body;
    const otp = Math.floor(100000 + Math.random() * 900000).toString();
    
    tempOtpStore[phone] = otp; // Save code to verify later

    client.messages.create({
        body: `Your FarmGate code is ${otp}. Do not share it.`,
        from: '+1234567890', // Your Twilio Number
        to: phone
    })
    .then(() => res.json({ success: true }))
    .catch(err => res.json({ success: false, error: err.message }));
});

// ROUTE: Verify OTP
app.post('/api/verify-otp', (req, res) => {
    const { phone, otp } = req.body;
    if (tempOtpStore[phone] === otp) {
        delete tempOtpStore[phone]; // Clear after use
        res.json({ success: true });
    } else {
        res.json({ success: false });
    }
});

app.listen(3000, () => console.log("Server running on port 3000"));

app.listen(3000, () => console.log('FarmGate Backend running on port 3000'));
app.post('/finalize-registration', (req, res) => {
    const { otp, userData } = req.body;
    const phoneNumber = userData.phone;

    // MANDATORY CHECK: Does OTP match the phone?
    if (otpStorage[phoneNumber] === otp) {
        // Save to your Database (e.g., MongoDB/MySQL)
        // db.farmers.save(userData); 
        
        delete otpStorage[phoneNumber]; // Clean up
        res.status(200).send({ success: true, message: 'Account Created!' });
    } else {
        res.status(401).send({ success: false, message: 'OTP mismatch.' });
    }
});