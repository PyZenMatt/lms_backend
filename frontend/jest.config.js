module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  
  transform: {
    '^.+\\.(js|jsx)$': ['babel-jest', {
      presets: [
        ['@babel/preset-env', { targets: { node: 'current' } }],
        ['@babel/preset-react', { runtime: 'automatic' }]
      ]
    }]
  },
  
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$': 'jest-transform-stub',
    '^@/(.*)$': '<rootDir>/src/$1'
  },
  
  testMatch: [
    '<rootDir>/src/**/*.{test,spec}.{js,jsx}'
  ],
  
  moduleFileExtensions: ['js', 'jsx', 'json'],
  
  transformIgnorePatterns: [
    'node_modules/(?!(.*\\.mjs$))'
  ]
};
