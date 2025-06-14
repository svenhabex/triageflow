export function checkRuleExists(
  filePath: string,
  rule: string,
  rules: object,
): boolean {
  if (!rules['rules']) {
    // eslint-disable-next-line no-console
    console.info(`${filePath}: rules expected`);
    return false;
  }

  if (!rules['rules'][rule]) {
    // eslint-disable-next-line no-console
    console.info(`${filePath}: ${rule} expected`);
    return false;
  }

  if (rules['rules'][rule]['length'] < 2) {
    // eslint-disable-next-line no-console
    console.info(`${filePath}: ${rule}.1 unexpected`);
    return false;
  }

  if (!rules['rules'][rule][1]['depConstraints']) {
    // eslint-disable-next-line no-console
    console.info(`${filePath}: ${rule}.1.depConstraints expected.`);
    return false;
  }

  if (!Array.isArray(rules['rules'][rule][1]['depConstraints'])) {
    // eslint-disable-next-line no-console
    console.info(
      `${filePath}: ${rule}.1.depConstraints expected to be an array.`,
    );
    return false;
  }

  return true;
}
