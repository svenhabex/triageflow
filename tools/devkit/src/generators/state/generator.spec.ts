import { Tree, readProjectConfiguration } from '@nx/devkit';
import { createTreeWithEmptyWorkspace } from '@nx/devkit/testing';

import { stateGenerator } from './generator';
import { StateGeneratorSchema } from './schema';

describe('tools/devkit/src/generators/state generator', () => {
  let tree: Tree;
  const options: StateGeneratorSchema = { name: 'test' };

  beforeEach(() => {
    tree = createTreeWithEmptyWorkspace();
  });

  it('should run successfully', async () => {
    await stateGenerator(tree, options);
    const config = readProjectConfiguration(tree, 'test');

    expect(config).toBeDefined();
  });
});
