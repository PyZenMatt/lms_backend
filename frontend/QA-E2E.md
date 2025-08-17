# QA / E2E Guidelines

## Come lanciare gli smoke
```bash
cd frontend
npm ci
npx playwright install --with-deps
npm run build
npx http-server ./dist -p 3000 &
npx playwright test tests/e2e/smoke --reporter=html
npx playwright show-report
