#!/usr/bin/python
# coding: utf-8

r"""Simplistic geometry creation script

The part variable is assigned a ccad Solid in the global module namespace. This
part variable must exist as it is used by Part object constructors

"""

import ccad.model as cm

part = cm.sphere(2.0)
