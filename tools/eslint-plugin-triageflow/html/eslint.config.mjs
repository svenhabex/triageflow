import angularTemplatePlugin from '@angular-eslint/eslint-plugin-template';
import angularTemplateParserPlugin from '@angular-eslint/template-parser';
import angularEslint from '@angular-eslint/eslint-plugin';
import eslintConfigPrettier from 'eslint-config-prettier';

export default [
  {
    files: ['**/*.html'],
    languageOptions: {
      parser: angularTemplateParserPlugin,
    },
    plugins: {
      '@angular-eslint': angularEslint,
      '@angular-eslint/template': angularTemplatePlugin,
    },
    rules: {
      ...angularTemplatePlugin.configs.all.rules,
      // Disable rules that conflict with Prettier
      ...eslintConfigPrettier.rules,
      '@angular-eslint/template/alt-text': 'off',
      '@angular-eslint/template/button-has-type': 'warn',
      '@angular-eslint/template/click-events-have-key-events': 'off',
      '@angular-eslint/template/conditional-complexity': 'warn',
      '@angular-eslint/template/cyclomatic-complexity': 'warn',
      '@angular-eslint/template/i18n': 'off',
      '@angular-eslint/template/interactive-supports-focus': 'off',
      '@angular-eslint/template/label-has-associated-control': 'warn',
      '@angular-eslint/template/no-any': 'warn',
      '@angular-eslint/template/no-call-expression': 'off',
      '@angular-eslint/template/no-inline-styles': 'warn',
      '@angular-eslint/template/no-interpolation-in-attributes': 'warn',
      '@angular-eslint/template/prefer-control-flow': 'warn',
      '@angular-eslint/template/prefer-ngsrc': 'warn',
      '@angular-eslint/template/prefer-self-closing-tags': 'error',
      '@angular-eslint/template/use-track-by-function': 'warn',
    },
  },
];
