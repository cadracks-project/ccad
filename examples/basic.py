#!/usr/bin/python
# coding: utf-8

r"""Basic example

Probably the simplest example of using ccad

"""

import ccad.model as cm
import ccad.display as cd
s1 = cm.sphere(2.0)
v1 = cd.view()
v1.display(s1)
cd.start()
