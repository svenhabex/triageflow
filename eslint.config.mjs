import nx from '@nx/eslint-plugin';

export default [
  {
    files: ['**/*.json'],
    // Override or add rules here
    rules: {},
    languageOptions: {
      parser: await import('jsonc-eslint-parser'),
    },
  },
  ...nx.configs['flat/base'],
  ...nx.configs['flat/typescript'],
  ...nx.configs['flat/javascript'],
  {
    ignores: [
      '**/dist',
      '**/vite.config.*.timestamp*',
      '**/vitest.config.*.timestamp*',
    ],
  },
  {
    files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx'],
    rules: {
      '@nx/enforce-module-boundaries': [
        'error',
        {
          enforceBuildableLibDependency: true,
          allow: ['^.*/eslint(\\.base)?\\.config\\.[cm]?js$'],
          depConstraints: [
            {
              sourceTag: 'type:app',
              onlyDependOnLibsWithTags: [
                'type:shell',
                'type:models',
                'type:const',
              ],
            },
            {
              sourceTag: 'type:shell',
              onlyDependOnLibsWithTags: [
                'type:feature',
                'type:ui',
                'type:data-access',
                'type:state',
                'type:utils',
                'type:api',
                'type:models',
                'type:const',
              ],
            },
            {
              sourceTag: 'type:feature',
              onlyDependOnLibsWithTags: [
                'type:feature',
                'type:ui',
                'type:data-access',
                'type:state',
                'type:utils',
                'type:api',
                'type:models',
                'type:const',
              ],
            },
            {
              sourceTag: 'type:api',
              onlyDependOnLibsWithTags: [
                'type:feature',
                'type:ui',
                'type:data-access',
                'type:utils',
                'type:models',
                'type:const',
              ],
            },
            {
              sourceTag: 'type:ui',
              onlyDependOnLibsWithTags: [
                'type:ui',
                'type:utils',
                'type:models',
                'type:const',
              ],
            },
            {
              sourceTag: 'type:data-access',
              onlyDependOnLibsWithTags: [
                'type:data-access',
                'type:utils',
                'type:api',
                'type:models',
                'type:const',
              ],
            },
            {
              sourceTag: 'type:state',
              onlyDependOnLibsWithTags: [
                'type:state',
                'type:data-access',
                'type:utils',
                'type:api',
                'type:models',
                'type:const',
              ],
            },
            {
              sourceTag: 'type:guard',
              onlyDependOnLibsWithTags: [
                'type:state',
                'type:data-access',
                'type:utils',
                'type:api',
                'type:models',
                'type:const',
              ],
            },
            {
              sourceTag: 'type:utils',
              onlyDependOnLibsWithTags: [
                'type:utils',
                'type:models',
                'type:const',
              ],
            },
            {
              sourceTag: 'type:const',
              onlyDependOnLibsWithTags: ['type:const', 'type:models'],
            },
            {
              sourceTag: 'type:models',
              onlyDependOnLibsWithTags: ['type:models', 'type:const'],
            },
            {
              sourceTag: 'domain:shared',
              onlyDependOnLibsWithTags: ['domain:shared'],
            },
            {
              sourceTag: '*',
              onlyDependOnLibsWithTags: ['*'],
            },
          ],
        },
      ],
    },
  },
  {
    files: [
      '**/*.ts',
      '**/*.tsx',
      '**/*.cts',
      '**/*.mts',
      '**/*.js',
      '**/*.jsx',
      '**/*.cjs',
      '**/*.mjs',
    ],
    // Override or add rules here
    rules: {},
  },
];
