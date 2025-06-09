import { Tree, readProjectConfiguration } from '@nx/devkit';
import { createTreeWithEmptyWorkspace } from '@nx/devkit/testing';

import { constGenerator } from './generator';
import { ConstGeneratorSchema } from './schema';

describe('const generator', () => {
  let tree: Tree;
  const options: ConstGeneratorSchema = { name: 'test' };

  beforeEach(() => {
    tree = createTreeWithEmptyWorkspace();
  });

  it('should run successfully', async () => {
    await constGenerator(tree, options);
    const config = readProjectConfiguration(tree, 'test');

    expect(config).toBeDefined();
  });
});
