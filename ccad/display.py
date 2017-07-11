# coding: utf-8

"""
Description
-----------
ccad viewer designed to be imported from a python prompt or program.
View README for a full description of ccad.

display.py contains classes and functions for displaying.

The viewer uses python-qt4.

This version runs a low-level viewer for Linux and pythonocc's own
Display3d for other platforms.  Display3d has an error with multiple
viewing windows:

RuntimeError: Aspect_GraphicDeviceDefinitionError
Cannot connect to server

Author
------
View AUTHORS.

License
-------
Distributed under the GNU LESSER GENERAL PUBLIC LICENSE Version 3.
View LICENSE for details.
"""

from __future__ import print_function

import os as _os
import sys as _sys
import math as _math
import logging

try:
    # from PyQt4 import QtCore as _QtCore, QtGui as _QtGui
    from PyQt5 import QtCore, QtWidgets
except ImportError:
    try:
        from PySide import QtCore, QtGui as QtWidgets
    except:
        manager = 'none'
        print("""
Warning: Cannot find python-qt4 or pyside.  You will not be able to
use ccad's display.  Instead, you may use pythonocc's viewers.  ccad
shapes may be displayed in pythonocc's viewers by using the .shape
attribute.  For example:

    import ccad.model as cm
    import OCC.Display.SimpleGui as SimpleGui

    s1 = cm.sphere(1.0)
    display, start_display, add_menu, add_function_to_menu = \
        SimpleGui.init_display()
    display.DisplayShape(s1.shape, update = True)
    start_display()
""")

from OCC import (AIS as _AIS, Aspect as _Aspect, gp as _gp,
                 Graphic3d as _Graphic3d, Prs3d as _Prs3d,
                 Quantity as _Quantity, TopAbs as _TopAbs, V3d as _V3d)
from OCC.BRepTools import BRepTools_WireExplorer as _BRepTools_WireExplorer
from OCC.HLRAlgo import HLRAlgo_Projector as _HLRAlgo_Projector
from OCC.HLRBRep import (HLRBRep_Algo as _HLRBRep_Algo,
                         HLRBRep_HLRToShape as _HLRBRep_HLRToShape)
# from OCC.TCollection import (TCollection_ExtendedString as
#                                                   TCollection_ExtendedString)
from OCC.TopExp import TopExp_Explorer as _TopExp_Explorer

# TODO : the following import breaks when migrating from OCC 0.16.2 to 0.17
# from OCC.Visual3d import Visual3d_ViewOrientation as _Visual3d_ViewOrientation

# Use Viewer3d, a subclass of Display3d
# from OCC.Visualization import Display3d as _Display3d
from OCC.Display.OCCViewer import Viewer3d as _Display3d

from OCC.gp import gp_Pnt, gp_Vec, gp_Dir
from OCC.Prs3d import Prs3d_Arrow, Prs3d_Presentation
from OCC.BRepBuilderAPI import BRepBuilderAPI_MakeEdge

try:
    import ccad.model as _cm
except ImportError:
    import model as _cm


# Globals
version = '0.13'  # Change also in setup.py, doc/conf.py
interactive = True
manager = 'qt'
app = None

logger = logging.getLogger(__name__)


