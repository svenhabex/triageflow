import { libraryGenerator } from '@nx/angular/generators';
import {
  formatFiles,
  getWorkspaceLayout,
  joinPathFragments,
  names,
  Tree,
} from '@nx/devkit';

import { ShellGeneratorSchema } from './schema';
import { addFiles } from '../../lib/add-files';
import { BaseNormaliedSchemaType } from '../../lib/normalized-schema';
import { updateDomainDepConst } from '../../lib/update-domain-dep-const';

type NormalizedSchema = ShellGeneratorSchema & BaseNormaliedSchemaType;

function normalizeOptions(
  tree: Tree,
  options: ShellGeneratorSchema,
): NormalizedSchema {
  const fileName = names(options.name).fileName;
  const name =
    fileName === 'shell' ? fileName : `shell-${names(options.name).fileName}`;
  const projectDirectory = options.domain
    ? `${names(options.domain).fileName}/${name}`
    : name;
  const projectName = 'shell';
  const domainDirectory = `${getWorkspaceLayout(tree).libsDir}/${options.domain}`;
  const projectRoot = `${getWorkspaceLayout(tree).libsDir}/${projectDirectory}`;
  const parsedTags = ['type:shell', `domain:${names(options.domain).fileName}`];

  return {
    ...options,
    name,
    projectName,
    projectRoot,
    projectDirectory,
    domainDirectory,
    parsedTags,
  };
}

export default async function (
  tree: Tree,
  options: ShellGeneratorSchema,
): Promise<void> {
  const normalizedOptions = normalizeOptions(tree, options);

  await libraryGenerator(tree, {
    name: normalizedOptions.name,
    directory: normalizedOptions.projectDirectory,
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
