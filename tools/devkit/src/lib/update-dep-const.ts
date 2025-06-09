import { Tree } from '@nx/devkit';

import { checkRuleExists } from './check-rule-exists';

export function updateDepConst(host: Tree, update: (depConst: Array<object>) => void): void {
  let filePath = 'tslint.json';
  let rule = 'nx-enforce-module-boundaries';

  if (!host.exists('tslint.json')) {
    if (host.exists('.eslintrc.json')) {
      filePath = '.eslintrc.json';
      rule = '@nx/enforce-module-boundaries';
      // eslint-disable-next-line no-console
      console.info('Found .eslintrc.json');
    } else if (host.exists('.eslintrc')) {
      filePath = '.eslintrc';
      rule = '@nx/enforce-module-boundaries';
      // eslint-disable-next-line no-console
      console.info('Did not find .eslintrc.json but found .eslintrc');
    } else {
      // eslint-disable-next-line no-console
      console.info('Cannot add linting rules: linting config file does not exist');
      return;
    }
  }

  const text = host.read(filePath)?.toString() ?? '';
  const json = JSON.parse(text);
  let rules = json;
  if (rules['overrides']) {
    const overrides = rules['overrides'];
    rules = overrides.find(
      (e: { rules: { [x: string]: unknown } }) => e.rules && e.rules['@nx/enforce-module-boundaries'],
    );
  }

  if (!checkRuleExists(filePath, rule, rules)) {
    return;
  }

  const depConst = rules['rules'][rule][1]['depConstraints'] as Array<object>;
  update(depConst);

  const newText = JSON.stringify(json, undefined, 2);
  host.write(filePath, newText);
}
