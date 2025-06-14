import importPlugin from 'eslint-plugin-import';
import sortClassMembersPlugin from 'eslint-plugin-sort-class-members';

export default [
  {
    files: ['**/*.ts'],
    languageOptions: {
      parser: (await import('@typescript-eslint/parser')).default,
      parserOptions: {
        project: './tsconfig.base.json',
      },
    },
    plugins: {
      import: importPlugin,
      'sort-class-members': sortClassMembersPlugin,
    },
    rules: {
      '@angular-eslint/prefer-output-readonly': 'warn',
      '@angular-eslint/prefer-on-push-component-change-detection': 'off',
      '@angular-eslint/prefer-standalone': 'off',
      '@angular-eslint/use-component-view-encapsulation': 'error',
      '@angular-eslint/no-pipe-impure': 'error',
      '@angular-eslint/no-output-native': 'warn',
      '@angular-eslint/no-input-rename': 'off',
      'import/no-unresolved': 'off',
      'import/export': 'warn',
      'import/order': [
        'error',
        {
          groups: [
            ['builtin', 'external', 'internal'],
            ['parent', 'sibling', 'index'],
          ],
          'newlines-between': 'always',
          alphabetize: {
            order: 'asc',
            caseInsensitive: true,
          },
          pathGroups: [
            {
              pattern: 'rxjs',
              group: 'builtin',
            },
            {
              pattern: '@angular/**',
              group: 'builtin',
              position: 'after',
            },
            {
              pattern: '@triageflow/**',
              group: 'builtin',
              position: 'after',
            },
          ],
          distinctGroup: false,
          pathGroupsExcludedImportTypes: ['rxjs', '@angular', '@triageflow'],
        },
      ],
      'no-console': 'error',
      'no-duplicate-imports': 'error',
      'sort-class-members/sort-class-members': [
        'error',
        {
          order: [
            '[static-properties]',
            '[static-methods]',
            '[properties]',
            '[conventional-private-properties]',
            'constructor',
            '[methods]',
            '[conventional-private-methods]',
          ],
          accessorPairPositioning: 'getThenSet',
        },
      ],
      '@typescript-eslint/no-non-null-assertion': 'warn',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          ignoreRestSiblings: true,
          argsIgnorePattern: '^_',
          destructuredArrayIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
      '@typescript-eslint/consistent-type-definitions': 'off',
      '@typescript-eslint/consistent-indexed-object-style': 'off',
      '@typescript-eslint/consistent-type-assertions': [
        'warn',
        { assertionStyle: 'as' },
      ],
      '@typescript-eslint/explicit-function-return-type': 'error',
      '@typescript-eslint/member-ordering': [
        'warn',
        {
          default: ['#private-field', 'public-field'],
        },
      ],
      '@typescript-eslint/no-confusing-non-null-assertion': 'warn',
      //FIXME: HIGH: @typescript-eslint/no-parameter-properties should be an error - all constructor args should be private readonly so they cannot be mutated
      '@typescript-eslint/parameter-properties': [
        'warn',
        { allow: ['private readonly', 'protected readonly'] },
      ],
      '@typescript-eslint/prefer-for-of': 'warn',
      'max-lines': [
        'warn',
        { max: 300, skipComments: true, skipBlankLines: true },
      ],
      'no-unused-disable': 'off',
    },
  },
];
