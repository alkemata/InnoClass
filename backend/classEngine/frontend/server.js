const express = require('express');
const path = require('path');
const compression = require('compression');
const helmet = require('helmet');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(helmet());
app.use(compression());

app.use(express.static(path.join(__dirname, 'dist'), {
  index: false,
  maxAge: '1y',
  setHeaders: (res, path) => {
    if (path.endsWith('index.html')) {
      res.setHeader('Cache-Control', 'no-cache');
    }
  }
}));

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Production server running on http://localhost:${PORT}`);
});
