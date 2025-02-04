const express = require('express');
const app = express();

const PORT = process.env.PORT || 3000;
const NAME = process.env.NAME || "Node Example";

app.get('/', (req, res) => {
    res.send('🚀 ¡Hello from ' + NAME + '!');
});

app.listen(PORT, () => {
    console.log(`✅ ${NAME}  listening on port: ${PORT}`);
});