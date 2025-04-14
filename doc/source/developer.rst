#######################
Developer Documentation
#######################

*********
Backports
*********

In order to backport a change, you can simply add the appropriate label to the
pull request, the pattern is ``backport <branch>``.  For example, if you want to
backport a change to the ``stable/2023.1`` branch, you would add the label
``backport stable/2023.1``.  The backport will be created automatically once the
pull request is merged.

If you need to run a backport after a pull request has been merged, you can do so
by adding the labels and then adding a comment with the text ``/backport``.
