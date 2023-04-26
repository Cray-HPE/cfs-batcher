# Cray Configuration Framework Service Batcher

The cfs-batcher attempts to keep the configuration state of components the same
as the desired configuration state.  All configuration state and desired state
information is stored in the cfs-api database.

Users do not interact directly with the batcher.  It continuously monitors
the state information the cfs has stored, and when it detects components that
do not match the desired configuration state, it schedules CFS sessions.  If
many components need configuration, the batcher will group the components and
schedule multiple sessions as needed to keep the number of components per
session to the desired size.

Because the batcher is constantly checking for components out of the desired
state, it will also retry configuration in cases where it fails.  So long as
the component does not fail to configure more than the maximum number of
retries, the batcher will automatically attempt to re-configure.

## Build Helpers
This repo uses some build helpers from the 
[cms-meta-tools](https://github.com/Cray-HPE/cms-meta-tools) repo. See that repo for more details.

## Local Builds
If you wish to perform a local build, you will first need to clone or copy the contents of the
cms-meta-tools repo to `./cms_meta_tools` in the same directory as the `Makefile`. When building
on github, the cloneCMSMetaTools() function clones the cms-meta-tools repo into that directory.

For a local build, you will also need to manually write the .version, .docker_version (if this repo
builds a docker image), and .chart_version (if this repo builds a helm chart) files. When building
on github, this is done by the setVersionFiles() function.

## Copyright and License
This project is copyrighted by Hewlett Packard Enterprise Development LP and is under the MIT
license. See the [LICENSE](LICENSE) file for details.

When making any modifications to a file that has a Cray/HPE copyright header, that header
must be updated to include the current year.

When creating any new files in this repo, if they contain source code, they must have
the HPE copyright and license text in their header, unless the file is covered under
someone else's copyright/license (in which case that should be in the header). For this
purpose, source code files include Dockerfiles, Ansible files, RPM spec files, and shell
scripts. It does **not** include Jenkinsfiles, OpenAPI/Swagger specs, or READMEs.

When in doubt, provided the file is not covered under someone else's copyright or license, then
it does not hurt to add ours to the header.