class ViewQt(QtWidgets.QWidget):
    """A Qt based viewer"""

    def __init__(self, perspective=False):
        """Perspective doesn't seem to work in pythonocc ***.  Don't use."""
        super(ViewQt, self).__init__()
        self.setMouseTracking(True)
        # self.setFocusPolicy(_QtCore.Qt.WheelFocus)
        # self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored,
        #                                       QtGui.QSizePolicy.Ignored))

        self.REGULAR_CURSOR = QtCore.Qt.ArrowCursor
        self.WAIT_CURSOR = QtCore.Qt.WaitCursor

        self.key_table = {'redraw()': 'PgUp',
                          'orbitup()': 'Up',
                          'panup()': '8',
                          'orbitdown()': 'Down',
                          'pandown()': '2',
                          'orbitleft()': 'Left',
                          'panleft()': '4',
                          'orbitright()': 'Right',
                          'panright()': '6',
                          'rotateccw()': '/',
                          'rotatecw()': '*',
                          'zoomin()': '+',
                          'zoomout()': '-',
                          'fit()': 'Del',
                          'query()': 'Q',
                          'viewstandard("top")': 'Home',
                          'viewstandard("bottom")': '7',
                          'viewstandard("front")': 'End',
                          'viewstandard("back")': '1',
                          'viewstandard("right")': 'PgDown',
                          'viewstandard("left")': '3',
                          'quit()': 'Ctrl+Q'}

        self.selected = None
        self.selected_shape = None
        self.selection_type = 'shape'
        self.selection_index = -1
        self.foreground = (1.0, 1.0, 0.0)  # Bright-Yellow is default
        self.display_shapes = []

        # Main Window
        self.setWindowTitle('ccad viewer')
        self.menus = {}

        # Vertical Container
        vbox1 = QtWidgets.QVBoxLayout()
        vbox1.setContentsMargins(0, 0, 0, 0)
        vbox1.setSpacing(0)

        # Menu Space
        self.menubar = QtWidgets.QMenuBar()
        vbox1.setMenuBar(self.menubar)

        # File
        file_menu = QtWidgets.QMenu('&File', self)
        self.menubar.addMenu(file_menu)

        file_menu.addAction('&Save', self.save)
        file_menu.addAction('&Quit', self.quit, self.key_lookup('quit()'))

        # view
        view_menu = QtWidgets.QMenu('&View', self)
        self.menubar.addMenu(view_menu)

        view_mode = QtWidgets.QMenu('Mode', self)
        view_menu.addMenu(view_mode)
        view_mode_container = QtWidgets.QActionGroup(self)
        view_mode_wireframe = view_mode.addAction('Wireframe',
                                                  self.mode_wireframe)
        view_mode_wireframe.setCheckable(True)
        view_mode_container.addAction(view_mode_wireframe)
        view_mode_shaded = view_mode.addAction('Shaded', self.mode_shaded)
        view_mode_shaded.setCheckable(True)
        view_mode_shaded.setChecked(True)
        view_mode_container.addAction(view_mode_shaded)
        view_mode_hlr = view_mode.addAction('Hidden Line Removal',
                                            self.mode_hlr)
        view_mode_hlr.setCheckable(True)
        view_mode_container.addAction(view_mode_hlr)

        view_side = QtWidgets.QMenu('Side', self)
        view_menu.addMenu(view_side)
        view_side.addAction('Front', lambda view='front': self.viewstandard(view),
                            self.key_lookup('viewstandard("front")'))
        view_side.addAction('Top', lambda view='top': self.viewstandard(view),
                            self.key_lookup('viewstandard("top")'))
        view_side.addAction('Right', lambda view='right': self.viewstandard(view),
                            self.key_lookup('viewstandard("right")'))
        view_side.addAction('Back', lambda view='back': self.viewstandard(view),
                            self.key_lookup('viewstandard("back")'))
        view_side.addAction('Bottom', lambda view='bottom': self.viewstandard(view),
                            self.key_lookup('viewstandard("bottom")'))
        view_side.addAction('Left', lambda view='left': self.viewstandard(view),
                            self.key_lookup('viewstandard("left")'))

        view_orbit = QtWidgets.QMenu('Orbit', self)
        view_menu.addMenu(view_orbit)
        view_orbit.addAction('Up', self.orbitup, self.key_lookup('orbitup()'))
        view_orbit.addAction('Down', self.orbitdown, self.key_lookup('orbitdown()'))
        view_orbit.addAction('Left', self.orbitleft, self.key_lookup('orbitleft()'))
        view_orbit.addAction('Right', self.orbitright, self.key_lookup('orbitright()'))
        view_orbit.addAction('CCW', self.rotateccw, self.key_lookup('rotateccw()'))
        view_orbit.addAction('CW', self.rotatecw, self.key_lookup('rotatecw()'))

        view_pan = QtWidgets.QMenu('Pan', self)
        view_menu.addMenu(view_pan)
        view_pan.addAction('Up', self.panup, self.key_lookup('panup()'))
        view_pan.addAction('Down', self.pandown, self.key_lookup('pandown()'))
        view_pan.addAction('Left', self.panleft, self.key_lookup('panleft()'))
        view_pan.addAction('Right', self.panright, self.key_lookup('panright()'))

        view_zoom = QtWidgets.QMenu('Zoom', self)
        view_menu.addMenu(view_zoom)
        view_zoom.addAction('In', self.zoomin, self.key_lookup('zoomin()'))
        view_zoom.addAction('Out', self.zoomout, self.key_lookup('zoomout()'))
        view_zoom.addAction('Fit to Screen', self.fit, self.key_lookup('fit()'))

        view_menu.addAction('Redraw', self.redraw, self.key_lookup('redraw()'))

        # select
        select_menu = QtWidgets.QMenu('&Select', self)
        self.menubar.addMenu(select_menu)
        select_container = QtWidgets.QActionGroup(self)

        select_vertex = select_menu.addAction('Select Vertex',
                                              self.select_vertex)
        select_vertex.setCheckable(True)
        select_container.addAction(select_vertex)

        select_edge = select_menu.addAction('Select Edge', self.select_edge)
        select_edge.setCheckable(True)
        select_container.addAction(select_edge)

        select_wire = select_menu.addAction('Select Wire', self.select_wire)
        select_wire.setCheckable(True)
        select_container.addAction(select_wire)

        select_face = select_menu.addAction('Select Face', self.select_face)
        select_face.setCheckable(True)
        select_container.addAction(select_face)

        select_shape = select_menu.addAction('Select Shape', self.select_shape)
        select_shape.setCheckable(True)
        select_shape.setChecked(True)
        select_container.addAction(select_shape)

        select_menu.addAction('Query', self.query, self.key_lookup('query()'))

        # help
        help_menu = QtWidgets.QMenu('&Help', self)
        self.menubar.addMenu(help_menu)
        help_menu.addAction('&Manual', self.display_manual)
        help_menu.addAction('&About', self.about)

        # OpenGL Space
        self.glarea = GLWidget(self)
        vbox1.addWidget(self.glarea)

        # Status Line
        self.status_bar = QtWidgets.QLabel()
        self.status_bar.setText('')
        vbox1.addWidget(self.status_bar)

        self.setLayout(vbox1)
        self.show()

        self.glarea.start(perspective)

        # Some Initial Values
        self.mode_shaded()
        self.set_background((0.0, 0.0, 0.0))
        self.set_triedron(1)

        # Set up some initial states
        self.morbit = _math.pi / 12.0
        self.set_scale(10.0)

    def add_menu(self, hierarchy):
        """Add a menu.  Used internally.  Used externally for those who
        know the window manager well, and want to add fancy menu items
        (radio buttons, check boxes, items with graphics, etc.)
        manually.  For text-only menu items, use add_menuitem.

        Parameters
        ----------
        hierarchy

        """
        last_menu = self.menubar
        for sub_menu in hierarchy:
            if sub_menu not in self.menus:
                menu = QtWidgets.QMenu(sub_menu, self)
                last_menu.addMenu(menu)
                self.menus[sub_menu] = menu
            last_menu = self.menus[sub_menu]
        return last_menu

    def add_menuitem(self, hierarchy, func, *args):
        """Add a menu item.  hierarchy is a tuple.  The first element in
        the tuple is the main menu at the menubar level, and the last
        item is the menu item.  Intermediate items may be specified,
        if there are submenus.  func is the function to call when the
        menu is selected.  args are any pass parameters to pass to the
        function.

        Generates all needed menus to create the passed hierarchy.

        Parameters
        ----------
        hierarchy
        func
        *args

        """
        last_menu = self.add_menu(hierarchy[:-1])
        last_menu.addAction(hierarchy[-1], lambda: func(*args))

    # Event Functions
    def redraw(self):
        """Called from a user request"""
        self.glarea.paintEvent(None)

    def key_lookup(self, func_call):
        """Connects a key press to a function in the key_table

        Parameters
        ----------
        func_call

        """
        key = self.key_table[func_call]
        return key

    def keyPressEvent(self, event):
        """Called when a key is pressed

        Parameters
        ----------
        event

        """
        key = event.key()
        self.status_bar.setText('Key ' + hex(key))
        if key in self.key_table.values():
            try:
                cmd = self.key_table.keys()[self.key_table.values().index(key)]
                eval('self.' + cmd)
            except:
                self.status_bar.setText('Command unknown ' + cmd)

    def mousePressEvent(self, event):
        """Called when a mouse button is pressed

        Parameters
        ----------
        event

        """
        pos = self.glarea.mapFromParent(event.pos())
        self.beginx, self.beginy = pos.x(), pos.y()
        self.glarea.occ_view.StartRotation(self.beginx, self.beginy)

    def mouseReleaseEvent(self, event):
        """Called when a mouse button is released

        Parameters
        ----------
        event

        """
        if event.button() == QtCore.Qt.RightButton:  # Selection
            self.glarea.occ_context.Select()
            self.glarea.occ_context.InitSelected()
            if self.glarea.occ_context.MoreSelected():
                if self.glarea.occ_context.HasSelectedShape():
                    self.selected = self.glarea.occ_context.SelectedShape()
            else:
                self.selected = None
            self.make_selection()

    def mouseMoveEvent(self, event):
        """Called when a mouse button is pressed and the mouse is moving

        Parameters
        ----------
        event

        """
        pos = self.glarea.mapFromParent(event.pos())
        x, y = pos.x(), pos.y()
        # Mouse-Controlled Projection
        # ComputedModes are too slow to redraw, so disabled for them
        if (event.buttons() & QtCore.Qt.MidButton) and \
                not self.glarea.occ_view.ComputedMode():
            # Mouse-Controlled Pan
            if event.modifiers() & QtCore.Qt.ShiftModifier:
                self.glarea.occ_view.Pan(x - self.beginx, -y + self.beginy)
                self.beginx, self.beginy = x, y
            else:  # Mouse-Controlled Orbit
                self.glarea.occ_view.Rotation(x, y)
        self.glarea.occ_context.MoveTo(x, y, self.glarea.handle_view)

    # View Functions
    def viewstandard(self, viewtype='front'):
        """Sets up the viewing projection according to a standard set of views

        Parameters
        ----------
        viewtype : str

        """
        if viewtype == 'front':
            self.glarea.occ_view.SetProj(_V3d.V3d_Yneg)
        elif viewtype == 'back':
            self.glarea.occ_view.SetProj(_V3d.V3d_Ypos)
        elif viewtype == 'top':
            self.glarea.occ_view.SetProj(_V3d.V3d_Zpos)
        elif viewtype == 'bottom':
            self.glarea.occ_view.SetProj(_V3d.V3d_Zneg)
        elif viewtype == 'right':
            self.glarea.occ_view.SetProj(_V3d.V3d_Xpos)
        elif viewtype == 'left':
            self.glarea.occ_view.SetProj(_V3d.V3d_Xneg)
        elif viewtype == 'iso':
            self.glarea.occ_view.SetProj(_V3d.V3d_XposYnegZpos)
        elif viewtype == 'iso_back':
            self.glarea.occ_view.SetProj(_V3d.V3d_XnegYposZneg)
        else:
            self.status_bar.setText('Unknown view' + viewtype)

    # def orbitup(self, widget=None, rapid=False):
    def orbitup(self):
        """The observer has moved up

        All orbits orbit with respect to (0,0,0).  That means points
        far from (0,0,0) will translate as you orbit.  I'd prefer it
        orbiting with respect to the center of the screen.  That
        should be possible using the Gravity method from occ_view, but
        pythonocc doesn't implement OCC's Gravity.

        """
        # The better way (pythonocc doesn't implement)
        # gravity = self.glarea.occ_view.Gravity()
        # self.glarea.occ_view.Rotate(0.0, -self.morbit, 0.0,
        #                            gravity[0], gravity[1], gravity[2])
        self.glarea.occ_view.Rotate(0.0, -self.morbit, 0.0)

    # def panup(self, widget=None, rapid=False):
    def panup(self):
        """The scene is panned up"""
        self.glarea.occ_view.Pan(0, -self.glarea.mpan)

    # def orbitdown(self, widget=None, rapid=False):
    def orbitdown(self):
        """The observer has moved down"""
        self.glarea.occ_view.Rotate(0.0, self.morbit, 0.0)

    # def pandown(self, widget=None, rapid=False):
    def pandown(self):
        """The scene is panned down"""
        self.glarea.occ_view.Pan(0, self.glarea.mpan)

    # def orbitright(self, widget=None, rapid=False):
    def orbitright(self):
        """The observer has moved to the right"""
        self.glarea.occ_view.Rotate(-self.morbit, 0.0, 0.0)

    # def panright(self, widget=None, rapid=False):
    def panright(self):
        """The scene is panned right"""
        self.glarea.occ_view.Pan(-self.glarea.mpan, 0)

    # def orbitleft(self, widget=None, rapid=False):
    def orbitleft(self):
        """The observer has moved to the left"""
        self.glarea.occ_view.Rotate(self.morbit, 0.0, 0.0)

    # def panleft(self, widget=None, rapid=False):
    def panleft(self):
        """The scene is panned to the left"""
        self.glarea.occ_view.Pan(self.glarea.mpan, 0)

    # def zoomin(self, widget=None, rapid=False):
    def zoomin(self):
        """Zoom in"""
        self.glarea.occ_view.SetZoom(_math.sqrt(2.0))

    # def zoomout(self, widget=None, rapid=False):
    def zoomout(self):
        """Zoom out"""
        self.glarea.occ_view.SetZoom(_math.sqrt(0.5))

    # def rotateccw(self, widget=None, rapid=False):
    def rotateccw(self):
        """The scene is rotated counter clockwise"""
        self.glarea.occ_view.Rotate(0.0, 0.0, -self.morbit)

    # def rotatecw(self, widget=None, rapid=False):
    def rotatecw(self):
        """The scene is rotated clockwise"""
        self.glarea.occ_view.Rotate(0.0, 0.0, self.morbit)

    # def fit(self, widget=None):
    def fit(self):
        """Fit the scene to the screen"""
        self.glarea.occ_view.ZFitAll()
        self.glarea.occ_view.FitAll()

    # def query(self, widget=None):
    def query(self):
        """Reports the properties of a selection
        Should do something other than print (popup?) ***
        """
        if self.selected is not None:
            if self.selection_type == 'Vertex':
                s = _cm.Vertex(self.selected)
                retval = 'center: ' + str(s.center()) + \
                    '\ntolerance: ' + str(s.tolerance())
            elif self.selection_type == 'Edge':
                s = _cm.Edge(self.selected)
                retval = 'center: ' + str(s.center()) + \
                    '\nlength: ' + str(s.length()) + \
                    '\ntolerance: ' + str(s.tolerance())
            elif self.selection_type == 'Wire':
                s = _cm.Wire(self.selected)
                retval = 'center: ' + str(s.center()) + \
                    '\nlength: ' + str(s.length())
            elif self.selection_type == 'Face':
                s = _cm.Face(self.selected)
                retval = 'center: ' + str(s.center()) + \
                    '\ntype: ' + str(s.type()) + \
                    '\narea: ' + str(s.area()) + \
                    '\ntolerance: ' + str(s.tolerance())
            else:
                retval = 'No properties for type ' + self.selection_type
            print(retval)

    # Direct Call (not from GUI) Functions
    def set_projection(self, vcenter, vout, vup):
        """Set the projection to a custom view given

        vcenter, the scene coordinates in the center of the window,
        vout, the vector from vcenter in scene coordinates out of the window,
        vup, the vector from vcenter in scene coordinates that show straight up

        Parameters
        ----------
        vcenter
        vout
        vup

        """

        projection = _Visual3d_ViewOrientation(
            _Graphic3d.Graphic3d_Vertex(vcenter[0], vcenter[1], vcenter[2]),
            _Graphic3d.Graphic3d_Vector(vout[0], vout[1], vout[2]),
            _Graphic3d.Graphic3d_Vector(vup[0], vup[1], vup[2]))
        self.glarea.occ_view.SetViewOrientation(projection)

    def set_scale(self, scale):
        """Set the screen scale.  I'm not certain, but it looks to me
        like scale is the number of scene-coordinates in the
        x-direction.  For example, if you have a block 8.0 wide in the
        x-direction, and you set the scale to 8.0, the block will
        exactly fill the screen in the x-direction.

        Parameters
        ----------
        scale

        """
        self.glarea.occ_view.SetSize(scale)

    def set_size(self, size):
        """Sets the size of the window in pixels.  Size is a 2-tuple.

        Parameters
        ----------
        size : tuple(int, int)

        """
        # This worked, but adjustSize is limited to 2/3 screen size
        # self.glarea.SCR = size
        # self.glarea.updateGeometry()
        # self.adjustSize()

        # self.glarea.resize didn't work.  This worked but it's based
        # on the non-glarea stuff not growing -- a potential future
        # bug.
        all_size = self.size()
        glarea_size = self.glarea.size()
        dx = all_size.width() - glarea_size.width()
        dy = all_size.height() - glarea_size.height()
        self.resize(size[0] + dx, size[1] + dy)

    def set_background(self, color):
        """Sets the background color.
        color is a 3-tuple with each value from 0.0 to 1.0

        Parameters
        ----------
        color : tuple(float)

        """
        self.glarea.occ_view.SetBackgroundColor(
            _Quantity.Quantity_TOC_RGB, color[0], color[1], color[2])

    def set_foreground(self, color):
        """Sets the default shape color.
        color is a 3-tuple with each value from 0.0 to 1.0

        Parameters
        ----------
        color : tuple(float, float, float)

        """
        self.foreground = color

    def set_triedron(self, state, position='bottom_right',
                     color=(1.0, 1.0, 1.0), size=0.08):
        """Controls the triedron, the little x, y, z coordinate display.

        state (1 or 0) turns it on or off
        position sets the position of the triedron in the window.
        color sets the triedron color (only black or white, currently)
        size sets the triedron size in scene-coordinates

        Parameters
        ----------
        state : int
            1 (on) or 0 (off)
        position : str
            Triedron position
        color : tuple(float, float, float), optional (default is (1., 1., 1.)
        size : float, optional (default is 0.08)
        """
        if not state:
            self.glarea.occ_view.TriedronErase()
        else:
            local_positions = {'bottom_right': _Aspect.Aspect_TOTP_RIGHT_LOWER,
                               'bottom_left': _Aspect.Aspect_TOTP_LEFT_LOWER,
                               'top_right': _Aspect.Aspect_TOTP_RIGHT_UPPER,
                               'top_left': _Aspect.Aspect_TOTP_LEFT_UPPER}
            local_position = local_positions[position]
            # Can't set Triedron color RGB-wise!
            # qcolor = _Quantity.Quantity_Color(
            #    color[0], color[1], color[2], _Quantity.Quantity_TOC_RGB)
            if color == (1.0, 1.0, 1.0):
                qcolor = _Quantity.Quantity_NOC_WHITE
            else:
                qcolor = _Quantity.Quantity_NOC_BLACK
            self.glarea.occ_view.TriedronDisplay(local_position,
                                                 qcolor,
                                                 size,
                                                 _V3d.V3d_ZBUFFER)
                                                 # _V3d.V3d_WIREFRAME)

    # Things to Show Functions
    def display(self, shape, color=None, material='default', transparency=0.0,
                line_type='solid', line_width=1, logging=True):
        """Displays a ccad shape.

        Parameters
        ----------
        shape : ccad shape
        color : tuple(float), optional (default is None)
            The shape color
            color is used for all shape types.  It is a tuple of (R, G, B)
            from 0.0 to 1.0.
        material : str, optional (default is 'default')
            material sets the solid material (unused for non-solids).
            Material can be:

            brass, bronze, copper, gold, pewter, plaster, plastic, silver,
            steel, stone, shiny_plastic, satin, metallized, neon_gnc, chrome,
            aluminum, obsidian, neon_phc, jade, default
        transparency : float, optional (default is 0.)
            transparency sets the solid transparency; 0 is opaque; 1 is
            transparent
        line_type : str, optional (default is 'solid')
            line_type can be solid, dash, or dot for edges and wires
        line_width : int, optional (default is 1)
            line_width sets the edge or wire width in pixels
        logging : bool, optional (default is True)
            logging allows you to keep a list of all shapes displayed

        """
        if hasattr(shape, 'shape'):
            s = shape.shape
        else:
            s = shape
        self.selected_shape = s
        display_shape = {'shape': s,
                         'color': color,
                         'material': material,
                         'transparency': transparency,
                         'line_type': line_type,
                         'line_width': line_width}
        if logging:
            self.display_shapes.append(display_shape)
        aisshape = _AIS.AIS_Shape(s)
        handle_aisshape = aisshape.GetHandle()

        # Set Color
        if not color:
            color = self.foreground
        # print('color', color)

        # drawer = AIS_Drawer()
        # handle_drawer = drawer.GetHandle()

        handle_drawer = aisshape.Attributes()
        drawer = handle_drawer.GetObject()

        qcolor = _Quantity.Quantity_Color(color[0], color[1], color[2],
                                          _Quantity.Quantity_TOC_RGB)

        # Set Point Type
        aspect_point = _Prs3d.Prs3d_PointAspect(_Aspect.Aspect_TOM_PLUS,
                                                qcolor, 1.0)
        handle_aspect_point = aspect_point.GetHandle()
        drawer.SetPointAspect(handle_aspect_point)

        # Set Line Type
        local_line_type = {'solid': _Aspect.Aspect_TOL_SOLID,
                           'dash': _Aspect.Aspect_TOL_DASH,
                           'dot': _Aspect.Aspect_TOL_DOT}[line_type]
        aspect_line = _Prs3d.Prs3d_LineAspect(qcolor,
                                              local_line_type,
                                              line_width)
        handle_aspect_line = aspect_line.GetHandle()
        # drawer = self.glarea.occ_context.DefaultDrawer().GetObject()
        drawer.SetSeenLineAspect(handle_aspect_line)
        drawer.SetWireAspect(handle_aspect_line)

        # Set Shading Type
        aspect_shading = _Prs3d.Prs3d_ShadingAspect()
        handle_aspect_shading = aspect_shading.GetHandle()
        # print('shading color', color)
        aspect_shading.SetColor(qcolor, _Aspect.Aspect_TOFM_BOTH_SIDE)
        local_materials = {'brass': _Graphic3d.Graphic3d_NOM_BRASS,
                           'bronze': _Graphic3d.Graphic3d_NOM_BRONZE,
                           'copper': _Graphic3d.Graphic3d_NOM_COPPER,
                           'gold': _Graphic3d.Graphic3d_NOM_GOLD,
                           'pewter': _Graphic3d.Graphic3d_NOM_PEWTER,
                           'plaster': _Graphic3d.Graphic3d_NOM_PLASTER,
                           'plastic': _Graphic3d.Graphic3d_NOM_PLASTIC,
                           'silver': _Graphic3d.Graphic3d_NOM_SILVER,
                           'steel': _Graphic3d.Graphic3d_NOM_STEEL,
                           'stone': _Graphic3d.Graphic3d_NOM_STONE,
                           'shiny_plastic': _Graphic3d.Graphic3d_NOM_SHINY_PLASTIC,
                           'satin': _Graphic3d.Graphic3d_NOM_SATIN,
                           'metallized': _Graphic3d.Graphic3d_NOM_METALIZED,
                           'neon_gnc': _Graphic3d.Graphic3d_NOM_NEON_GNC,
                           'chrome': _Graphic3d.Graphic3d_NOM_CHROME,
                           'aluminum': _Graphic3d.Graphic3d_NOM_ALUMINIUM,
                           'obsidian': _Graphic3d.Graphic3d_NOM_OBSIDIAN,
                           'neon_phc': _Graphic3d.Graphic3d_NOM_NEON_PHC,
                           'jade': _Graphic3d.Graphic3d_NOM_JADE,
                           'default': _Graphic3d.Graphic3d_NOM_DEFAULT}
        local_material = local_materials[material]
        aspect_shading.SetMaterial(local_material)
        aspect_shading.SetTransparency(transparency)
        drawer.SetShadingAspect(handle_aspect_shading)

        self.glarea.occ_context.Display(handle_aisshape, True)

    def display_vector(self, origin, direction):
        r"""Display a vector starting at origin and going in direction

        Parameters
        ----------
        origin : tuple(float)
            The origin coordinates (x, y, z) of the vector to display
        direction : tuple(float)
            The direction coordinates (x, y, z) of the vector to display

        """
        xo, yo, zo = origin
        xd, yd, zd = direction
        end = (xo + xd, yo + xd, zo + zd)
        xe, ye, ze = end

        # self.glarea.d3d.DisplayVector(gp_Vec(xd, yd, zd), gp_Pnt(xo, yo, zo))

        presentation = Prs3d_Presentation(self.glarea.occ_context.MainPrsMgr().
                                          GetObject().StructureManager())
        arrow = Prs3d_Arrow()
        arrow.Draw(presentation.GetHandle(), gp_Pnt(xe, ye, ze),
                   gp_Dir(gp_Vec(xd, yd, zd)), _math.radians(20),
                   gp_Vec(xd, yd, zd).Magnitude() / 4.)
        presentation.Display()

        e1 = BRepBuilderAPI_MakeEdge(gp_Pnt(xo, yo, zo), gp_Pnt(xe, ye, ze)).\
            Edge()
        self.display(e1, line_width=4)

    def clear(self, display_shapes=True):
        """Clears all shapes from the window

        Parameters
        ----------
        display_shapes : bool, optional (default is True)

        """
        self.select_shape()
        self.glarea.occ_context.PurgeDisplay()
        self.glarea.occ_context.EraseAll()
        if display_shapes:
            self.display_shapes = []

    # Selection Functions
    def _build_hashes(self, htype):
        if htype == 'Face':
            ex_type = _TopAbs.TopAbs_FACE
        elif htype == 'Wire':
            ex_type = _TopAbs.TopAbs_WIRE
        elif htype == 'Edge':
            ex_type = _TopAbs.TopAbs_EDGE
        elif htype == 'Vertex':
            ex_type = _TopAbs.TopAbs_VERTEX
        else:
            print('Error: Unknown hash type', htype)
        if (self.selected_shape.ShapeType == _TopAbs.TopAbs_WIRE and
                    htype == 'Edge'):
            ex = _BRepTools_WireExplorer(self.selected_shape)  # Ordered this way
        else:
            ex = _TopExp_Explorer(self.selected_shape, ex_type)
        self.hashes = []
        self.positions = []
        while ex.More():
            s1 = ex.Current()
            # Calculate hash
            s1_hash = s1.__hash__()
            if s1_hash not in self.hashes:
                self.hashes.append(s1_hash)
                # Calculate position
                if htype == 'Face':
                    f = _cm.Face(s1)
                    c = (' type ' + f.type(), f.center())
                elif htype == 'Wire':
                    w = _cm.Wire(s1)
                    c = ('', w.center())
                elif htype == 'Edge':
                    e = _cm.Edge(s1)
                    c = ('', e.center())
                elif htype == 'Vertex':
                    c = ('', _cm.Vertex(s1).center())
                self.positions.append(c)
            ex.Next()

    def make_selection(self, event=None):
        """Called when a shape is selected

        Parameters
        ----------
        event : <> optional, default is None

        """
        if self.selected is not None:
            if self.selection_type == 'shape':
                self.selected_shape = self.selected
            else:
                h = self.selected.__hash__()
                try:
                    index = self.hashes.index(h)
                except ValueError:
                    index = -1
                if index == -1:
                    self.status_bar.setText('Select shape first.')
                else:
                    status = self.selection_type + ' ' + str(index) + \
                        self.positions[index][0] + \
                        ' at (%.9f, %.9f, %.9f)' % self.positions[index][1]
                    print(status)
                    self.status_bar.setText(status)
                self.selection_index = index

    def select_vertex(self, event=None):
        """Changes to a mode where only vertices can be selected

        Parameters
        ----------
        event : <> optional (default is None)

        """
        self.setCursor(self.WAIT_CURSOR)
        self.glarea.occ_context.CloseAllContexts()
        self.glarea.occ_context.OpenLocalContext()
        self.glarea.occ_context.ActivateStandardMode(_TopAbs.TopAbs_VERTEX)
        self._build_hashes('Vertex')
        self.selection_type = 'Vertex'
        self.setCursor(self.REGULAR_CURSOR)

    def select_edge(self, event=None):
        """Changes to a mode where only edges can be selected

        Parameters
        ----------
        event : <>, optional (default is None)

        """
        self.setCursor(self.WAIT_CURSOR)
        self.glarea.occ_context.CloseAllContexts()
        self.glarea.occ_context.OpenLocalContext()
        self.glarea.occ_context.ActivateStandardMode(_TopAbs.TopAbs_EDGE)
        self._build_hashes('Edge')
        self.selection_type = 'Edge'
        self.setCursor(self.REGULAR_CURSOR)

    def select_wire(self, event=None):
        """Changes to a mode where only wires can be selected

        Parameters
        ----------
        event : <>, optional (default is None)

        """
        self.setCursor(self.WAIT_CURSOR)
        self.glarea.occ_context.CloseAllContexts()
        self.glarea.occ_context.OpenLocalContext()
        self.glarea.occ_context.ActivateStandardMode(_TopAbs.TopAbs_WIRE)
        self._build_hashes('Wire')
        self.selection_type = 'Wire'
        self.setCursor(self.REGULAR_CURSOR)

    def select_face(self, event=None):
        """Changes to a mode where only faces can be selected

        Parameters
        ----------
        event : <>, optional (default is None)

        """
        self.setCursor(self.WAIT_CURSOR)
        self.glarea.occ_context.CloseAllContexts()
        self.glarea.occ_context.OpenLocalContext()
        self.glarea.occ_context.ActivateStandardMode(_TopAbs.TopAbs_FACE)
        self._build_hashes('Face')
        self.selection_type = 'Face'
        self.setCursor(self.REGULAR_CURSOR)

    def select_shape(self, event=None):
        """Changes to a mode where only shapes can be selected

        Parameters
        ----------
        event : <>, optional (default is None)

        """
        self.setCursor(self.WAIT_CURSOR)
        self.glarea.occ_context.CloseAllContexts()
        self.selection_type = 'shape'
        self.setCursor(self.REGULAR_CURSOR)

    # Viewing Mode Functions
    def mode_wireframe(self, widget=None):
        """Changes the display to view shapes as wireframes

        Parameters
        ----------
        widget : <>, optional (default is None)

        """
        if not widget or (widget and widget.get_active()):
            self.glarea.occ_view.SetComputedMode(False)
            self.glarea.occ_context.SetDisplayMode(_AIS.AIS_WireFrame)

    def mode_shaded(self, widget=None):
        """Changes the display to view shapes as shaded (filled) shapes.

        Parameters
        ----------
        widget : <>, optional (default is None)

        """
        if not widget or (widget and widget.get_active()):
            self.glarea.occ_view.SetComputedMode(False)
            self.glarea.occ_context.SetDisplayMode(_AIS.AIS_Shaded)

    def mode_hlr(self, widget=None):
        """Changes the display to view shapes in hidden line removal
        mode, where the part outline, sharp edges, and face barriers
        are shown as lines.

        Parameters
        ----------
        widget : <>, optional (default is None)

        """
        if not widget or (widget and widget.get_active()):
            self.glarea.occ_view.SetComputedMode(True)
            self.glarea.occ_context.SetDisplayMode(_AIS.AIS_ExactHLR)

        # Draws hidden lines
        # presentation = Prs3d_LineAspect(
        #    Quantity_NOC_BLACK, Aspect_TOL_DASH, 3)
        # self.glarea.occ_context.SetHiddenLineAspect(presentation.GetHandle())
        # self.glarea.occ_context.EnableDrawHiddenLine()

    def reset_mode_drawing(self):
        """Call this after mode_drawing to reset everything."""
        self.view_shaded.set_active(True)
        self.clear(0)
        self.glarea.occ_view.SetViewOrientation(self.saved_projection)
        for display_shape in self.display_shapes:
            self.display(display_shape['shape'],
                         display_shape['color'],
                         display_shape['material'],
                         display_shape['transparency'],
                         display_shape['line_type'],
                         display_shape['line_width'],
                         logging=0)

    def mode_drawing(self, widget=None):
        """This is a stand-alone call to make a drafting-like drawing of
        the shape.  It's better than HLR, because HLR shows creases at
        edges where shapes are tangent.  If this must be a menu call,
        pop up a separate window for it.

        Parameters
        ----------
        widget : <>, optional (default is None)

        """
        self.saved_projection = self.glarea.occ_view.ViewOrientation()
        # Graphic3d_Vertex
        vcenter = self.saved_projection.ViewReferencePoint()
        vout = self.saved_projection.ViewReferencePlane()  # Graphic3d_Vector
        vup = self.saved_projection.ViewReferenceUp()  # Graphic3d_Vector
        vout_gp = _gp.gp_Vec(vout.X(), vout.Y(), vout.Z())
        vright = _gp.gp_Vec(vup.X(), vup.Y(), vup.Z())
        vright.Cross(vout_gp)
        projection = _HLRAlgo_Projector(
            _gp.gp_Ax2(_gp.gp_Pnt(vcenter.X(), vcenter.Y(), vcenter.Z()),
                       _gp.gp_Dir(vout.X(), vout.Y(), vout.Z()),
                       _gp.gp_Dir(vright.X(), vright.Y(), vright.Z())))
        hlr_algo = _HLRBRep_Algo()
        handle_hlr_algo = hlr_algo.GetHandle()
        for display_shape in self.display_shapes:
            hlr_algo.Add(display_shape['shape'])
        hlr_algo.Projector(projection)
        hlr_algo.Update()
        hlr_algo.Hide()
        hlr_toshape = _HLRBRep_HLRToShape(handle_hlr_algo)
        vcompound = hlr_toshape.VCompound()
        outlinevcompound = hlr_toshape.OutLineVCompound()
        self.clear(0)
        self.display(vcompound,
                     color=display_shape['color'],
                     line_type=display_shape['line_type'],
                     line_width=display_shape['line_width'],
                     logging=False)
        self.display(outlinevcompound,
                     color=display_shape['color'],
                     line_type=display_shape['line_type'],
                     line_width=display_shape['line_width'],
                     logging=False)
        self.viewstandard(viewtype='top')

    # Helps
    def display_manual(self):
        """Displays the manual"""

        # I couldn't get the directory to work for all platforms.
        if _sys.platform.startswith('linux'):
            updirs = 4
        elif _sys.platform.startswith('win'):
            updirs = 3
        elif _sys.platform.startswith('darwin'):
            updirs = 4  # Not debugged
        else:
            updirs = 0

        doc_directory = _os.path.normpath(
            _os.path.join(
                _os.path.dirname(__file__),
                '../' * updirs + 'share/doc/ccad/html'))
        fullname = _os.path.join(doc_directory, 'contents.html')

        if _os.path.exists(fullname):
            if _sys.platform.startswith('linux'):
                _os.system('xdg-open ' + fullname + ' &')
            elif _sys.platform.startswith('win'):
                _os.system('start ' + fullname)
            elif _sys.platform.startswith('darwin'):
                _os.system('open ' + fullname)
            else:
                self.status_bar.setText(
                    'Warning: viewer not found for ' + _sys.platform)
        else:
            self.status_bar.setText('Warning: cannot find ' + fullname)

    def about(self):
        """Pops up a window about ccad"""
        global version
        QtWidgets.QMessageBox.about(self, 'ccad viewer ' + str(version),
            '\251 Copyright 2015 by Charles Sharman and Others')

    def save(self, name=''):
        """Saves a screen shot

        Parameters
        ----------
        name : str, optional (default is '')

        """
        global app

        if name:
            filename = name
        else:
            filename = str(
                QtWidgets.QFileDialog.getSaveFileName(
                    self,
                    'Save Screen Image',
                    '.',
                    'Image Files (*.png *.bmp *.jpg *.gif)'))

        if filename:
            while app.hasPendingEvents():
                app.processEvents()
            retval = self.glarea.occ_view.Dump(filename)
            if not retval:
                self.status_bar.setText('Error: Could not save ' + filename)
            else:
                self.status_bar.setText('Saved ' + filename)

            # This works and allows higher resolutions
            # pixmap = Image_AlienPixMap()
            # size = self.glarea.size()
            # self.glarea.occ_view.ToPixMap(pixmap, size.width(), size.height())
            # pixmap.Save(TCollection_AsciiString(name))

    def perspective_length(self, distance):
        """Sets the focal length for perspective views

        Parameters
        ----------
        distance : float

        """
        self.glarea.occ_view.SetFocale(distance)

    def perspective_angle(self, angle):
        """Sets the focal length for perspective views

        Parameters
        ----------
        angle : float

        """
        self.glarea.occ_view.SetAngle(angle)

    def quit(self):
        """Closes the viewer"""
        global __name__, app, interactive
        if __name__ == '__main__' or not interactive:
            app.quit()
        else:
            self.close()


