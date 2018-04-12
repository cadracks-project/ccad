****
ccad
****

.. image:: https://travis-ci.org/osv-team/ccad.svg?branch=master
    :target: https://travis-ci.org/osv-team/ccad

.. image:: https://api.codacy.com/project/badge/Grade/7a33b7bb47c74733b848b5b382a7e5ca
    :target: https://www.codacy.com/app/guillaume-florent/ccad?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=osv-team/ccad&amp;utm_campaign=Badge_Grade

.. image:: https://anaconda.org/gflorent/ccad/badges/version.svg
    :target: https://anaconda.org/gflorent/ccad

.. image:: https://anaconda.org/gflorent/ccad/badges/latest_release_date.svg
    :target: https://anaconda.org/gflorent/ccad

.. image:: https://anaconda.org/gflorent/ccad/badges/platforms.svg
    :target: https://anaconda.org/gflorent/ccad

.. image:: https://anaconda.org/gflorent/ccad/badges/downloads.svg
    :target: https://anaconda.org/gflorent/ccad




Description
===========

ccad is a text-based mechanical CAD (computer aided design) tool.  It
is a python module you import within a python file or from the python
prompt.  Once imported, you can create and view mechanical objects.

ccad is a python wrapper of pythonocc.  No knowledge of pythonocc is
necessary to operate ccad.

Install
=======

This is the old installation documentation, to view the new Docker based procedures
please see `INSTALL.rst <./INSTALL.rst>`_

Linux
-----

Make sure you have working copies of pythonocc and python-qt4.  Then:

- Download and unzip the .zip file from github

- cd ccad-master

- python setup.py install --prefix=/usr/local (as root)

Change the prefix argument to install in a different directory.

Windows
-------

Make sure you have working copies of pythonocc and python-qt4.  Then:

- Download the .zip file from github

- From a file explorer window, right-click on the downloaded zip file
  and select "extract here"

- Navigate to the folder just created

- Shift-right-click in the file explorer window and select "open
  command window here"

- Type the following command:
  python setup.py install

For interactive mode, use ipython or run python from a command window.
ccad does *not* work under Idle.

Mac
---

While ccad should work for Mac, we haven't heard of anyone trying it.
If you install it, let us know, and we'll update the README.

To Operate
==========

Start python from the command line.  Then:

.. code-block:: python

  import ccad.model as cm
  import ccad.display as cd
  s1 = cm.sphere(1.0)
  v1 = cd.view()
  v1.display(s1)

You should see a sphere displayed in a window.

Consult the documentation at prefix/share/doc/ccad/html/contents.html
for ccad's full capabilities.

Developpers only
================

Build
-----

Update components with modifications to MANIFEST.in and setup.py.
Then,

  python setup.py sdist

**Make sure you verify changes with unittest/test_all.py before
committing.**

Build the Documentation
-----------------------

Some files are captured with xwd (window dump).  They're commented in
MANIFEST.in.  The remaining are generated with generate_images.py.

  cd ccad-ver/doc
  python generate_images.py
  sphinx-build . html

Then, direct your browser to ccad-ver/doc/html/contents.html

Philosophy
----------

1. Edges are continuous lines in 3D space.  There should be no reason
   to distinguish between them and OCC curves.  Wires are collections
   of edge connections.  Faces are continuous surfaces in 3D space.
   There should be no reason to distinguish between them and OCC
   surfaces.  Shells are collections of face connections.

2. The end-user should not ever have to call pythonOCC directly.  ccad
   should handle all things someone might want to do in CAD.
