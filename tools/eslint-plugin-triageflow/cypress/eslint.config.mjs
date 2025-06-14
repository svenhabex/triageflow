import cypressPlugin from 'eslint-plugin-cypress';

export default [
  {
    files: ['**/*.cy.ts'],
    rules: {
      ...cypressPlugin.configs.recommended.rules,
      '@typescript-eslint/explicit-function-return-type': 'off',
    },
  },
];
