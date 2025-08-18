module.exports = {
  root: true,
  env: { browser: true, es2021: true, node: true },
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  extends: [],
  rules: {
    'no-restricted-imports': ['error', {
      paths: [
        'bootstrap',
        'bootstrap/dist/css/bootstrap.min.css',
        'react-bootstrap'
      ],
      patterns: [
        '**/styles/legacy/**',
        '**/assets/scss/**',
        '**/assets/css/**'
      ]
    }]
  }
};
