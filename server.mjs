import express from 'express';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import cors from 'cors';

// 에러 핸들링
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const port = process.env.PORT || 9000;

// 미들웨어 설정
app.use(cors());
app.use(express.json());
app.use(express.static(join(__dirname, 'public')));

// 기본 라우트
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Shrimp Task Manager</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          line-height: 1.6;
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }
        h1 { color: #2c3e50; }
        .status {
          background: #f8f9fa;
          padding: 20px;
          border-radius: 5px;
          margin: 20px 0;
        }
      </style>
    </head>
    <body>
      <h1>🦐 Shrimp Task Manager</h1>
      <div class="status">
        <h2>Status: <span style="color: #27ae60;">Running</span></h2>
        <p>MCP Endpoint: <a href="/mcp">/mcp</a></p>
        <p>Server Time: ${new Date().toISOString()}</p>
      </div>
    </body>
    </html>
  `);
});

// MCP 엔드포인트
app.get('/mcp', (req, res) => {
  res.json({
    name: 'Shrimp Task Manager',
    version: '1.0.0',
    status: 'running',
    timestamp: new Date().toISOString(),
    endpoints: {
      mcp: '/mcp',
      health: '/health'
    }
  });
});

// 헬스 체크 엔드포인트
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 404 핸들러
app.use((req, res) => {
  res.status(404).json({ error: 'Not Found', path: req.path });
});

// 에러 핸들러
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    error: 'Internal Server Error',
    message: err.message
  });
});

// 서버 시작
const server = app.listen(port, '0.0.0.0', () => {
  console.log(`Server is running on port ${port}`);
  console.log(`MCP endpoint: http://localhost:${port}/mcp`);
  console.log(`Health check: http://localhost:${port}/health`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received. Shutting down gracefully...');
  server.close(() => {
    console.log('Server closed.');
    process.exit(0);
  });
});
