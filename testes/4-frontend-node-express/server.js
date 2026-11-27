const express = require('express');
const path = require('path');

const app = express();
const PORT = 3000;

// Serve todos os arquivos estáticos (HTML, CSS, JS) da pasta 'public'
app.use(express.static(path.join(__dirname, 'public')));

app.listen(PORT, () => {
    console.log(`🚀 Frontend Node.js/Express rodando em: http://localhost:${PORT}`);
});