class GLWidget(QtWidgets.QWidget):
    """A ccad canvas"""

    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        self.setMouseTracking(True)
        # self.setFocusPolicy(QtCore.Qt.WheelFocus)
        self.setAttribute(QtCore.Qt.WA_PaintOnScreen)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                                 QtWidgets.QSizePolicy.Expanding))
        self.occ_view = None
        self.SCR = (400, 400)

    def start(self, perspective=False):
        r"""

        Parameters
        ----------
        perspective : bool, optional (default is False)

        """

        # Set up the OCC hooks to the OpenGL space
        window_handle = int(self.winId())

        self.d3d = _Display3d(window_handle=window_handle)
        self.d3d.Init(window_handle)

        # GF
        # from OCC.Display.OCCViewer import Viewer3d
        # self.d3d = Viewer3d(window_handle)

        handle_occ_context = self.d3d.GetContext()
        handle_occ_viewer = self.d3d.GetViewer()
        self.handle_view = self.d3d.GetView()
        self.occ_context = handle_occ_context.GetObject()
        self.occ_viewer = handle_occ_viewer.GetObject()
        self.occ_viewer.SetDefaultLights()
        self.occ_viewer.SetLightOn()
        self.occ_view = self.handle_view.GetObject()

    def sizeHint(self):
        r"""<>"""
        return QtCore.QSize(self.SCR[0], self.SCR[1])

    def paintEvent(self, event):
        r"""<>

        Parameters
        ----------
        event

        """
        if self.occ_viewer:
            self.occ_viewer.Redraw()

    def resizeEvent(self, event):
        r"""<>

        Parameters
        ----------
        event

        """
        global app
        x, y = event.size().width(), event.size().height()
        self.SCR = (x, y)
        self.mpan = max(x, y) / 10

        if self.occ_view:
            # There's a race condition here.  The resize must be known
            # to qt before MustBeResized is called.
            while app.hasPendingEvents():
                app.processEvents()
            self.occ_view.MustBeResized()

    def paintEngine(self):
        r"""<>"""
        return None


def view(perspective=False):
    r"""<>

    Parameters
    ----------
    perspective : bool, optional (default is False)

    Returns
    -------
    ViewQt

    """
    global manager, app

    if manager == 'qt':
        if not app:
            app = QtWidgets.QApplication([])
        v1 = ViewQt(perspective)
        return v1
    else:
        print('Error: Manager', manager, 'not supported')


def start():
    r"""<>

    For non-interactive sessions (don't run in ipython)

    """
    global interactive, manager, app
    interactive = False

    if manager == 'qt':
        app.exec_()
    else:
        print('Error: Manager', manager, 'not supported')


if __name__ == '__main__':
    import model as cm
    # view = ViewQt()
    view = view()
    view.set_background((0.35, 0.35, 0.35))
    s1 = cm.sphere(1.0)
    view.display(s1, (0.5, 0.0, 0.0), line_type='solid', line_width=3)
    s2 = cm.box(1, 2, 3)
    view.display(s2,
                 (0.0, 0.0, 0.5),
                 transparency=0.5,
                 line_type='dash',
                 line_width=1)
    start()
