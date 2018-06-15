#!/usr/bin/env python
# coding: utf-8

r"""Basic example

Probably the simplest example of using ccad

"""

import ccad.model as cm
#import ccad.display as cd
import wx
from aocutils.display.wx_viewer import Wx3dViewerFrame

s1 = cm.sphere(2.0)
#v1 = cd.view()
#v1.display(s1)
App = wx.App()
frame = Wx3dViewerFrame()
frame.wx_3d_viewer.display_shape(s1.shape)
#cd.start()
App.SetTopWindow(frame)
App.MainLoop()
