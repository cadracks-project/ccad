#!/usr/bin/env python
# coding: utf-8

r"""
Description
-----------
ccad unittest.  View ../model.py for a full description of ccad.

Author
------
Charles Sharman, modified by Guillaume Florent to get a non zero exit code
when any test fails

License
-------
Distributed under the GNU LESSER GENERAL PUBLIC LICENSE Version 3.
View LICENSE for details.

"""
import sys

import unittest

import model_unittest

suite = unittest.TestSuite()
suite.addTests([model_unittest.suite()])
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
# Return a non zero exit code if any test fails
sys.exit(not result.wasSuccessful())
