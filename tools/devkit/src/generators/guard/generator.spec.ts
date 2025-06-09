import { readProjectConfiguration, Tree } from '@nx/devkit';
import { createTreeWithEmptyWorkspace } from '@nx/devkit/testing';

import { dataAccessGenerator } from './generator';
import { DataAccessGeneratorSchema } from './schema';

describe('guard generator', () => {
  let tree: Tree;
  const options: DataAccessGeneratorSchema = { name: 'test' };

  beforeEach(() => {
    tree = createTreeWithEmptyWorkspace();
  });

  it('should run successfully', async () => {
    await dataAccessGenerator(tree, options);
    const config = readProjectConfiguration(tree, 'test');

    expect(config).toBeDefined();
  });
});
