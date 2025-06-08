import express from 'express';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { createRequire } from 'module';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const require = createRequire(import.meta.url);

const app = express();
const PORT = process.env.PORT || 8000;

// 정적 파일 제공 (public 폴더)
app.use(express.static('public'));

// 기본 라우트
app.get('/', (req, res) => {
  res.send('Shrimp Task Manager MCP Server is running on port ' + PORT);
});

// MCP 엔드포인트 예시
app.get('/mcp', (req, res) => {
  res.json({
    name: 'Shrimp Task Manager',
    version: '1.0.0',
    status: 'running',
    port: PORT
  });
});

// 서버 시작
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
  console.log(`MCP endpoint: http://localhost:${PORT}/mcp`);
});
