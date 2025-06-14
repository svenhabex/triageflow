import { libraryGenerator } from '@nx/angular/generators';
import {
  formatFiles,
  getWorkspaceLayout,
  joinPathFragments,
  names,
  Tree,
} from '@nx/devkit';

import { FeatureGeneratorSchema } from './schema';
import { addFiles } from '../../lib/add-files';
import { BaseNormaliedSchemaType } from '../../lib/normalized-schema';
import { updateDomainDepConst } from '../../lib/update-domain-dep-const';

type NormalizedSchema = FeatureGeneratorSchema &
  BaseNormaliedSchemaType & {
    componentName: string;
  };

function normalizeOptions(
  tree: Tree,
  options: FeatureGeneratorSchema,
): NormalizedSchema {
  const name = `feat-${names(options.name).fileName}`;
  const componentName = `${names(options.name).fileName}`;
  const projectDirectory = `${names(options.domain).fileName}/${name}`;
  const projectName = projectDirectory.replace(new RegExp('/', 'g'), '-');
  const domainDirectory = `${getWorkspaceLayout(tree).libsDir}/${options.domain}`;
  const projectRoot = `${getWorkspaceLayout(tree).libsDir}/${projectDirectory}`;
  const parsedTags = [
    'type:feature',
    `domain:${names(options.domain).fileName}`,
  ];

  return {
    ...options,
    name,
    componentName,
    projectName,
    projectRoot,
    projectDirectory,
    domainDirectory,
    parsedTags,
  };
}

export default async function (
  tree: Tree,
  options: FeatureGeneratorSchema,
): Promise<void> {
  const normalizedOptions = normalizeOptions(tree, options);

  await libraryGenerator(tree, {
    name: normalizedOptions.name,
    directory: normalizedOptions.projectRoot,
    tags: normalizedOptions.parsedTags.join(','),
    skipModule: true,
    displayBlock: true,
    style: 'scss',
    simpleName: true,
    prefix: 'flow',
  });

  const pathToDelete = joinPathFragments(
    'libs',
    normalizedOptions.projectDirectory,
    'src',
    'lib',
    `${normalizedOptions.name}`,
  );
  if (tree.exists(pathToDelete)) {
    tree.delete(pathToDelete);
  }

  addFiles(
    tree,
    {
      ...normalizedOptions,
      domainClassName: names(normalizedOptions.domain).className,
      componentClassName: names(normalizedOptions.componentName).className,
      domainFileName: names(options.domain).fileName,
    },
    __dirname,
  );

  updateDomainDepConst(tree, normalizedOptions.domain);

  await formatFiles(tree);
}
