module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
  extends: ['eslint:recommended', 'plugin:@typescript-eslint/recommended'],
  rules: {
    // Disallow direct imports of ethers library from arbitrary modules.
  // Developers should use the on-chain wrapper in `src/web3/ethersWeb3.ts` (alias `@onchain/ethersWeb3`).
    'no-restricted-imports': [
      'error',
      {
        'paths': [
          {
            'name': 'ethers',
            'message': "Import 'ethers' only from the on-chain adapter (src/web3/ethersWeb3.ts or @onchain/ethersWeb3) and avoid direct usage in DB/REST modules."
          }
        ]
      }
    ],

    // Keep other rules permissive for incremental cleanup.
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['warn', { 'argsIgnorePattern': '^_' }],
  }
};
