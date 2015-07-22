#!/usr/bin/env python

# Copyright (c) 2015, Riverbank Computing Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


"""This script extracts various items of meta-data from a Mercurial repository
or a Mercurial archive.  It is not part of a packaged release.
"""


import os
import sys
import time


# The root directory, i.e. the one containing this script.
_RootDir = os.path.dirname(os.path.abspath(__file__))


def _release_tag(ctx):
    """ Get the release tag (i.e. a tag of the form x.y[.z]) converted to a
    3-tuple of integers if there is one.

    :param ctx:
        The Mercurial change context containing the tags.
    :return:
        The 3-tuple of integers or ``None`` if there was no release tag.
    """

    for tag in ctx.tags():
        if tag != 'tip':
            parts = tag.split('.')

            if len(parts) == 2:
                parts.append('0')

            if len(parts) == 3:
                major, minor, micro = parts

                try:
                    return (int(major), int(minor), int(micro))
                except ValueError:
                    pass

    return None


def _format_changelog(ctx):
    """ Format the log message for a changeset.

    :param ctx:
        The Mercurial change context containing the tags.
    :return:
        The formatted change log.
    """

    from mercurial.util import datestr

    log = "changeset:   %s\ndate:        %s\n%s" % (str(ctx), datestr(ctx.date()), ctx.description())

    return log


def _get_release():
    """ Get the release of the package.

    :return:
        A tuple of the full release name, the version number, the hexadecimal
        version number and a list of changelog entries (all as strings).
    """

    # The root directory should contain dot files that tell us what sort of
    # package we are.

    release_suffix = ''

    if os.path.exists(os.path.join(_RootDir, '.hg')):
        # Handle a Mercurial repository.

        from mercurial import hg, ui

        # Get the repository.
        repo = hg.repository(ui.ui(), _RootDir)

        # The last changeset is the "parent" of the working directory.
        ctx = repo[None].parents()[0]

        # If the one before the last changeset has a release tag then the last
        # changeset refers to the tagging and not a genuine change.
        before = ctx.parents()[0]

        version = _release_tag(before)

        if version is not None:
            ctx = before
        else:
            release_suffix = time.strftime('.dev%y%m%d%H%M')

        changelog = [_format_changelog(ctx)]

        # Go back through the line of the first parent to find the last
        # release.
        parent_version = None

        parents = ctx.parents()
        while len(parents) != 0:
            parent_ctx = parents[0]
            if parent_ctx.rev() < 0:
                break

            changelog.append(_format_changelog(parent_ctx))

            parent_version = _release_tag(parent_ctx)
            if parent_version is not None:
                break

            parents = parent_ctx.parents()

        if version is None and parent_version is not None:
            # This is a development release so work out what the next version
            # will be based on the previous version.
            major, minor, micro = parent_version

            if ctx.branch() == 'default':
                minor += 1

                # This should be 0 anyway.
                micro = 0
            else:
                micro += 1

            version = (major, minor, micro)
    else:
        # Handle a Mercurial archive.

        changelog = None
        name = os.path.basename(_RootDir)

        release_suffix = "-unknown"
        version = None

        parts = name.split('-')
        if len(parts) > 1:
            name = parts[-1]

            if len(name) == 12:
                # This is the best we can do without access to the repository.
                release_suffix = '-' + name

    # Format the results.
    if version is None:
        version = (0, 1, 0)

    major, minor, micro = version

    if micro == 0:
        version = '%d.%d' % (major, minor)
    else:
        version = '%d.%d.%d' % (major, minor, micro)

    if 'dev' in release_suffix:
        level = 0x0
    elif 'alpha' in release_suffix:
        level = 0xa
    elif 'beta' in release_suffix:
        level = 0xb
    elif 'rc' in release_suffix:
        level = 0xc
    else:
        level = 0xf

    release = '%s%s' % (version, release_suffix)
    hex_version = '%02x%02x%02x%01x0' % (major, minor, micro, level)

    return release, version, hex_version, changelog


def changelog(output_dir):
    """ The description of each change set going back to the last release are
    written to a file object.

    :param output_dir:
        The name of the directory that the log is created in.
    :return:
        ``True`` if the log was written or ``False`` if the information wasn't
        available (because this is a Mercurial archive).
    """

    release, _, _, changelog = _get_release()

    if changelog is None:
        return False

    changelog_name = 'ChangeLog'
    if 'dev' in release:
        changelog_name += '-' + release

    out_file = open(os.path.join(output_dir, changelog_name), 'w')
    out_file.write("\n\n".join(changelog) + "\n")
    out_file.close()

    return True


def pyversion(py_file):
    """ Write the version of the package as a string and a hexversion to a
    file.  If it is a release then it will be of the form x.y[.z].  If it is a
    development release then it will be of the form x.y[.z].dev{timestamp}
    where x.y[.z] is the version number of the next release (not the previous
    one).  If this is a Mercurial archive (rather than a repository) then it
    does the best it can (based on the name of the directory) with the limited
    information available.

    :param py_file:
        The file that the Python code is written to.
    """

    release, _, hexversion, _ = _get_release()

    py_file.write('PYQTDEPLOY_RELEASE = \'%s\'\n' % release)
    py_file.write('PYQTDEPLOY_HEXVERSION = 0x%s\n' % hexversion)


if __name__ == '__main__':

    def _changelog(options):
        """get the changelog entries since the last release"""

        output_dir = options.output
        if output_dir is None:
            output_dir = '.'

        if not changelog(output_dir):
            sys.stderr.write("Unable to produce a changelog without a repository\n")
            sys.exit(2)


    def _pyversion(options):
        """create Python code implementing the version of the package"""

        if options.output is not None:
            out_file = open(options.output, 'w')
        else:
            out_file = sys.stdout

        pyversion(out_file)

        if options.output is not None:
            out_file.close()


    actions = (_changelog, _pyversion)

    import optparse

    class MyParser(optparse.OptionParser):

        def get_usage(self):
            """ Reimplemented to add the description of the actions.  We don't
            use the description because the default formatter strips newlines.
            """

            usage = optparse.OptionParser.get_usage(self)

            usage += "\n" + __doc__ + "\nActions:\n"

            for action in actions:
                usage += "  %-9s  %s\n" % (action.__name__[1:], action.func_doc)

            return usage


    action_names = [action.__name__[1:] for action in actions]

    rel, _, _, _ = _get_release()

    parser = MyParser(
            usage="%%prog [options] %s" % '|'.join(action_names), version=rel)

    parser.add_option("-o", "--output", metavar="FILE or DIR", dest='output',
            help="write output to FILE or DIR")

    options, args = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        sys.exit(1)

    for action in actions:
        if action.__name__[1:] == args[0]:
            action(options)
            break
    else:
        parser.print_help()
        sys.exit(1)

    sys.exit()
