import { libraryGenerator } from '@nx/angular/generators';
import {
  formatFiles,
  getWorkspaceLayout,
  joinPathFragments,
  names,
  Tree,
} from '@nx/devkit';

import { StateGeneratorSchema } from './schema';
import { addFiles } from '../../lib/add-files';
import { BaseNormaliedSchemaType } from '../../lib/normalized-schema';
import { updateDomainDepConst } from '../../lib/update-domain-dep-const';

type NormalizedSchema = StateGeneratorSchema &
  BaseNormaliedSchemaType & {
    storeName: string;
    storeClassName: string;
  };

function normalizeOptions(
  tree: Tree,
  options: StateGeneratorSchema,
): NormalizedSchema {
  const name = `state-${names(options.name).fileName}`;
  const storeName = names(options.name).fileName;
  const storeClassName = names(options.name).className;
  const projectDirectory = options.domain
    ? `${names(options.domain).fileName}/${name}`
    : name;
  const projectName = projectDirectory.replace(new RegExp('/', 'g'), '-');
  const domainDirectory = `${getWorkspaceLayout(tree).libsDir}/${options.domain}`;
  const projectRoot = `${getWorkspaceLayout(tree).libsDir}/${projectDirectory}`;
  const parsedTags = ['type:state', `domain:${names(options.domain).fileName}`];

  return {
    ...options,
    name,
    storeName,
    storeClassName,
    projectName,
    projectRoot,
    projectDirectory,
    domainDirectory,
    parsedTags,
  };
}

export default async function stateGenerator(
  tree: Tree,
  options: StateGeneratorSchema,
): Promise<void> {
  const normalizedOptions = normalizeOptions(tree, options);

  await libraryGenerator(tree, {
    name: normalizedOptions.name,
    directory: normalizedOptions.projectRoot,
    tags: normalizedOptions.parsedTags.join(','),
    skipModule: true,
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

  addFiles(tree, normalizedOptions, __dirname);

  updateDomainDepConst(tree, normalizedOptions.domain);

  await formatFiles(tree);
}
