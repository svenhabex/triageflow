import jestPlugin from 'eslint-plugin-jest';

export default [
  {
    files: ['**/*.spec.ts'],
    plugins: {
      jest: jestPlugin,
    },
    rules: {
      ...jestPlugin.configs.all.rules,
      'jest/no-hooks': 'off',
      'jest/prefer-expect-assertions': 'off',
      'jest/prefer-importing-jest-globals': 'off',
      'jest/prefer-lowercase-title': 'off',
      'jest/max-expects': 'off',
      'jest/require-hook': 'off',
      'jest/prefer-called-with': 'off',
      'jest/no-conditional-in-test': 'off',
      'max-lines': 'off',
    },
  },
];
