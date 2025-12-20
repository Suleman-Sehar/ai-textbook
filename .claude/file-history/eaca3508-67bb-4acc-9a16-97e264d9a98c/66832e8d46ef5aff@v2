import js from '@eslint/js';
import reactPlugin from 'eslint-plugin-react';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    plugins: {
      react: reactPlugin,
    },
    languageOptions: {
      ecmaVersion: 12,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.node,
      },
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    rules: {
      'no-console': 'warn',
      'no-unused-vars': 'warn',
      'no-undef': 'error',
      'no-duplicate-imports': 'error',
      'prefer-const': 'error',
      'no-var': 'error',
      'object-shorthand': 'error',
      'prefer-template': 'error',
      'no-useless-escape': 'off', // Docusaurus markdown often needs escapes
      'react/react-in-jsx-scope': 'off', // Not needed in React 17+
    },
  },
  {
    files: ['**/*.md', '**/*.mdx'],
    rules: {
      'no-undef': 'off', // Allow global variables in MD/MDX files
    },
  },
];