import { Tree, readProjectConfiguration } from '@nx/devkit';
import { createTreeWithEmptyWorkspace } from '@nx/devkit/testing';

import { shellGenerator } from './generator';
import { ShellGeneratorSchema } from './schema';

describe('shell generator', () => {
  let tree: Tree;
  const options: ShellGeneratorSchema = { name: 'test' };

  beforeEach(() => {
    tree = createTreeWithEmptyWorkspace();
  });

  it('should run successfully', async () => {
    await shellGenerator(tree, options);
    const config = readProjectConfiguration(tree, 'test');

    expect(config).toBeDefined();
  });
});
