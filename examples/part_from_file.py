#!/usr/bin/python
# coding: utf-8

r"""Example of creating a Part from a local Python file"""

import logging

import ccad.model as cm
import ccad.display as cd

p = cm.Part.from_py("sphere_r_2.py").geometry

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s :: %(levelname)6s :: '
                               '%(module)20s :: %(lineno)3d :: %(message)s')
    v1 = cd.view()
    v1.display(p)
    cd.start()
