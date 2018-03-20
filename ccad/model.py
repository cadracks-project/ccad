# coding: utf-8

"""
Description
----------
ccad modeller designed to be imported from a python prompt or program.
View README for a full description of ccad.

model.py contains classes and functions for modelling.

Author
------
View AUTHORS.

License
-------
Distributed under the GNU LESSER GENERAL PUBLIC LICENSE Version 3.
View LICENSE for details.
"""
from __future__ import print_function

import logging
import os
import pdb
from os import path as _path
import sys
if sys.version_info[0] < 3:
    PY3 = False
else:
    PY3 = True
import re as _re  # Needed for svg
import math as _math
if PY3 is True:
    from urllib.request import urlopen
else:
    from urllib import urlopen
import imp
import matplotlib.pyplot as plt

import networkx as nx
import numpy as np

# from OCC.ChFi3d import *
# from OCC.BlockFix import *
from OCC.Core.Bnd import Bnd_Box as _Bnd_Box
# from OCC.BOP import *
from OCC.Core.BRep import (BRep_Builder as _BRep_Builder, BRep_Tool as _BRep_Tool,
                      BRep_Tool_Surface as _BRep_Tool_Surface)
from OCC.Core import BRepAlgo as _BRepAlgo
from OCC.Core import BRepAlgoAPI as _BRepAlgoAPI
from OCC.Core.BRepBndLib import brepbndlib_Add as _brepbndlib_Add
from OCC.Core import BRepBuilderAPI as _BRepBuilderAPI
from OCC.Core.BRepCheck import BRepCheck_Analyzer as _BRepCheck_Analyzer
from OCC.Core.BRepFeat import BRepFeat_Gluer as _BRepFeat_Gluer
from OCC.Core import BRepFilletAPI as _BRepFilletAPI
from OCC.Core.BRepGProp import\
    (brepgprop_VolumeProperties as _brepgprop_VolumeProperties,
     brepgprop_LinearProperties as _brepgprop_LinearProperties,
     brepgprop_SurfaceProperties as _brepgprop_SurfaceProperties)
from OCC.Core import BRepOffsetAPI as _BRepOffsetAPI
from OCC.Core import BRepOffset as _BRepOffset
from OCC.Core import BRepPrimAPI as _BRepPrimAPI
from OCC.Core import BRepTools as _BRepTools
from OCC.Core.BRepTools import (breptools_Read as _breptools_Read,
                           breptools_Write as _breptools_Write)
from OCC.Core.GC import (GC_MakeArcOfCircle as _GC_MakeArcOfCircle,
                    GC_MakeArcOfEllipse as _GC_MakeArcOfEllipse)
from OCC.Core.GCPnts import (GCPnts_QuasiUniformDeflection as
                        _GCPnts_QuasiUniformDeflection)
from OCC.Core.Geom import Geom_BezierCurve as _Geom_BezierCurve
from OCC.Core.Geom import Handle_Geom_Plane_DownCast,Geom_Plane
from OCC.Core import GeomAbs as _GeomAbs
from OCC.Core.GeomAdaptor import (GeomAdaptor_Curve as _GeomAdaptor_Curve,
                             GeomAdaptor_Surface as _GeomAdaptor_Surface)
from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline as _GeomAPI_PointsToBSpline
from OCC.Core import gp as _gp
from OCC.Core.GProp import GProp_GProps as _GProp_GProps
from OCC.Core import IFSelect as _IFSelect
from OCC.Core.IGESControl import (IGESControl_Controller as _IGESControl_Controller,
                             IGESControl_Reader as _IGESControl_Reader,
                             IGESControl_Writer as _IGESControl_Writer)
from OCC.Core.Interface import (
            Interface_Static_SetCVal as _Interface_Static_SetCVal,
            Interface_Static_SetIVal as _Interface_Static_SetIVal,
            Interface_Static_SetRVal as _Interface_Static_SetRVal)
from OCC.Core.LocOpe import LocOpe_FindEdges as _LocOpe_FindEdges
from OCC.Core.ShapeFix import ShapeFix_Shape as _ShapeFix_Shape
from OCC.Core import STEPControl as _STEPControl
from OCC.Core.StlAPI import StlAPI_Writer as _StlAPI_Writer
from OCC.Core.TColgp import TColgp_Array1OfPnt as _TColgp_Array1OfPnt
from OCC.Core.TColStd import TColStd_Array1OfReal as _TColStd_Array1OfReal
from OCC.Core import TopAbs as _TopAbs
from OCC.Core.TopoDS import (topods_Edge as _TopoDS_edge,
                        topods_Face as _TopoDS_face,
                        topods_Solid as _TopoDS_solid,
                        topods_Shell as _TopoDS_shell,
                        topods_Compound as _TopoDS_compound,
                        topods_CompSolid as _TopoDS_compsolid,
                        topods_Vertex as _TopoDS_vertex,
                        topods_Wire as _TopoDS_wire,
                        TopoDS_Shape as _TopoDS_Shape)
from OCC.Core import TopoDS as _TopoDS
from OCC.Core.TopExp import (TopExp_Explorer as _TopExp_Explorer,
                        topexp_MapShapesAndAncestors as
                        _TopExp_MapShapesAndAncestors)
from OCC.Core.TopOpeBRep import (TopOpeBRep_FacesIntersector as
                            _TopOpeBRep_FacesIntersector)
from OCC.Core.TopOpeBRepTool import (TopOpeBRepTool_FuseEdges as
                                _TopOpeBRepTool_FuseEdges)
from OCC.Core import TopTools as _TopTools

# Even though this might look like mixing model and display code, X3DomRenderer
# is used to export an html/x3d representation (just like STEP, STL ...)
from OCC.Display.WebGl.x3dom_renderer import X3DomRenderer

logger = logging.getLogger(__name__)

# Shape Functions

def _transform(s1, matrix):
    r"""
    Parameters
    ----------
    s1
    matrix: 3 lines, 4 columns

    Returns
    -------

    """
    m = _gp.gp_Trsf()
    # for i in range(3):
    #     for j in range(4):
    #         print(matrix[i][j])
    m.SetValues(matrix[0][0],
                matrix[0][1],
                matrix[0][2],
                matrix[0][3],
                matrix[1][0],
                matrix[1][1],
                matrix[1][2],
                matrix[1][3],
                matrix[2][0],
                matrix[2][1],
                matrix[2][2],
                matrix[2][3])
    trf = _BRepBuilderAPI.BRepBuilderAPI_Transform(m)
    trf.Perform(s1.shape, True)
    return trf.Shape()


def _translate(s1, pdir):
    r"""Translate s1 in pdir

    Parameters
    ----------
    s1
    pdir

    Returns
    -------
    The translated shape

    """
    m = _gp.gp_Trsf()
    m.SetTranslation(_gp.gp_Vec(pdir[0], pdir[1], pdir[2]))
    trf = _BRepBuilderAPI.BRepBuilderAPI_Transform(m)
    trf.Perform(s1.shape, True)
    return trf.Shape()


def _rotate(s1, pabout, pdir, angle):
    r"""

    Parameters
    ----------
    s1
    pabout : tuple[float]
        The coordinates of a point on the rotation axis
    pdir : tuple[float]
        The axis direction vector coordinates
    angle : float

    Returns
    -------
    The rotated shape


    """
    m = _gp.gp_Trsf()
    m.SetRotation(_gp.gp_Ax1(_gp.gp_Pnt(pabout[0], pabout[1], pabout[2]),
                             _gp.gp_Dir(pdir[0], pdir[1], pdir[2])), angle)
    trf = _BRepBuilderAPI.BRepBuilderAPI_Transform(m)
    trf.Perform(s1.shape, True)
    return trf.Shape()


def _mirror(s1, pabout, pdir):
    r"""

    Parameters
    ----------
    s1
    pabout
    pdir

    Returns
    -------
    The mirrored shape

    """
    m = _gp.gp_Trsf()
    m.SetMirror(_gp.gp_Ax2(_gp.gp_Pnt(pabout[0], pabout[1], pabout[2]),
                           _gp.gp_Dir(pdir[0], pdir[1], pdir[2])))
    trf = _BRepBuilderAPI.BRepBuilderAPI_Transform(m)
    trf.Perform(s1.shape, True)
    return trf.Shape()


def _scale(s1, sx=1.0, sy=1.0, sz=1.0):
    r"""

    Parameters
    ----------
    s1
    sx : float
        Scaling factor in the x direction
    sy : float
        Scaling factor in the y direction
    sz : float
        Scaling factor in the z direction

    Returns
    -------
    The scaled shape

    """
    m = _gp.gp_GTrsf()
    m.SetVectorialPart(_gp.gp_Mat(sx, 0, 0, 0, sy, 0, 0, 0, sz))
    trf = _BRepBuilderAPI.BRepBuilderAPI_GTransform(s1.shape, m, False)
    return trf.Shape()


def transformed(s1, matrix):
    r"""
    Returns a new shape which is s1 translated (moved).

    Parameters
    ----------
    s1
    pdir

    Returns
    -------
    A new shape which is s1 translated (moved).

    """
    s2 = s1.copy()
    s2.transform(matrix)
    return s2


def translated(s1, pdir):
    r"""
    Returns a new shape which is s1 translated (moved).

    Parameters
    ----------
    s1
    pdir

    Returns
    -------
    A new shape which is s1 translated (moved).

    """
    s2 = s1.copy()
    s2.translate(pdir)
    return s2


def rotated(s1, pabout, pdir, angle):
    r"""
    Returns a new shape which is s1 rotated.

    Parameters
    ----------
    s1
    pabout
    pdir
    angle : float
        The rotation angle

    Returns
    -------
    A new shape which is s1 rotated.

    """
    s2 = s1.copy()
    s2.rotate(pabout, pdir, angle)
    return s2


def rotatedx(s1, angle):
    r"""Rotate around x axis

    Parameters
    ----------
    s1
    angle

    Returns
    -------
    A new shape which is s1 rotated about (0.0, 0.0, 0.0) and
    around (1.0, 0.0, 0.0)

    """
    s2 = s1.copy()
    s2.rotatex(angle)
    return s2


def rotatedy(s1, angle):
    r"""Rotate around y axis

    Parameters
    ----------
    s1
    angle

    Returns
    -------
    A new shape which is s1 rotated about (0.0, 0.0, 0.0) and
    around (0.0, 1.0, 0.0)

    """
    s2 = s1.copy()
    s2.rotatey(angle)
    return s2


def rotatedz(s1, angle):
    r"""Rotate around z axis

    Parameters
    ----------
    s1 : Shape
    angle : float

    Returns
    -------
    A new shape which is s1 rotated about (0.0, 0.0, 0.0) and
    around (0.0, 0.0, 1.0)

    """
    s2 = s1.copy()
    s2.rotatez(angle)
    return s2


def mirrored(s1, pabout, pdir):
    r"""
    Returns a new shape which is s1 mirrored.

    Parameters
    ----------
    s1
    pabout
    pdir

    Returns
    -------
    A new shape which is s1 mirrored.

    """
    s2 = s1.copy()
    s2.mirror(pabout, pdir)
    return s2


def mirroredx(s1):
    r"""Mirror about (0.0, 0.0, 0.0) in the x-direction

    Parameters
    ----------
    s1

    Returns
    -------
    A new shape which is s1 mirrored about (0.0, 0.0, 0.0) in
    the x-direction

    """
    s2 = s1.copy()
    s2.mirrorx()
    return s2


def mirroredy(s1):
    r"""Mirror about (0.0, 0.0, 0.0) in the y-direction

    Parameters
    ----------
    s1

    Returns
    -------
    A new shape which is s1 mirrored about (0.0, 0.0, 0.0) in
    the y-direction

    """
    s2 = s1.copy()
    s2.mirrory()
    return s2


def mirroredz(s1):
    r"""Mirror about (0.0, 0.0, 0.0) in the z-direction

    Parameters
    ----------
    s1

    Returns
    -------
    A new shape which is s1 mirrored about (0.0, 0.0, 0.0) in
    the z-direction

    """
    s2 = s1.copy()
    s2.mirrorz()
    return s2


def scaled(s1, sfx, sfy=None, sfz=None):
    r"""
    Returns a new shape which is s1 scaled by a different scale factor
    in all 3 dimensions.  If sfy and sfz are left undefined, all 3
    dimensions are scaled by sfx.

    Parameters
    ----------
    s1
    sfx : float
        X direction scale factor
    sfy : float, optional (default is None)
        Y direction scale factor
    sfz : float, optional (default is None)
        Z direction scale factor

    Returns
    -------
    A new shape which is s1 scaled by a different scale factor
    in all 3 dimensions.  If sfy and sfz are left undefined, all 3
    dimensions are scaled by sfx.

    """
    s2 = s1.copy()
    s2.scale(sfx, sfy, sfz)
    return s2


def scaledx(s1, sfx):
    r"""Scale in the x direction

    Parameters
    ----------
    s1
    sfx : float
        Scaling factor

    Returns
    -------
    A new shape which is s1 scaled by sfx in the x-dimension

    """
    s2 = s1.copy()
    s2.scalex(sfx)
    return s2


def scaledy(s1, sfy):
    r"""Scale in the y direction

    Parameters
    ----------
    s1
    sfy : float
        Scaling factor

    Returns
    -------
    A new shape which is s1 scaled by sfy in the y-dimension

    """
    s2 = s1.copy()
    s2.scaley(sfy)
    return s2


def scaledz(s1, sfz):
    r"""Scale in the z direction

    Parameters
    ----------
    s1
    sfz : float
        Scaling factor

    Returns
    -------
    A new shape which is s1 scaled by sfz in the z-dimension

    """
    s2 = s1.copy()
    s2.scalez(sfz)
    return s2


def reversed_(s1):
    r"""Reverse the orientation

    Parameters
    ----------
    s1

    Returns
    -------
    A new shape which is s1 reversed in orientation.

    """
    s2 = s1.copy()
    s2.reverse()
    return s2


# Face Functions
def _raw_faces_same_domain(f1, f2, skip_fits=0):
    """
    If f1 and f2 are in the same domain, returns 1; otherwise, returns
    0.  FacesIntersector is painfully slow.  I don't think the
    intersection calculation is necessary, but I couldn't find a
    stand-alone OCC domain checker. ***

    Parameters
    ----------
    f1 : face 1
    f2 : face 2
    skip_fits

    Returns
    -------
    1 or 0

    """
    # Didn't Work.  Always empty.
    # fi = TopOpeBRepDS_DataStructure()
    # i1 = fi.AddShape(f1)
    # print fi.ShapeSameDomain(f2).IsEmpty():

    # Pre-screen, since FacesIntersector is slow
    t1 = _GeomAdaptor_Surface(_BRep_Tool_Surface(_TopoDS_face(f1))).GetType()
    t2 = _GeomAdaptor_Surface(_BRep_Tool_Surface(_TopoDS_face(f2))).GetType()
    if t1 != t2:
        return 0
    else:
        if not skip_fits or (skip_fits and t1 <= _GeomAbs.GeomAbs_Torus):
            fi = _TopOpeBRep_FacesIntersector()
            fi.Perform(f1, f2)
            return fi.SameDomain()
        else:
            return 0


def _raw_faces_merge(f1, f2):
    """
    Merges two raw faces in the same domain that share common edge(s)
    into a single face.
    """
    # Attempt with Fuse didn't work
    # new_face = BRepAlgoAPI_Fuse(f1, f2).Shape()
    # new_face = BRepAlgo_Fuse(f1, f2).Shape()
    # print _raw_type(new_face)

    # Attempt with sewing didn't work
    # b = BRepBuilderAPI_Sewing()
    # b.Add(f1)
    # b.Add(f2)
    # b.Perform()
    # new_face = b.SewedShape()
    # print 'new_face type', _raw_type(new_face)
    # new_faces[index] = new_face

    # # This worked, but only sometimes.  Error
    # # reporting wasn't sufficient enough to discover
    # # cause.
    # lfs = TopTools_ListOfShape()
    # print f1.Orientation(), f2.Orientation()
    # Didn't help
    # if f1.Orientation() != f2.Orientation():
    #     f2.Reverse()
    # lfs.Append(f1)
    # lfs.Append(f2)
    # b = TopOpeBRepBuild_FuseFace(TopTools_ListOfShape(), lfs, 1)
    # #b.PerformEdge()
    # b.PerformFace()
    # if not b.IsModified():
    #     print 'Error: Face fusion failed'
    #     #return face(f1), face(f2)
    # lfs = b.LFuseFace()
    # new_face = lfs.First()
    # new_faces[index] = new_face

    # The orientations were derived by trial and error.
    # Expect problems. ***
    other_wires = []
    ow1 = _BRepTools.breptools_OuterWire(_TopoDS_face(f1))
    ow1o = ow1.Orientation()
    ex1w = _TopExp_Explorer(f1, _TopAbs.TopAbs_WIRE)
    while ex1w.More():
        cw = ex1w.Current()
        if cw != ow1:
            cw.Orientation(_TopAbs.TopAbs_Compose(ow1o, cw.Orientation()))
            other_wires.append(cw)
        ex1w.Next()
    ex1e = _BRepTools.BRepTools_WireExplorer(_TopoDS_wire(ow1))
    e1s = []
    while ex1e.More():
        e1s.append(ex1e.Current())
        ex1e.Next()
    ow2 = _BRepTools.breptools_OuterWire(_TopoDS_face(f2))
    ow2o = ow2.Orientation()
    ex2w = _TopExp_Explorer(f2, _TopAbs.TopAbs_WIRE)
    while ex2w.More():
        cw = ex2w.Current()
        if cw != ow2:
            cw.Orientation(_TopAbs.TopAbs_Compose(ow2o, cw.Orientation()))
            other_wires.append(cw)
        ex2w.Next()
    ex2e = _BRepTools.BRepTools_WireExplorer(_TopoDS_wire(ow2))
    e2s = []
    while ex2e.More():
        e2s.append(ex2e.Current())
        ex2e.Next()
    # Find all places where wires are connected
    c1s = []
    c2s = []
    e1_hashes = map(lambda x: x.__hash__(), e1s)
    e2_hashes = map(lambda x: x.__hash__(), e2s)
    for index1, e1 in enumerate(e1_hashes):
        try:
            index2 = e2_hashes.index(e1)
        except:
            index2 = -1
        if index2 > -1:
            c1s.append(index1)
            c2s.append(index2)
    # Can only handle one continuous edge merge now.
    # Multiple edge merges sometimes imply holes and
    # sometimes don't.  Truncate c1s, c2s
    # accordingly. ***
    if len(c1s) == 0:
        # print('No common edges')
        logger.info('No common edges')
    if len(c1s) > 1:
        # print('c1-', c1s, c2s, len(e1s), len(e2s))
        logger.info(str(('c1-', c1s, c2s, len(e1s), len(e2s))))
        min_index = 0
        max_index = 0
        while (max_index < len(c1s) - 1 and
               c1s[max_index + 1] - c1s[max_index] == 1):
            max_index += 1
        if max_index < len(c1s) - 1:
            while (min_index > -(len(c1s) - 1) and
                   c1s[min_index] - c1s[min_index - 1] == 1):
                min_index -= 1
        if min_index < 0:
            c1s = c1s[min_index:] + c1s[:max_index + 1]
            c2s = c2s[min_index:] + c2s[:max_index + 1]
        else:
            c1s = c1s[:max_index + 1]
            c2s = c2s[:max_index + 1]
        # print('c1+', c1s, c2s, len(e1s), len(e2s))
        logger.info(str(('c1+', c1s, c2s, len(e1s), len(e2s))))
    # Create the merged wire
    b = _BRepBuilderAPI.BRepBuilderAPI_MakeWire()
    ds = []
    for count in range(len(e1s)):
        if count in c1s:
            if len(c2s) < len(e2s):  # Make sure they're not all common
                index1 = c1s.index(count)
                count2 = c2s[index1]
                while count2 in c2s:
                    count2 = (count2 + 1) % len(e2s)
                b2 = _BRepBuilderAPI.BRepBuilderAPI_MakeWire()
                while count2 not in c2s:
                    b2.Add(e2s[count2])
                    count2 = (count2 + 1) % len(e2s)
                b.Add(_TopoDS_wire(b2.Wire()))
        else:
            b.Add(e1s[count])
            ds.append(Edge(e1s[count]))
    w = b.Wire()
    b = _ShapeFix_Shape(w)
    b.Perform()
    w = b.Shape()
    # Create the fused face
    s = _BRep_Tool_Surface(_TopoDS_face(f1))
    bf = _BRepBuilderAPI.BRepBuilderAPI_MakeFace(s, _TopoDS_wire(w))
    for other_wire in other_wires:
        if ow1o != ow2o:
            other_wire.Reverse()
        bf.Add(_TopoDS_wire(other_wire))
    f = bf.Face()
    # Fix wire mess orientation mess ups.  It would be
    # nicer to avoid this in the first place
    # above. ***
    # ShapeFix creates new edges, which hinders
    # multiple merges.  Unfortunately, only an
    # orientation fix had problems too. ***
    b = _ShapeFix_Shape(f)
    b.Perform()
    f = b.Shape()
    # b = ShapeFix_Face(f)
    # bw = b.FixWireTool().GetObject()
    # bw.FixReorder()
    # b.FixOrientation()
    # f = b.Face()
    # Since I use f1's surface, I must orient
    # the output the same way.
    if ow1o == _TopAbs.TopAbs_REVERSED:
        f.Reverse()
    return f


# Solid Functions
def fuse(s1, s2, refine=0):
    """
    Performs a boolean fuse between solids s1 and s2 and returns the
    result as a new solid.

    Parameters
    ----------
    s1 : solid 1
    s2 : solid 2
    refine : int(default is 0)

    Returns
    -------
    A new solid that is the fusion of s1 and s2

    """
    # return solid(BRepAlgoAPI_Fuse(s1.shape, s2.shape).Shape())
    b1 = _BRepAlgoAPI.BRepAlgoAPI_Fuse(s1.shape, s2.shape)
    if refine:
        # Fuses edges along the way however doesn't fuse faces
        b1.RefineEdges()
    return Solid(b1.Shape())


def old_fuse(s1, s2):
    """
    Performs a boolean fuse between solids s1 and s2 and returns the
    result as a new solid.  Uses OCC's old Fuse algorithm.

    Parameters
    ----------
    s1 : solid 1
    s2 : solid 2

    Returns
    -------
    A new solid that is the fusion of s1 and s2 with the old OCC fusion algorithm

    """
    return Solid(_BRepAlgo.BRepAlgo_Fuse(s1.shape, s2.shape).Shape())


def cut(s1, s2, refine=0):
    """
    Performs a boolean cut between solids s1 and s2 and returns the
    result as a new solid.

    Parameters
    ----------
    s1
    s2
    refine : int, optional (default is 0)

    Returns
    -------
    A new solid made by cutting s1 by s2

    """
    b1 = _BRepAlgoAPI.BRepAlgoAPI_Cut(s1.shape, s2.shape)
    if refine:
        b1.RefineEdges()
    return Solid(b1.Shape())


def old_cut(s1, s2):
    """
    Performs a boolean cut between solids s1 and s2 and returns the
    result as a new solid.  Uses OCC's old Cut algorithm.

    Parameters
    ----------
    s1
    s2

    Returns
    -------
    A new solid made by cutting s1 by s2 using the old OCC cutting algorithm

    """
    return Solid(_BRepAlgo.BRepAlgo_Cut(s1.shape, s2.shape).Shape())


def common(s1, s2, refine=0):
    """
    Performs a boolean common between solids s1 and s2 and returns the
    result as a new solid.

    Parameters
    ----------
    s1
    s2
    refine : int, optional (default is 0)

    Returns
    -------
    The common solid of s1 and s2 as a new solid

    """
    b1 = _BRepAlgoAPI.BRepAlgoAPI_Common(s1.shape, s2.shape)
    if refine:
        b1.RefineEdges()
    return Solid(b1.Shape())


def old_common(s1, s2):
    """
    Performs a boolean common between solids s1 and s2 and returns the
    result as a new solid.  Uses OCC's old Common algorithm.

    Parameters
    ----------
    s1
    s2

    Returns
    -------
    The common solid of s1 and s2 as a new solid using the old OCC common algorithm

    """
    return Solid(_BRepAlgo.BRepAlgo_Common(s1.shape, s2.shape).Shape())


def _fillet_boolean(b1, rad):
    r"""

    Parameters
    ----------

    b1 :
    rad :

    Returns
    -------

    A solid

    """
    new_edges = b1.SectionEdges()
    b2 = _BRepFilletAPI.BRepFilletAPI_MakeFillet(b1.Shape())
    iterator = _TopTools.TopTools_ListIteratorOfListOfShape(new_edges)
    while iterator.More():
        b2.Add(rad, _TopoDS_edge(iterator.Value()))
        iterator.Next()
    b3 = b2.Shape()
    return Solid(b3)


def fillet_fuse(s1, s2, rad):
    """
    Performs a boolean fuse between s1 and s2 and fillets the newly
    created edges.

    Parameters
    ----------
    s1
    s2
    rad : float

    Returns
    -------
    <tbc>

    """
    if rad > 0.0:
        return _fillet_boolean(
                    _BRepAlgoAPI.BRepAlgoAPI_Fuse(s1.shape, s2.shape), rad)
    else:
        return fuse(s1, s2)


def fillet_cut(s1, s2, rad):
    """
    Performs a boolean cut between s1 and s2 and fillets the newly
    created edges.

    Parameters
    ----------
    s1
    s2
    rad : float

    Returns
    -------
    <tbc>

    """
    if rad > 0.0:
        return _fillet_boolean(
                    _BRepAlgoAPI.BRepAlgoAPI_Cut(s1.shape, s2.shape), rad)
    else:
        return cut(s1, s2)


def fillet_common(s1, s2, rad):
    """
    Performs a boolean common between s1 and s2 and fillets the newly
    created edges.

    Parameters
    ----------
    s1
    s2
    rad : float

    Returns
    -------
    <tbc>

    """
    if rad > 0.0:
        return _fillet_boolean(
                    _BRepAlgoAPI.BRepAlgoAPI_Common(s1.shape, s2.shape), rad)
    else:
        return common(s1, s2)


def _chamfer_boolean(b1, dist):
    r"""

    Parameters
    ----------
    b1
    dist

    Returns
    -------
    solid

    """
    # Doesn't work.  The SectionEdges don't map to faces, it seems. ***
    new_edges = b1.SectionEdges()
    edge_map = _TopTools.TopTools_IndexedDataMapOfShapeListOfShape()
    s = b1.Shape()
    _TopExp_MapShapesAndAncestors(s, _TopAbs.TopAbs_EDGE, _TopAbs.TopAbs_FACE,
                                  edge_map)
    b2 = _BRepFilletAPI.BRepFilletAPI_MakeChamfer(s)
    iterator = _TopTools.TopTools_ListIteratorOfListOfShape(new_edges)
    while iterator.More():
        e1 = iterator.Value()
        f1 = edge_map.FindFromKey(e1).First()
        b2.Add(dist, dist, _TopoDS_edge(e1), _TopoDS_face(f1))
        iterator.Next()
    return Solid(b2.Shape())


def chamfer_fuse(s1, s2, dist):
    """
    Performs a chamfer fuse between s1 and s2 and chamfers the newly
    created edges.

    Parameters
    ----------
    s1
    s2
    dist

    Returns
    -------
    solid

    """
    if dist > 0.0:
        return _chamfer_boolean(
                    _BRepAlgoAPI.BRepAlgoAPI_Fuse(s1.shape, s2.shape), dist)
    else:
        return fuse(s1, s2)


def chamfer_cut(s1, s2, dist):
    """
    Performs a chamfer cut between s1 and s2 and chamfers the newly
    created edges.

    Parameters
    ----------
    s1
    s2
    dist

    Returns
    -------
    solid

    """
    if dist > 0.0:
        return _chamfer_boolean(
                    _BRepAlgoAPI.BRepAlgoAPI_Cut(s1.shape, s2.shape), dist)
    else:
        return cut(s1, s2)


def chamfer_common(s1, s2, dist):
    """
    Performs a chamfer common between s1 and s2 and chamfers the newly
    created edges.

    Parameters
    ----------
    s1
    s2
    dist

    Returns
    -------
    solid

    """
    if dist > 0.0:
        return _chamfer_boolean(
                    _BRepAlgoAPI.BRepAlgoAPI_Common(s1.shape, s2.shape), dist)
    else:
        return common(s1, s2)


def glue(s1, s2, face_pairs=[]):
    """
    Glues solids s1 and s2 together at the face_pairs.  face_pairs is
    a list of tuples.  Each tuple represents face indices that should
    be glued.

    Parameters
    ----------
    s1
    s2
    face_pairs : list, optional (default is an empty list)

    Returns
    -------
    solid

    """
    s1f = s1._raw('Face')
    s2f = s2._raw('Face')
    if len(face_pairs) == 0:
        # print('Error: Haven\'t implemented locate glued faces')
        logger.error('Error: Haven\'t implemented locate glued faces')
        return
        # This was expensive and didn't work.  I believe intersections
        # occurred at edge coincidences.  I may want to try
        # BRepTools_UVBounds as a pre-filter.  I may also want to try
        # Bounds first. ***

        # for i1, f1 in enumerate(s1f):
        #     for i2, f2 in enumerate(s2f):
        #         b = _TopOpeBRep_FacesIntersector()
        #         b.Perform(f1, f2)
        #         if b.SurfacesSameOriented():
        #             face_pairs.append((i1, i2))
        # print(face_pairs)

    b = _BRepFeat_Gluer(s1.shape, s2.shape)
    for face_pair in face_pairs:
        f1 = _TopoDS_face(s1f[face_pair[0]])
        f2 = _TopoDS_face(s2f[face_pair[1]])
        b.Bind(f1, f2)
        common_edges = _LocOpe_FindEdges(f1, f2)
        common_edges.InitIterator()
        while common_edges.More():
            b.Bind(common_edges.EdgeFrom(), common_edges.EdgeTo())
            common_edges.Next()
    return Solid(b.Shape())


def simple_glue(s1, s2, face_pairs=[], tolerance=1e-3):
    """
    Glues solids s1 and s2 together at the face_pairs.  face_pairs is
    a list of tuples.  Each tuple represents faces that should be
    glued.  Unlike glue, each face_pair is expected to exactly
    overlap.  It's more robust than glue, so it was added.

    Parameters
    ----------
    s1 : Solid
    s2 : Solid
    face_pairs : list, optional (default is an empty list)
    tolerance : float, optional (default is 1e-3)

    Returns
    -------

    Solid

    """

    s1f = s1._raw('Face')
    s2f = s2._raw('Face')
    f1rs = []
    f2rs = []
    for face_pair in face_pairs:
        f1rs.append(face_pair[0])
        f2rs.append(face_pair[1])
    f1rs.sort()
    f1rs.reverse()
    f2rs.sort()
    f2rs.reverse()
    for f1r in f1rs:
        del s1f[f1r]
    for f2r in f2rs:
        del s2f[f2r]
    b = _BRepBuilderAPI.BRepBuilderAPI_Sewing(tolerance)
    for f in s1f:
        b.Add(f)
    for f in s2f:
        b.Add(f)
    b.Perform()
    new_shell = b.SewedShape()
    if _raw_type(new_shell) == 'Shell':
        b2 = _BRepBuilderAPI.BRepBuilderAPI_MakeSolid()
        b2.Add(_TopoDS_shell(new_shell))
        return Solid(b2.Solid())
    elif _raw_type(new_shell) == 'compound':
        # print('Warning: simple_glue() returned compound')
        logger.warning('Warning: simple_glue() returned compound')
        s = Solid(new_shell)
        css = s._raw('Shell')
        c = _TopoDS_compound()
        b3 = _BRep_Builder()
        b3.MakeCompound(c)
        for cs in css:
            b2 = _BRepBuilderAPI.BRepBuilderAPI_MakeSolid()
            b2.Add(_TopoDS_shell(cs))
            b3.Add(c, b2.Solid())
        return Solid(c)
    else:
        # print('Warning: Wrong sewed shape after simple_glue():', end='')
        logger.warning('Warning: Wrong sewed shape after simple_glue():')
        _raw_type(new_shell)
        return Solid(new_shell)


# Import Functions
def _convert_import(s):
    r"""

    Parameters
    ----------
    s : Shape

    Returns
    -------

    """
    stype = _raw_type(s)
    logger.debug("stype of raw shape is %s" % stype)
    if stype in ['Solid', 'compound', 'compsolid']:
        return Solid(s)
    elif stype == 'shape':
        msg = "type 'shape' is not supported"
        logger.error(msg)
        # print('Error: Unsupported type', stype)
    else:
        # return eval(stype + '(s)')
        return globals()[stype](s)


def from_brep(name):
    """
    Imports a brep file and returns the shape.

    Parameters
    ----------
    name

    Returns
    -------
    <tbc>

    """
    if _path.exists(name):
        s = _TopoDS_Shape()
        b = _BRep_Builder()
        _breptools_Read(s, name, b)
        return _convert_import(s)
    else:
        # print('Error: Can\'t find', name)
        logger.error('Error: Can\'t find %s' % name)


def from_iges(name):
    """
    Imports an iges file and returns the shape.

    Parameters
    ----------
    name

    Returns
    -------
    <tbc>

    """
    if _path.exists(name):
        reader = _IGESControl_Reader()
        status = reader.ReadFile(name)
        okay = reader.TransferRoots()
        if not okay:
            # print('Warning: Could not translate all shapes')
            logger.warning('Warning: Could not translate all shapes')
        shape = reader.OneShape()
        return _convert_import(shape)
    else:
        # print('Error: Can\'t find', name)
        logger.error('Error: Can\'t find %s' % name)


def from_step(name):
    """
    Imports a step file and returns the shape.

    Parameters
    ----------
    name

    Returns
    -------
    <tbc>

    """
    if _path.exists(name):
        reader = _STEPControl.STEPControl_Reader()
        logger.info("Reading STEP file : %s" % name)
        status = reader.ReadFile(name)
        logger.info("Reading STEP file status : %s" % str(status))
        okay = reader.TransferRoots()
        logger.info("Reading STEP file okay : %s" % str(okay))
        shape = reader.OneShape()
        return _convert_import(shape)
    else:
        msg = "Cannot find STEP file %s" % name
        logger.error(msg)
        # print('Error: Can\'t find', name)


def from_svg(name):
    """
    Imports a 2D svg file, converts each graphics path into a wire,
    and returns a list of wires.

    Warning: Currently only implements a subset of the svg protocol.
    The subset follows.  However, it's pretty easy to add more.
      transforms with
        matrix, translate
      paths with
        a, A, c, C, l, L, m, M, q, Q, z, Z elements

    Warning: Only checked with small inkscape-generated files

    Parameters
    ----------
    name

    Returns
    -------

    """

    def finish_wire():
        r"""<tbc>"""
        if len(local_wire) > 0:
            retval.append(Wire(local_wire))
            # Cannot do local_wire = [] because thinks a new variable
            del local_wire[:]

    def strpt_to_float(strpt):
        r""" string point to float 

        Parameters
        ----------
        strpt

        """
        pt = list(map(lambda x: float(x), strpt.split(',')))
        if not absolute:
            pt = (pt0[0] + pt[0], pt0[1] + pt[1])  # Make absolute
        return pt[0], pt[1]

    def transform_matrix():
        r"""<tbc>"""
        retval = _gp.gp_Mat(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
        for matrix in matrices:
            retval.Multiply(matrix[1])  # second element is the matrix
        return retval

    def transform_pts(transform, pts):
        r"""Matrix transforms and adds a third dimension

        Parameters
        ----------
        transform
        pts

        Returns
        -------

        """
        # Matrix transforms and adds a third dimension
        retval = []
        for pt in pts:
            # retval.append((pt[0], pt[1], 0.0)) # No transform (for debug)
            xyz = _gp.gp_XYZ(pt[0], pt[1], 1.0)
            xyz.Multiply(transform)
            # svg y increases downward; height - xpt[1] corrects
            retval.append((xyz.X(), height - xyz.Y(), 0.0))
        return retval

    def vector_angle(u, v):
        r"""Computes the angle between two vectors

        Parameters
        ----------
        u : vector
        v : vector

        Returns
        -------
        float

        """
        # Computes the angle between two vectors
        if ((u[0] * v[1]) - (u[1] * v[0])) < 0.0:
            s = -1
        else:
            s = 1
        dot = (u[0] * v[0]) + (u[1] * v[1])
        magu = _math.sqrt((u[0] ** 2) + (u[1] ** 2))
        magv = _math.sqrt((v[0] ** 2) + (v[1] ** 2))
        return s * _math.acos(min(1.0, max(-1.0, dot / (magu * magv))))

    height = 0.0
    fp = open(name, 'r')
    entities = []
    matrices = []
    transforms = []
    paths = []
    for line in fp:
        m = _re.match('\s*<([a-zA-Z]+)', line)  # Start of an entity
        if m:
            entities.append(m.group(1))
        if len(entities) > 0 and entities[-1] == 'svg':
            m = _re.match('\s*height="(.+)"', line)
            if m:
                height = float(m.group(1))
        if len(entities) > 1 and entities[-2] == 'g' and entities[-1] == 'path':
            m = _re.match('\s*d="(.+)"', line)  # Should this be multi-line?
            if m:
                paths.append(m.group(1))
                transforms.append(transform_matrix())
        if len(entities) > 0 and entities[-1] == 'g':
            m = _re.match('\s*transform="matrix\((.+)\)"', line)
            if m:
                matrix = map(lambda x: float(x), m.group(1).split(','))
                matrices.append((len(entities), _gp.gp_Mat(matrix[0],
                                                           matrix[2],
                                                           matrix[4],
                                                           matrix[1],
                                                           matrix[3],
                                                           matrix[5],
                                                           0.0, 0.0, 1.0)))
            m = _re.match('\s*transform="translate\((.+)\)"', line)
            if m:
                matrix = map(lambda x: float(x), m.group(1).split(','))
                matrices.append((len(entities), _gp.gp_Mat(1.0,
                                                           0.0,
                                                           matrix[0],
                                                           0.0,
                                                           1.0,
                                                           matrix[1],
                                                           0.0, 0.0, 1.0)))
        m = _re.match('.*/>|.*</', line)  # End of an entity
        if m:
            if entities[-1] == 'g' and len(matrices) > 0 and matrices[-1][0] == len(entities):
                matrices.pop()
            entities.pop()
    fp.close()

    retval = []
    local_wire = []
    cmds = 'aAcChHlLmMqQsStTvVzZ'

    for path, transform in zip(paths, transforms):
        pt0 = (0.0, 0.0)
        absolute = 1
        # command, arguments format
        # ls = filter(lambda x: x != '', re.split('([' + cmds + '])', path))
        ls = path.split()
        index = 0
        while index < len(ls):

            if ls[index].isupper():
                absolute = 1
            else:
                absolute = 0

            cmd = ls[index].lower()

            if cmd == 'm':  # Move
                finish_wire()
                pt0 = strpt_to_float(ls[index + 1])
                index += 2
                pts = [pt0]
                while index < len(ls) and ls[index] not in cmds:
                    pts.append(strpt_to_float(ls[index]))
                    pt0 = pts[-1]
                    index += 1
                if len(pts) > 1:
                    local_wire.append(polygon(transform_pts(transform, pts)))

            elif cmd == 'q':  # Quadratic Bezier
                index += 1
                while index < len(ls) and ls[index] not in cmds:
                    pts = [pt0,
                           strpt_to_float(ls[index]),
                           strpt_to_float(ls[index + 1])]
                    pt0 = pts[-1]
                    local_wire.append(bezier(transform_pts(transform, pts)))
                    index += 2

            elif cmd == 'c':  # Cubic Bezier
                index += 1
                while index < len(ls) and ls[index] not in cmds:
                    pts = [pt0,
                           strpt_to_float(ls[index]),
                           strpt_to_float(ls[index + 1]),
                           strpt_to_float(ls[index + 2])]
                    pt0 = pts[-1]
                    local_wire.append(bezier(transform_pts(transform, pts)))
                    index += 3

            elif cmd == 'l':  # Line
                index += 1
                pts = [pt0]
                while index < len(ls) and ls[index] not in cmds:
                    pts.append(strpt_to_float(ls[index]))
                    pt0 = pts[-1]
                    index += 1
                local_wire.append(polygon(transform_pts(transform, pts)))

            elif cmd == 'a':  # Elliptical Arc
                index += 1
                while index < len(ls) and ls[index] not in cmds:
                    x1, y1 = pt0
                    rx, ry = map(lambda x: float(x), ls[index].split(','))
                    phi = _math.radians(float(ls[index + 1]))
                    fa = int(ls[index + 2])
                    fs = int(ls[index + 3])
                    x2, y2 = strpt_to_float(ls[index + 4])
                    index += 5

                    # Algorithm copied from W3C SVG 1.1 Appendix F
                    rx = abs(rx)
                    ry = abs(ry)
                    if rx == 0.0 or ry == 0.0:
                        pts = [(x1, y1), (x2, y2)]
                        local_wire.append(
                            polygon(transform_pts(transform, pts)))
                    else:
                        cosphi = _math.cos(phi)
                        sinphi = _math.sin(phi)
                        x = (x1 - x2) / 2
                        y = (y1 - y2) / 2
                        x1p = (cosphi * x) + (sinphi * y)
                        y1p = (-sinphi * x) + (cosphi * y)
                        # Correct for out-of-range radii
                        l = _math.sqrt((x1p ** 2) / (rx ** 2) +
                                       (y1p ** 2) / (ry ** 2))
                        if l > 1.0:
                            rx *= l
                            ry *= l

                        if fa == fs:
                            s = -1
                        else:
                            s = 1
                        c = s * _math.sqrt(max(0.0,
                                               (rx ** 2) * (ry ** 2) -
                                               (rx ** 2) * (y1p ** 2) -
                                               (ry ** 2) * (x1p ** 2)) /
                                           ((rx ** 2) * (y1p ** 2) +
                                            (ry ** 2) * (x1p ** 2)))
                        cxp = c * rx * y1p / ry
                        cyp = c * (-ry) * x1p / rx
                        cx = (cosphi * cxp) - (sinphi * cyp) + (x1 + x2) / 2
                        cy = (sinphi * cxp) + (cosphi * cyp) + (y1 + y2) / 2
                        v1 = (1.0, 0.0)
                        v2 = ((x1p - cxp) / rx, (y1p - cyp) / ry)
                        v3 = ((-x1p - cxp) / rx, (-y1p - cyp) / ry)
                        theta = vector_angle(v1, v2)
                        dtheta = vector_angle(v2, v3) % (2 * _math.pi)
                        if fs == 0 and dtheta > 0.0:
                            dtheta -= 2 * _math.pi
                        elif fs == 1 and dtheta < 0.0:
                            dtheta += 2 * _math.pi
                        if dtheta < 0.0:
                            theta1 = theta + dtheta
                            theta2 = theta
                        else:
                            theta1 = theta
                            theta2 = theta + dtheta
                        a = translated(
                            rotatedz(arc_ellipse(rx, ry, theta1, theta2), phi),
                            (cx, cy, 0.0))
                        a.bounds()
                        # Transform a
                        m = _gp.gp_Trsf()
                        # There's probably a better way to convert a
                        # matrix to a transformation
                        m.SetValues(transform.Value(1, 1),
                                    transform.Value(1, 2),
                                    0.0,
                                    transform.Value(1, 3),
                                    transform.Value(2, 1),
                                    transform.Value(2, 2),
                                    0.0,
                                    transform.Value(2, 3),
                                    0.0,
                                    0.0,
                                    transform.Value(1, 1),
                                    0.0, 1e-16, 1e-7)  # unsure of TolAng and TolDist
                        trf = _BRepBuilderAPI.BRepBuilderAPI_Transform(m)
                        trf.Perform(a.shape, 1)
                        a.shape = trf.Shape()
                        # Convert y to height - y
                        a.mirrory()
                        a.translate((0.0, height, 0.0))
                        local_wire.append(a)

                        pt0 = (x2, y2)

            elif cmd == 'z':  # Close path
                finish_wire()
                index += 1

            elif cmd in cmds:  # Need to do these some time
                # print('Error:', cmd, 'not implemented in path:', path)
                logger.error(str(('Error:', cmd, 'not implemented in path:', path)))
                sys.exit()

            else:
                # print('Error: svg path type unknown', cmd)
                logger.error(str(('Error: svg path type unknown', cmd)))
                sys.exit()

        finish_wire()
    return retval


def _raw_type(raw_shape):
    r"""

    Parameters
    ----------
    raw_shape

    Returns
    -------
    str : the shape type

    """
    raw_types = {_TopAbs.TopAbs_COMPOUND: 'compound',
                 _TopAbs.TopAbs_COMPSOLID: 'compsolid',
                 _TopAbs.TopAbs_SOLID: 'Solid',
                 _TopAbs.TopAbs_SHELL: 'Shell',
                 _TopAbs.TopAbs_FACE: 'Face',
                 _TopAbs.TopAbs_WIRE: 'Wire',
                 _TopAbs.TopAbs_EDGE: 'Edge',
                 _TopAbs.TopAbs_VERTEX: 'Vertex',
                 _TopAbs.TopAbs_SHAPE: 'shape'}
    try:
        return raw_types[raw_shape.ShapeType()]
    except KeyError:
        msg = "_raw_type was called with an unknown type"
        logger.warning(msg)
        return 'unknown'

# Classes
class Part(object):
    r"""Part class

    Notes
    -----

    A Part could be n solids : e.g. a bearing has two rings and n balls

    """

    def __init__(self, geometry, origin):
        self._geometry = geometry
        self.origin = origin

    @classmethod
    def from_step(cls, step_filename):
        r"""Create a Part instance from a STEP file

        Parameters
        ----------
        step_filename : str
            Path to the STEP file

        Returns
        -------
        Part : a new Part object created from the STEP file

        Raises
        ------
        IOError : if the STEP file cannot be found

        """
        # if not os.path.isfile(step_filename):
        #     msg = "STEP part file does not exist"
        #     logger.error(msg)
        #     raise IOError(msg)
        # TODO : make sure is it not a compound or a compsolid
        #      : actually, why not? e.g. bearing
        solid = from_step(step_filename)
        return cls(solid, origin=step_filename)

    @classmethod
    def from_py(cls, py_filename):
        r"""Create a Part instance from a Python file

        Parameters
        ----------
        py_filename : str
            Path to the Python generator module
            that has a 'part' variable in its global namespace

        Returns
        -------
        Part : a new Part object created from the library

        Raises
        ------
        IOError : if the Python generator module cannot be found
        ValueError : if the Python generator does not have a 'part' variable
                     in its global namespace

        """
        # if not os.path.isfile(py_filename):
        #     msg = "Python part file does not exist"
        #     logger.error(msg)
        #     raise IOError(msg)

        # TODO : PY3 versions (imp is not PY3 compliant)
        module = imp.load_source(os.path.splitext(py_filename)[0], py_filename)
        if not hasattr(module, 'part'):
            raise ValueError("The Python module should have a 'part' variable")
        solid = module.part
        return cls(solid, origin=py_filename)

    @classmethod
    def from_library(cls, url, name):
        r"""

        Parameters
        ----------
        url : str
            The library url
        name : str
            The name of the part in the library

        Returns
        -------
        Part : a new Part object created from the library

        Raises
        ------
        IOError : if the url of the library is wrong
        SyntaxError : if the name of the part does not exist

        """
        response = urlopen("%s/%s.py" % (url, name))

        with open("tmp.py", "wb") as tmp_py_file:
            for line in response.readlines():
                tmp_py_file.write(line)
        # TODO : PY3 versions (imp is not PY3 compliant)
        module = imp.load_source(name, "tmp.py")
        solid = module.part
        anchors = module.anchors
        logger.debug("solid has type: %s" % type(solid))
        os.remove("tmp.py")
        return cls(solid, origin="%s/%s.py" % (url, name)), anchors

    @property
    def geometry(self):
        r"""Part geometry

        Returns
        -------
        Solid

        """
        return self._geometry


class Assembly(object):
    r"""

    Parameters
    ----------
    shape
    origin : str
        The file or script the assembly was created from
    direct : bool, optional(default is False)
        If True, directly use the point cloud of the Shell
        If False, iterate the faces, wires and then vertices

    TODO : To Be remove ( redundant with recersy)

    """
    def __init__(self, shape, origin=None, direct=False):
        self.shape = shape
        self.G = nx.DiGraph()
        self.G.pos = dict()
        self.origin = origin

        shells = self.shape.subshapes("Shell")
        logger.info("%i shells in assembly" % len(shells))

        for k, shell in enumerate(shells):
            logger.info("Dealing with shell nb %i" % k)
            self.G.pos[k] = shell.center()
            pcloud = np.array([[]])
            pcloud.shape = (3, 0)

            if direct:
                vertices = shell.subshapes("Vertex")
                logger.info("%i vertices found for direct method")
                for vertex in vertices:
                    point = np.array(vertex.center())[:, None]
                    pcloud = np.append(pcloud, point, axis=1)
            else:
                faces = shell.subshapes("Face")

                for face in faces:
                    face_type = face.type()
                    wires = face.subshapes("Wire")

                    for wire in wires:
                        vertices = wire.subshapes("Vertex")

                        for vertex in vertices:
                            point = np.array(vertex.center())[:, None]
                            pcloud = np.append(pcloud, point, axis=1)

                    if face_type == "plane":
                        pass
                    if face_type == "cylinder":
                        pass

            self.G.add_node(k, pcloud=pcloud, shape=shell)

    @classmethod
    def from_step(cls, filename, direct=False):
        r"""Create an Assembly instance from a STEP file

        Parameters
        ----------
        filename : str
            Path to the STEP file
        direct : bool, optional(default is False)
            If True, directly use the point cloud of the Shell
            If False, iterate the faces, wires and then vertices

        Returns
        -------
        Assembly : the new Assembly object created from a STEP file

        """
        solid = from_step(filename)
        return cls(solid, origin=filename, direct=direct)

    def tag_nodes(self):
        r"""Add computed data to each node f the assembly"""
        for k in self.G.node:
            sig, V, ptm, q, vec, ang = signature(self.G.node[k]['pcloud'])
            self.G.node[k]['name'] = sig
            self.G.node[k]['R'] = V
            self.G.node[k]['ptm'] = ptm
            self.G.node[k]['q'] = q

    def write_components(self):
        r"""Write components of the assembly to their own step files in a
        subdirectory of the folder containing the original file"""
        if os.path.isfile(self.origin):
            directory = os.path.dirname(self.origin)
            basename = os.path.basename(self.origin)
            subdirectory = os.path.join(directory,
                                        os.path.splitext(basename)[0])
            if not os.path.isdir(subdirectory):
                os.mkdir(subdirectory)
        else:
            msg = "The components of the assembly should already exist"
            raise ValueError(msg)

        for k in self.G.node:
            sig, V, ptm, q, vec, ang = signature(self.G.node[k]['pcloud'])
            shp = self.G.node[k]['shape']
            filename = sig + ".stp"
            if not os.path.isfile(filename):
                shp.translate(-ptm)
                shp.rotate(np.array([0, 0, 0]), vec, ang)
                filename = os.path.join(subdirectory, filename)
                shp.to_step(filename)

    def __repr__(self):
        st = self.shape.__repr__()+'\n'
        st += self.G.__repr__()+'\n'
        return st


class Shape(object):
    """
        A base class for all shapes:
            edge
            wire
            face
            shell
            solid
    """

    def _raw_type(self):
        return _raw_type(self.shape)

    def to_brep(self, name):
        """
        Exports the shape in .brep format

        Parameters
        ----------
        name

        """
        _breptools_Write(self.shape, name)

    def to_iges(self, name, **options):
        """
        Exports the shape in .igs format.  It supports the following options:

        Parameters
        ----------
        name : str

        **options:
            precision_mode:
                -1: uncertainty is set to the minimum tolerance of all shapes
                0 (Default): uncertainty is set to the average tolerance of all
                shapes
                1: uncertainty is set to the maximum tolerance of all shapes
                2: uncertainty is set to precision_value

            precision_value (0.0001 Default): for precision_mode 2, uncertainty is
            set to this

            brep_mode:
                0 (Default): faces translated to IGES 144 entities (no brep)
                1: faces translated to IGES 510 entities (will have brep)

            convert_surface_mode:
                0 (Default): elementary surfaces are written as surfaces of
                revolution
                1: elementary surfaces are converted to corresponding IGES surfaces

            units:
                'MM': millimeters
                'INCH': inches

            author: the author of the file

            sending_company:

            receiving_company:

            product: the product creating the file

        """

        # Setup
        c = _IGESControl_Controller()
        c.Init()
        if 'units' in options:
            units = options['units']
        else:
            units = 'MM'
        if 'brep_mode' in options:
            brep_mode = options['brep_mode']
        else:
            brep_mode = 0
        w = _IGESControl_Writer(units, brep_mode)

        # Parse Options
        if 'precision_mode' in options:
            _Interface_Static_SetIVal('write.precision.mode',
                                      options['precision_mode'])
        if 'precision_value' in options:
            _Interface_Static_SetRVal('write.precision.val',
                                      options['precision_value'])
        # if 'brep_mode' in options:
        #    # Didn't work here
        #    _Interface_Static_SetIVal('write.iges.brep.mode',
        #                              options['brep_mode'])
        if 'convert_surface_mode' in options:
            if options['convert_surface_mode'] == 1:
                value = 'On'
            else:
                value = 'Off'
            _Interface_Static_SetCVal('write.convertsurface.mode', value)
        # if 'units' in options:
        #    _Interface_Static_SetCVal('write.step.unit', options['units'])
        if 'author' in options:
            _Interface_Static_SetCVal('write.iges.header.author',
                                      options['author'])
        if 'sending_company' in options:
            _Interface_Static_SetCVal('write.iges.header.company',
                                      options['sending_company'])
        if 'receiving_company' in options:
            _Interface_Static_SetCVal('write.iges.header.receiver',
                                      options['receiveing_company'])
        if 'product' in options:
            _Interface_Static_SetCVal('write.iges.header.product',
                                      options['product'])

        # Write
        okay = w.AddShape(self.shape)
        if not okay:
            # print('Warning: Could not translate all shapes')
            logger.warning('Warning: Could not translate all shapes')
        w.Write(name)

    def to_step(self, name, **options):
        """
        Exports the shape in .stp format.

        Parameters
        ----------
        name : str

        **options :

            precision_mode:
                -1: uncertainty is set to the minimum tolerance of all shapes
                0 (Default): uncertainty is set to the average tolerance of all
                shapes
                1: uncertainty is set the the maximum tolerance of all shapes
                2: uncertainty is set to precision_value

            precision_value (0.0001 Default): for precision_mode 2, uncertainty is
            set to this

            assembly:
                0 (Default): writes without assemblies
                1: writes with assemblies
                2: TopoDS_Compounds are written as assemblies

            schema: defines the version of schema
                1 (Default): AP214CD
                2: AP214DIS
                3: AP203
                4: AP214IS

            surface_curve_mode:
                0: write without pcurves
                1 (Default): write with pcurves

            transfer_mode:
                0 (Default): automatic
                1: transfer to manifold solid brep
                2: transfer to faceted brep (only for planar faces and linear
                    edges)
                3: transfer to shell based surface model
                4: transfer to geometric curve set

            units:
                'MM': millimeters
                'INCH': inches

            product: the product creating the file

        """

        # Setup
        c = _STEPControl.STEPControl_Controller()
        c.Init()
        w = _STEPControl.STEPControl_Writer()

        # Parse Options
        if 'precision_mode' in options:
            _Interface_Static_SetIVal('write.precision.mode',
                                      options['precision_mode'])
        if 'precision_value' in options:
            _Interface_Static_SetRVal('write.precision.val',
                                      options['precision_value'])
        if 'assembly' in options:
            _Interface_Static_SetIVal('write.step.assembly',
                                      options['assembly'])
        if 'schema' in options:
            _Interface_Static_SetCVal('write.step.schema',
                                      str(options['schema']))
            w.Model(True)
        if 'product' in options:
            _Interface_Static_SetCVal('write.product.name',
                                      options['product'])
        if 'surface_curve_mode' in options:
            _Interface_Static_SetIVal('write.surfacecurve.mode',
                                      options['surface_curve_mode'])
        if 'units' in options:
            _Interface_Static_SetCVal('write.step.unit', options['units'])
        if 'transfer_mode' in options:
            transfer_modes = [_STEPControl.STEPControl_AsIs,
                              _STEPControl.STEPControl_ManifoldSolidBrep,
                              _STEPControl.STEPControl_FacetedBrep,
                              _STEPControl.STEPControl_ShellBasedSurfaceModel,
                              _STEPControl.STEPControl_GeometricCurveSet]
            transfer_mode = transfer_modes[options['transfer_mode']]
        else:
            transfer_mode = _STEPControl.STEPControl_AsIs

        # Write
        okay = w.Transfer(self.shape, transfer_mode)
        if okay in [_IFSelect.IFSelect_RetError,
                    _IFSelect.IFSelect_RetFail,
                    _IFSelect.IFSelect_RetStop]:
            # print('Error: Could not translate shape to step')
            logger.error('Error: Could not translate shape to step')
        else:
            w.Write(name)

    def to_html(self, filename_html,color=(0.65,0.65,0.65)):
        r"""Generates an html file to view the Shape in the browser

        Parameters
        ----------
        filename_html : str
            name of the html file
        color : tuple
            (0.65,0.65,0.65)
        """
        class X3DomRendererCustomized(X3DomRenderer):
            r"""Customized version of X3DomRenderer where the html file name can
            be specified"""
            def __init__(self, path_, background_color="#123345"):
                # Intentionally not calling super constructor
                super(X3DomRendererCustomized,self).__init__()
                self._background_color = background_color
                name_no_extension, _ = os.path.splitext(os.path.basename(path_))
                self._path = os.path.dirname(path_)
                self._x3d_filename = os.path.join(self._path,
                                                  '%s.x3d' % name_no_extension)
                self._html_filename = path_

        renderer = X3DomRendererCustomized(path_=filename_html)
        renderer.DisplayShape(self.shape,
                              vertex_shader=None,
                              fragment_shader=None,
                              export_edges=False,
                              color=color,
                              specular_color=(1, 1, 1),
                              shininess=0.9,
                              transparency=0.,
                              line_color=(0, 0., 0.),
                              line_width=2.,
                              mesh_quality = 1.)

        renderer.GenerateHTMLFile()

    def transform(self, matrix):
        """
        moves the shape

        Parameters
        ----------
        pdir

        """
        self.shape = _transform(self, matrix)

    def translate(self, pdir):
        """
        moves the shape

        Parameters
        ----------
        pdir

        """
        self.shape = _translate(self, pdir)

    def rotate(self, pabout, pdir, angle):
        """
        rotates the shape

        Parameters
        ----------
        pabout
        pdir
        angle : float

        """
        self.shape = _rotate(self, pabout, pdir, angle)

    def rotatex(self, angle):
        """
        rotates the shape about (0.0, 0.0, 0.0) around (1.0, 0.0, 0.0)

        Parameters
        ----------
        angle : float

        """
        self.shape = _rotate(self, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle)

    def rotatey(self, angle):
        """
        rotates the shape about (0.0, 0.0, 0.0) around (0.0, 1.0, 0.0)

        Parameters
        ----------
        angle : float

        """
        self.shape = _rotate(self, (0.0, 0.0, 0.0), (0.0, 1.0, 0.0), angle)

    def rotatez(self, angle):
        """
        rotates the shape about (0.0, 0.0, 0.0) around (1.0, 0.0, 0.0)

        Parameters
        ----------
        angle : float

        """
        self.shape = _rotate(self, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle)

    def mirror(self, pabout, pdir):
        """
        mirrors the shape

        Parameters
        ----------
        pabout
        pdir

        """
        self.shape = _mirror(self, pabout, pdir)

    def mirrorx(self):
        """
        mirrors the shape about (0.0, 0.0, 0.0) in the x-direction
        """
        self.shape = _mirror(self, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))

    def mirrory(self):
        """
        mirrors the shape about (0.0, 0.0, 0.0) in the y-direction
        """
        self.shape = _mirror(self, (0.0, 0.0, 0.0), (0.0, 1.0, 0.0))

    def mirrorz(self):
        """
        mirrors the shape about (0.0, 0.0, 0.0) in the z-direction
        """
        self.shape = _mirror(self, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))

    def scale(self, sfx, sfy=None, sfz=None):
        """
        scales the shape by scale factor sfx in all 3 dimensions.  If
        all 3 scale factors are specified, scales x, y, z
        independently.

        Parameters
        ----------
        sfx : float
        sfy : float, optional (default is None)
            Scaling factor on the y axis
        sfz : float, optional (default is None)
            Scaling factor on the z axis

        """
        if sfy and sfz:
            self.shape = _scale(self, sfx, sfy, sfz)
        else:
            self.shape = _scale(self, sfx, sfx, sfx)

    def scalex(self, sfx):
        """
        scales the shape by scale factor sfx in the x-dimension

        Parameters
        ----------
        sfx : float

        """
        self.shape = _scale(self, sfx, 1.0, 1.0)

    def scaley(self, sfy):
        """
        scales the shape by scale factor sfy in the y-dimension

        Parameters
        ----------
        sfy : float

        """
        self.shape = _scale(self, 1.0, sfy, 1.0)

    def scalez(self, sfz):
        """
        scales the shape by scale factor sfz in the z-dimension

        Parameters
        ----------
        sfz : float

        """
        self.shape = _scale(self, 1.0, 1.0, sfz)

    def reverse(self):
        """
        Reverses a shape's orientation
        """
        self.shape.Reverse()

    def _raw(self, raw_type):
        """
        Returns a list of all the OCC vertices, edges, wires, faces,
        shells, or solids (dependent on raw_type) in the shape.

        Parameters
        ----------
        raw_type : str

        """
        raw_types = {'Vertex': _TopAbs.TopAbs_VERTEX,
                     'Edge': _TopAbs.TopAbs_EDGE,
                     'Wire': _TopAbs.TopAbs_WIRE,
                     'Face': _TopAbs.TopAbs_FACE,
                     'Shell': _TopAbs.TopAbs_SHELL,
                     'Solid': _TopAbs.TopAbs_SOLID,
                     'Compound':_TopAbs.TopAbs_COMPOUND,
                     'Compsolid':_TopAbs.TopAbs_COMPSOLID}
        # This returns OCC types, not ccad types
        if self.stype == 'Wire' and raw_type == 'Edge':
            # Ordered this way
            ex = _BRepTools.BRepTools_WireExplorer(_TopoDS_wire(self.shape))
        else:
            ex = _TopExp_Explorer(self.shape, raw_types[raw_type])
        hashes = []
        retval = []
        while ex.More():
            s1 = ex.Current()
            s1_hash = s1.__hash__()
            if s1_hash not in hashes:
                hashes.append(s1_hash)
                retval.append(s1)
            ex.Next()
        return retval

    def _valid_subshapes(self, include_top=False):
        r"""

        Parameters
        ----------
        include_top

        Returns
        -------
        list[str] : the list of valid subshapes

        """
        types = ['Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid']
        self_index = types.index(self.stype)
        if include_top:
            self_index += 1
        return types[:self_index]

    def _valid_subshape(self, stype):
        r"""

        Parameters
        ----------
        stype

        Returns
        -------
        bool

        """
        if stype in self._valid_subshapes():
            return True
        else:
            # print('Warning: ' + stype + ' is not a subshape of ' + self.stype)
            msg = 'Warning: ' + stype + ' is not a subshape of ' + self.stype
            logger.warning(msg)
            return False

    def subshapes(self, stype):
        """
        Returns a list of all the vertices, edges, wires, faces,
        shells, or solids (dependent on stype) in the shape.

        Parameters
        ----------
        stype

        Returns
        -------
        list[Shape of subclass of Shape]

        """
        retval = list()
        if self._valid_subshape(stype):
            retval = [globals()[stype](raw_shape)
                      for raw_shape in self._raw(stype)]
        return retval

    def copy(self):
        """
        Copies the shape and returns the copied shape
        """
        s = _BRepBuilderAPI.BRepBuilderAPI_Copy(self.shape).Shape()
        # return eval(self.stype + '(s)')
        return globals()[self.stype](s)

    def bounds(self):
        """
        Puts a box around the shape and returns the minimum and
        maximum coordinates in a 6-tuple.

        It currently returns a box which extends far beyond the real
        boundaries.  It seems to be an OCC problem, but uncertain ***

        Returns
        -------
        tuple[float, float, float, float, float, float]
            The bounding box coordinates

        """
        b1 = _Bnd_Box()
        _brepbndlib_Add(self.shape, b1)
        return b1.Get()

    def center(self):
        """
        Finds the center of mass of the shape.
        """
        # print('Center not defined for', self.stype)
        logger.error('Center not defined for %s' % str(self.stype))
        sys.exit()

    def subcenters(self, stype):
        """
        Iterates over every subshape (as selected by stype) and
        returns the center of each subshape.  For example,
        s.subcenters('face') finds the centers of the faces of the
        shape.

        Parameters
        ----------
        stype

        """
        centers = list()
        if self._valid_subshape(stype):
            centers = [globals()[stype](s).center() for s in self._raw(stype)]
        return centers

    def check(self):
        """
        Performs a BRep check.  Returns 1 if its okay.  Returns 0
        otherwise.  I'd like to generate a report on 0, but it
        requires an SStream, which pythonocc doesn't seem to handle
        right now.  ***
        """
        b = _BRepCheck_Analyzer(self.shape)
        return b.IsValid()

    def fix(self, precision=None, max_tolerance=None, min_tolerance=None):
        """
        Performs Shape Healing.  It didn't work on all cases I
        tested.  Perhaps it needs more help (precision and
        tolerance)? ***

        Parameters
        ----------
        precision : float, optional (default is None)
        max_tolerance : float, optional (default is None)
        min_tolerance : float, optional (default is None)

        """
        b = _ShapeFix_Shape(self.shape)
        if precision is not None:
            b.SetPrecision(precision)
        if max_tolerance is not None:
            b.SetMaxTolerance(max_tolerance)
        if min_tolerance is not None:
            b.SetMinTolerance(min_tolerance)
        b.Perform()
        self.shape = b.Shape()

    def dump(self, flat=True, _level=0):
        """
        Print the details of an object from the top down.

        If flat is False, dumps a hierarchy form.
        _level is used for the recursion; don't touch it.

        Parameters
        ----------
        flat : bool, optional (default is True)
        _level : int, optional (default is 0)

        """
        types = self._valid_subshapes()
        types.reverse()
        if not flat and len(types) > 0:
            types = [types[0]]
        for t in types:
            ss = self.subshapes(t)
            for count, s in enumerate(ss):
                x, y, z = s.center()
                if t in ['Vertex', 'Edge', 'Face']:
                    suffix = ' tolerance: %.4e' % s.tolerance()
                else:
                    suffix = ''
                msg = '.' * _level + '%s%d location: (%.6f,%.6f,%.6f)%s' % \
                                     (t, count, x, y, z, suffix)
                # print('.' * _level + '%s%d location: (%.6f,%.6f,%.6f)%s' %
                #      (t, count, x, y, z, suffix))
                logger.info(msg)
                if not flat:
                    s.dump(False, _level + 1)

    def nearest(self, stype, positions, eps=1e-12):
        """
        Returns the index of the subshape nearest each position in
        positions.  If more than one shape tie for nearest, a 4th
        argument in positions selects which item to choose.

        This algorithm could probably be improved ***

        Parameters
        ----------
        stype
        positions
        eps : float, optional (default is 1e-12)
            A very small value

        """
        shape_centers = self.subcenters(stype)
        shape_indices = []
        for pt in positions:
            min_dsq = (pt[0] - shape_centers[0][0]) ** 2 + \
                (pt[1] - shape_centers[0][1]) ** 2 + \
                (pt[2] - shape_centers[0][2]) ** 2
            arg_min = 0
            arg_mins = []
            for count in range(1, len(shape_centers)):
                shape_center = shape_centers[count]
                dsq = (pt[0] - shape_center[0]) ** 2 + \
                    (pt[1] - shape_center[1]) ** 2 + \
                    (pt[2] - shape_center[2]) ** 2
                de = dsq - min_dsq
                if de < 0.0:
                    if -de < eps:
                        arg_mins.append(arg_min)
                    else:
                        arg_mins = []
                    min_dsq = dsq
                    arg_min = count
                elif de < eps:
                    arg_mins.append(count)
            if len(pt) == 4 and len(arg_mins) > 0:
                shape_indices.append(arg_mins[pt[3] - 2])
            else:
                shape_indices.append(arg_min)
        return shape_indices

    def subtolerance(self, stype='all', ttype='all'):
        """
        Iterates through every vertex, edge, and face,
        recording the tolerance.  Returns the minimum, average, and
        maximum tolerance.

        Parameters
        ----------
        stype : str, optional (default is 'all')
            limits the sweep to shapes of type stype.
        ttype : str, optional (default is 'all')
            limits the tolerance type to 'min', 'average', or 'max'.

        """

        tolerances = []

        # Vertices
        if stype == 'Vertex' or stype == 'all':
            raw_shapes = self._raw('Vertex')
            for raw_shape in raw_shapes:
                tolerances.append(
                    _BRep_Tool.Tolerance(_TopoDS_vertex(raw_shape)))

        # Edges
        if stype == 'Edge' or stype == 'all':
            raw_shapes = self._raw('Edge')
            for raw_shape in raw_shapes:
                tolerances.append(
                    _BRep_Tool.Tolerance(_TopoDS_edge(raw_shape)))

        # Faces
        if stype == 'Face' or stype == 'all':
            raw_shapes = self._raw('Face')
            for raw_shape in raw_shapes:
                tolerances.append(
                    _BRep_Tool.Tolerance(_TopoDS_face(raw_shape)))

        min_tol = min(tolerances)
        ave_tol = sum(tolerances) / len(tolerances)
        max_tol = max(tolerances)

        retval = (min_tol, ave_tol, max_tol)

        if ttype == 'all':
            return retval
        else:
            return retval[['min', 'average', 'max'].index(ttype)]


class Vertex(Shape):
    """
    A point in 3d space

    Parameters
    ----------
    s : tuple[float] or TopoDS_Vertex or TopoDS_Shape (of type vertex)

    """

    stype = 'Vertex'

    def __init__(self, s):
        if hasattr(s, '__getitem__') and isinstance(s[0], (int, float)):
            b = _BRepBuilderAPI.BRepBuilderAPI_MakeVertex(
                        _gp.gp_Pnt(s[0], s[1], s[2]))
            self.shape = b.Vertex()
        elif isinstance(s, _TopoDS.TopoDS_Vertex):
            self.shape = s
        elif isinstance(s, _TopoDS.TopoDS_Shape) and _raw_type(s) == 'Vertex':
            self.shape = _TopoDS_vertex(s)
        else:
            raise TypeError

    def center(self):
        r"""Center

        Returns
        -------
        tuple[float]

        """
        p = _BRep_Tool.Pnt(_TopoDS_vertex(self.shape))
        return p.X(), p.Y(), p.Z()

    def tolerance(self):
        r"""Tolerance

        Returns
        -------
        float

        """
        return _BRep_Tool.Tolerance(self.shape)


class Edge(Shape):
    """
    A continuous curve in 3d space bounded by two end points.
    """

    stype = 'Edge'

    def __init__(self, s):
        if isinstance(s, _TopoDS.TopoDS_Edge):
            self.shape = s
        elif isinstance(s, _TopoDS.TopoDS_Shape) and _raw_type(s) == 'Edge':
            self.shape = _TopoDS_edge(s)
        else:
            raise TypeError

    def __repr__(self):
        st = ''
        pt = self.poly()
        st = st + '(%.2f %.2f %.2f) -> (%.2f %.2f %.2f)' % (pt[0][0],pt[0][1],pt[0][2],pt[1][0],pt[1][1],pt[1][2]) +'\n'
        return(st)

    def center(self):
        r"""

        Returns
        -------
        tuple[float]

        """
        g1 = _GProp_GProps()
        _brepgprop_LinearProperties(self.shape, g1)
        p = g1.CentreOfMass()
        return p.X(), p.Y(), p.Z()

    def length(self):
        """Length of the edge

        Returns
        -------
        float : the length of the edge

        """
        g1 = _GProp_GProps()
        _brepgprop_LinearProperties(self.shape, g1)
        return g1.Mass()

    def tolerance(self):
        r"""Tolerance

        Returns
        -------
        float

        """
        return _BRep_Tool.Tolerance(_TopoDS_edge(self.shape))

    def type(self):
        """
        Returns the type of curve the edge is part of.  Use sparingly.
        The GeomAdaptor_Curve call often caused a Segmentation fault. ***

        Returns
        -------
        str

        """
        b1 = _BRep_Tool()
        c1 = b1.Curve(_TopoDS_edge(self.shape))
        gac1 = _GeomAdaptor_Curve(c1[0], c1[1], c1[2])
        t1 = gac1.GetType()
        return {_GeomAbs.GeomAbs_Line: 'line',
                _GeomAbs.GeomAbs_Circle: 'circle',
                _GeomAbs.GeomAbs_Ellipse: 'ellipse',
                _GeomAbs.GeomAbs_Hyperbola: 'hyperbola',
                _GeomAbs.GeomAbs_Parabola: 'parabola',
                _GeomAbs.GeomAbs_BezierCurve: 'bezier',
                _GeomAbs.GeomAbs_BSplineCurve: 'bspline',
                _GeomAbs.GeomAbs_OtherCurve: 'other'}[t1]

    def poly(self, deflection=1e-3):
        """ Returns a polyline approximation to the edge

        Parameters
        ----------
        deflection : float, optional (default is 1e-3)


        Returns
        -------
        list[tuple[float]]


        """
        c1 = _BRep_Tool.Curve(_TopoDS_edge(self.shape))
        gac1 = _GeomAdaptor_Curve(c1[0], c1[1], c1[2])
        ud = _GCPnts_QuasiUniformDeflection(gac1, deflection)
        retval = []
        for count in range(1, ud.NbPoints() + 1):
            pt = gac1.Value(ud.Parameter(count))
            retval.append((pt.X(), pt.Y(), pt.Z()))
        return retval


    def plot(self,**kwargs):
        """ pyplot figure of the Edge

        Paramters
        ---------

        b3d : boolean

        """
        b3d = kwargs.pop('b3d',False)
        if b3d:
            from mpl_toolkits.mplot3d import Axes3D
        if 'fig' in kwargs:
            fig = kwargs.pop('fig')
        else:
            fig = plt.gcf()
        if 'ax' in kwargs:
            ax = kwargs.pop('ax')
        else:
            ax = fig.add_subplot(111)
            if b3d:
                ax = fig.add_subplot(111,projection='3d')

        bgrid = kwargs.pop('bgrid',True)
        fontsize = kwargs.pop('fontsize',18)

        pts = np.array(self.poly())

        if b3d:
            ax.plot(pts[:,0],pts[:,1],pts[:,2],**kwargs)
        else:
            ax.plot(pts[:,0],pts[:,1],**kwargs)

        lbx = ax.get_xticklabels()
        lby = ax.get_yticklabels()
        for t in lbx:
            t.set_fontsize(fontsize)
        for t in lby:
            t.set_fontsize(fontsize)

        if bgrid:
            ax.grid('on')

        return fig,ax

class Wire(Shape):
    """ A connection of edges.  Can be instantiated with a list of edges
    to connect.

    Parameters
    ----------
    es : iterable[Edge] or TopoDS_Wire or TopoDS_Shape (of type wire)
    """

    stype = 'Wire'

    def __init__(self, es):
        if isinstance(es, (list, tuple)):
            b = _BRepBuilderAPI.BRepBuilderAPI_MakeWire()
            for e in es:
                if e.stype == 'Edge':
                    b.Add(_TopoDS_edge(e.shape))
                elif e.stype == 'Wire':
                    b.Add(_TopoDS_wire(e.shape))
                else:
                    # print('Error: Cannot add', e.stype, 'to wire.')
                    msg = 'Error: Cannot add %s to wire.' % str(e.stype)
                    logger.error(msg)
            self.shape = b.Wire()
        elif isinstance(es, _TopoDS.TopoDS_Wire):
            self.shape = es
        elif isinstance(es, _TopoDS.TopoDS_Shape) and _raw_type(es) == 'Wire':
            self.shape = _TopoDS_wire(es)
        else:
            raise TypeError

    def __repr__(self):
        st = ''
        #pts = np.array(self.poly())
        #N = pts.shape[0]
        #for k,pt in enumerate(pts):
        #    if k<(N-1):
        #        st = st + '(%.2f %.2f %.2f)' % (pt[0],pt[1],pt[2]) + ' , '
        #    else:
        #        st = st + '(%.2f %.2f %.2f)' % (pt[0],pt[1],pt[2]) 

        st = st  + 'Length : %2.f' % self.length() + '\n'
        edges = self.subshapes('Edge')
        for edge in edges:
            st = st + edge.__repr__()
        return st

    def center(self):
        r"""

        Returns
        -------
        tuple[float]
            Center coordinates

        """
        subs = self.subshapes('Edge')
        c = (0.0, 0.0, 0.0)
        total_length = 0.0
        for sub in subs:
            sub_center = sub.center()
            length = sub.length()
            c = (c[0] + length * sub_center[0],
                 c[1] + length * sub_center[1],
                 c[2] + length * sub_center[2])
            total_length = total_length + length
        c = (c[0] / total_length, c[1] / total_length, c[2] / total_length)
        return c

    def length(self):
        """Length of the wire

        Returns
        -------
        float : the length of the wire

        """
        subs = self.subshapes('Edge')
        total_length = 0.0
        for sub in subs:
            length = sub.length()
            total_length = total_length + length
        return total_length

    def poly(self, deflection=1e-3):
        """
        Returns a polyline approximation to the wire.

        Parameters
        ----------
        deflection : float, optional (default is 1e-3)

        Returns
        -------
        list[tuple[float]]

        """
        wo = self.shape.Orientation()
        edges = self.subshapes('Edge')
        retval = []
        for edge in edges:
            ep = edge.poly(deflection)
            if edge.shape.Orientation() != wo:
                ep = ep[::-1]
            retval = retval + ep[:-1]
        retval = retval + [ep[-1]]
        return retval

    def plot(self,**kwargs):
        """
        pyplot figure of the Edge
        """
        if 'b3d' in kwargs:
            b3d = kwargs.pop('b3d')
        else:
            b3d = False
        if b3d:
            from mpl_toolkits.mplot3d import Axes3D
        if 'fig' in kwargs:
            fig = kwargs.pop('fig')
        else:
            fig = plt.gcf()
        if 'ax' in kwargs:
            ax = kwargs.pop('ax')
        else:
            ax = fig.add_subplot(111)
            if b3d:
                ax = fig.add_subplot(111,projection='3d')

        bgrid = kwargs.pop('bgrid',True)
        fontsize = kwargs.pop('fontsize',18)
        pts = np.array(self.poly())
        if b3d:
            ax.plot(pts[:,0],pts[:,1],pts[:,2],**kwargs)
        else:
            ax.plot(pts[:,0],pts[:,1],**kwargs)

        ax.axis('equal')

        lbx = ax.get_xticklabels()
        lby = ax.get_yticklabels()
        for t in lbx:
            t.set_fontsize(fontsize)
        for t in lby:
            t.set_fontsize(fontsize)

        if bgrid:
            ax.grid('on')

        return fig,ax

class Face(Shape):
    """ A continuous surface in 3d space bounded by a closed wire.

    Parameters
    ----------

    s : TopoDS_Face or TopoDS_Shape (of type face)

    """

    stype = 'Face'

    def __init__(self, s):
        if isinstance(s, _TopoDS.TopoDS_Face):
            self.shape = s
        elif isinstance(s, _TopoDS.TopoDS_Shape) and _raw_type(s) == 'Face':
            self.shape = _TopoDS_face(s)
        else:
            raise TypeError

    def __repr__(self):

        st = ''
        wire = self.wire()
        st = st + 'Area : %.3f' % self.area() + '\n'
        st = st + wire.__repr__()
        st = st+'\n'

        return(st)

    def plot(self,**kwargs):
        self.wire().plot(**kwargs)

    def fillet(self, rad, vertex_indices=None):
        """
        Fillets the face at specified vertices with specified radii.

        If rad is a float, fillets all edges the same radius.  rad may
        also be a list of [(rad1, vertex_indices1), (rad2,
        vertex_indices2), ...] where rad1 is the radius to fillet all
        vertices in vertex_indices1, rad2 is the radius to fillet all
        vertices in vertex_indices2, etc.  In this latter case, the
        second argument (vertex_indices) is not used.

        If vertex_indices is None, fillets all vertices.
        vertex_indices may also be a list of [(x1, y1, z1), (x2, y2,
        z2), ...] where each (x1, y1, z1) specifies the edge with
        center nearest that point.

        Parameters
        ----------
        rad : float or list[tuple[float, tuple[int]]
        vertex_indices : list[tuple[float]], optional (default is None)

        """

        raw_vertices = self._raw('Vertex')
        if isinstance(rad, (int, float)):
            # Make real vertex_indices
            if vertex_indices is None:
                vertex_indices = range(len(raw_vertices))
            if len(vertex_indices) <= 0:
                return
            if not isinstance(vertex_indices[0], int):  # coordinate positions
                vertex_indices = self.nearest('Vertex', vertex_indices)
                # print 'vertex_indices', vertex_indices
            fillet_rads = [(rad, vertex_indices)]
        else:
            fillet_rads = rad

        b = _BRepFilletAPI.BRepFilletAPI_MakeFillet2d(_TopoDS_face(self.shape))
        changed = 0
        for fillet_rad in fillet_rads:
            rad, vertex_indices = fillet_rad
            if rad > 0.0:
                for vertex_index in vertex_indices:
                    changed = 1
                    b.AddFillet(_TopoDS_vertex(raw_vertices[vertex_index]),
                                rad)
        if changed:
            self.shape = b.Shape()

    def wire(self):
        """
        Returns the outside of the face as a wire

        Returns
        -------
        Wire

        """
        # return wire(self._raw('wire')[0])
        return Wire(_BRepTools.breptools_OuterWire(_TopoDS_face(self.shape)))

    def inner_wires(self):
        """
        Returns the inner contours of a face as a list of wires

        Returns
        -------
        list[Wire]

        """
        ow1 = _BRepTools.bpeptools_OuterWire(_TopoDS_face(self.shape))
        ow1o = ow1.Orientation()
        ex1w = _TopExp_Explorer(self.shape, _TopAbs.TopAbs_WIRE)
        retval = []
        while ex1w.More():
            cw = ex1w.Current()
            if cw != ow1:
                cw.Orientation(_TopAbs.TopAbs_Compose(ow1o, cw.Orientation()))
                retval.append(Wire(cw))
            ex1w.Next()
        return retval

    def normal(self):
        """ determine the face normal
        TODO : Implement is using OCC primitive
        """
        w = self.subshapes('Wire')
        e = self.subshapes('Edge')
        pt = e[0].poly()
        p0 = np.array([pt[0][0],pt[0][1],pt[0][2]])
        p1 = np.array([pt[1][0],pt[1][1],pt[1][2]])
        v0 = p1-p0
        pt = e[1].poly()
        p0 = np.array([pt[0][0],pt[0][1],pt[0][2]])
        p1 = np.array([pt[1][0],pt[1][1],pt[1][2]])
        v1 = p1-p0
        n = np.cross(v0,v1)
        n = n/np.linalg.norm(n)
        return n
        #surf = _BRep_Tool_Surface(_Topo(self.shape).face())
        #pl = Handle_Geom_Plane_DownCast(surf)
        #pln = pl.GetObject()
        #norm = pln.Axis().Direction()
        return(norm)

    def center(self):
        r"""

        Returns
        -------
        tuple[float]

        """
        g1 = _GProp_GProps()
        _brepgprop_SurfaceProperties(self.shape, g1)
        p = g1.CentreOfMass()
        return p.X(), p.Y(), p.Z()

    def area(self):
        """Area of the face

        Returns
        -------
        float : the area of the face

        """
        g1 = _GProp_GProps()
        _brepgprop_SurfaceProperties(self.shape, g1)
        return g1.Mass()

    def tolerance(self):
        r"""

        Returns
        -------
        float

        """
        return _BRep_Tool.Tolerance(_TopoDS_face(self.shape))

    def type(self):
        """
        Returns the type of surface the face is part of

        Returns
        -------
        str

        """
        t1 = _GeomAdaptor_Surface(
                _BRep_Tool.Surface(_TopoDS_face(self.shape))).GetType()
        return {_GeomAbs.GeomAbs_Plane: 'plane',
                _GeomAbs.GeomAbs_Cylinder: 'cylinder',
                _GeomAbs.GeomAbs_Cone: 'cone',
                _GeomAbs.GeomAbs_Sphere: 'sphere',
                _GeomAbs.GeomAbs_Torus: 'torus',
                _GeomAbs.GeomAbs_BezierSurface: 'bezier',
                _GeomAbs.GeomAbs_BSplineSurface: 'bspline',
                _GeomAbs.GeomAbs_SurfaceOfRevolution: 'revolution',
                _GeomAbs.GeomAbs_SurfaceOfExtrusion: 'extrusion',
                _GeomAbs.GeomAbs_OffsetSurface: 'offset',
                _GeomAbs.GeomAbs_OtherSurface: 'other'}[t1]


class Shell(Shape):
    """
    A connection of faces.  Can be instantiated with a list of faces
    to connect.

    Parameters
    ----------

    s : iterable[Face] or TopoDS_Shell or TopoDS_Shape (of type shell)

    """

    stype = 'Shell'

    def __init__(self, fs, tolerance=1e-6):
        if isinstance(fs, (list, tuple)):
            b = _BRepBuilderAPI.BRepBuilderAPI_Sewing(tolerance)
            for f in fs:
                #print(f.center())
                b.Add(f.shape)
            b.Perform()
            # fix
            self.shape = b.SewedShape()
            # print('sewing type:', self._raw_type())

            logger.info('sewing type: %s ' % str(self._raw_type()))
        elif isinstance(fs, _TopoDS.TopoDS_Shell):
            self.shape = fs
        elif isinstance(fs, _TopoDS.TopoDS_Shape) and _raw_type(fs) == 'Shell':
            self.shape = _TopoDS_shell(fs)
        else:
            raise TypeError

    def __repr__(self):
        st = 'Shell\n_____\n'
        subs = self.subshapes('Face')
        for k,sub in enumerate(subs):
            st = st + 'Face : %d' % k+'\n'
            st = st + sub.__repr__()

        return(st)

    def center(self):
        r""" determine Shell center

        Returns
        -------
        tuple[float]
            The center coordinates

        Notes
        -----

        Take all Faces from the Shell
        For each Face calculate its area and center

        """
        subs = self.subshapes('Face')
        c = (0.0, 0.0, 0.0)
        total_area = 0.0
        for sub in subs:
            sub_center = sub.center()
            area = sub.area()
            c = (c[0] + area * sub_center[0],
                 c[1] + area * sub_center[1],
                 c[2] + area * sub_center[2])
            total_area = total_area + area
        if total_area!=0:
            c = (c[0] / total_area, c[1] / total_area, c[2] / total_area)
        else:
            pdb.set_trace()
        return c

    def area(self):
        """
        Returns the area of the shell

        Returns
        -------
        float : the area of the shell

        """
        return sum([sub.area() for sub in self.subshapes('Face')])


class Solid(Shape):
    """
    A closed and filled shell.  Can be instantiated with a list of
    shells to connect.

    Currently OCC compound and compsolid are also handled by solid.
    That isn't right.  Ultimately, should make them their own classes
    and type check more carefully ***.

    Parameters
    ----------
    ss : iterable[Face] or TopoDS_Solid or TopoDS_Shape (of type solid, compound or compsolid)

    """

    stype = 'Solid'

    def __init__(self, ss):
        if isinstance(ss, (list, tuple)):
            b = _BRepBuilderAPI.BRepBuilderAPI_MakeSolid()
            for s in ss:
                b.Add(_TopoDS_shell(s.shape))
            self.shape = b.Solid()
        elif isinstance(ss, _TopoDS.TopoDS_Solid):
            self.shape = ss
        elif isinstance(ss, _TopoDS.TopoDS_Shape):
            if _raw_type(ss) == 'Solid':
                self.shape = _TopoDS_solid(ss)
            elif _raw_type(ss) == 'compound':
                self.shape = _TopoDS_compound(ss)
            elif _raw_type(ss) == 'compsolid':
                self.shape = _TopoDS_compsolid(ss)
            else:
                raise TypeError
        else:
            raise TypeError

    def __repr__(self):
        st = 'Volume : ' + '%.3f' % self.volume() + '\n'
        lfaces = self.subshapes('Face')
        for face in lfaces:
            st = st + face.__repr__()
        return(st)

    def __add__(self, other):
        return fuse(self, other)

    def __sub__(self, other):
        return cut(self, other)

    def __and__(self, other):
        return common(self, other)

    def to_stl(self, name, **options):
        """
        Exports the solid in .stl format.

        Parameters
        ----------
        name : str
        **options :

            ascii_mode:
                0: generate a binary stl file
                1 (Default): generate an ascii stl file

            relative_mode:
                0: deflection is calculated according to an absolute number
                1 (Default): deflection is calculated from the relative shape size

            abs_deflection (0.01 Default): for relative_mode 0, deflection is set
            to this

            rel_deflection (0.001 Default): for relative_mode 1, deflection is
            multiplied by this

        I found blender and gts had trouble with the output.  There
        were many repeated vertices in ascii or binary mode.  Most
        could be fixed by importing to blender, removing doubles, and
        exporting to stl. ***
        """

        w = _StlAPI_Writer()
        if 'ascii_mode' in options:
            w.SetASCIIMode(options['ascii_mode'])
        if 'relative_mode' in options:
            w.SetRelativeMode(options['relative_mode'])
        if 'abs_deflection' in options:
            w.SetDeflection(options['abs_deflection'])
        if 'rel_deflection' in options:
            w.SetCoefficient(options['rel_deflection'])
        w.Write(self.shape, name)

    def center(self):
        r"""

        Returns
        -------
        tuple[float]
            The center coordinates

        """
        g1 = _GProp_GProps()
        _brepgprop_VolumeProperties(self.shape, g1)
        p = g1.CentreOfMass()
        return p.X(), p.Y(), p.Z()

    def fillet(self, rad, edge_indices=None):
        """
        Fillets the solid at specified edges with specified radii.

        I found OCC's BRepFilletAPI_MakeFillet buggy.  Errors could be
        improved by the following workarounds:

        1. Eliminate impossible conditions (e.g. a 1x1x1 box with fillet
        radius > 0.5) (obviously not an OCC bug)

        2. Eliminate unneeded edges.  OCC's boolean operations often
        return two faces in the same domain with an edge between them
        that can be merged.  Eliminating these edges (by merging the
        faces) helped.  The simplify() method can do this for some
        shapes.  It's incomplete, though.  Also, seam edges (e.g. the
        edge along a cylinder's body) can be moved out of the way
        sometimes.

        3. Change the radius slightly.

        4. Fillet a few edges, then a few more, then a few more, etc.
        edge_center passing can be very useful for this workaround.
        All connected fillets should be in the same edge group.

        5. Extrusion along a spline causes straight edges to create
        bspline faces.  Planarazing these faces helped.

        Parameters
        ----------
        rad : float or list[tuple[float, int]]
            If rad is a float, fillets all edges the same radius.  rad may
            also be a list of [(rad1, edge_indices1), (rad2,
            edge_indices2), ...] where rad1 is the radius to fillet all
            edges in edge_indices1, rad2 is the radius to fillet all edges
            in edge_indices2, etc.  In this latter case, the second
            argument (edge_indices) is not used.  rad1, rad2, etc. may be
            two-tuples instead of floats.  In this case, the fillet rad is
            an evolutive radius that changes from one radius to another
            over the edge.
        edge_indices : list[tuple[float, float, float]], optional (default is None)
            If edge_indices is None, fillets all edges.  edge_indices may
            also be a list of [(x1, y1, z1), (x2, y2, z2), ...] where each
            (x1, y1, z1) specifies the edge with center nearest that
            point.

        """

        raw_edges = self._raw('Edge')
        if isinstance(rad, (int, float)):
            # Make real edge_indices
            if edge_indices is None:
                edge_indices = range(len(raw_edges))
            if len(edge_indices) <= 0:
                return
            if not isinstance(edge_indices[0], int):  # coordinate positions
                edge_indices = self.nearest('Edge', edge_indices)
                # print 'edge_indices', edge_indices
            fillet_rads = [(rad, edge_indices)]
        else:
            fillet_rads = rad

        b = _BRepFilletAPI.BRepFilletAPI_MakeFillet(self.shape)
        changed = 0
        for fillet_rad in fillet_rads:
            rad, edge_indices = fillet_rad
            if isinstance(rad, (int, float)):
                if rad > 0.0:
                    for edge_index in edge_indices:
                        changed = 1
                        b.Add(rad, _TopoDS_edge(raw_edges[edge_index]))
            else:  # evolutive radius
                for edge_index in edge_indices:
                    changed = 1
                    b.Add(rad[0], rad[1], _TopoDS_edge(raw_edges[edge_index]))
        if changed:
            self.shape = b.Shape()

    def chamfer(self, dist, edge_indices=None):
        """
        chamfers all edges in edge_indices the same distance at 45 degrees

        The arguments are more primitive than boolean--should change
        to be like boolean. ***

        Parameters
        ----------
        dist : float
        edge_indices : list[int], optional (default is None)

        """
        if dist > 0.0:
            edge_map = _TopTools.TopTools_IndexedDataMapOfShapeListOfShape()
            _TopExp_MapShapesAndAncestors(self.shape, _TopAbs.TopAbs_EDGE,
                                          _TopAbs.TopAbs_FACE, edge_map)
            b = _BRepFilletAPI.BRepFilletAPI_MakeChamfer(self.shape)
            raw_edges = self._raw('Edge')
            if edge_indices is None:
                edge_indices = range(len(raw_edges))
            if len(edge_indices) <= 0:
                return
            if not isinstance(edge_indices[0], int):  # coordinate positions
                edge_indices = self.nearest('Edge', edge_indices)

            for edge_index in edge_indices:
                e1 = raw_edges[edge_index]
                f1 = edge_map.FindFromKey(e1).First()
                b.Add(dist, dist, _TopoDS_edge(e1), _TopoDS_face(f1))
            self.shape = b.Shape()

    def draft(self, angle, pdir, pt, face_indices):
        """
        Drafts faces in face_indices by angle from direction pdir and
        reference plane that passes through pt.

        I found OCC's BRepOffsetAPI_DraftAngle buggy ***.  In most
        cases, it was better to hand-create two wire profiles, and use
        a loft with ruled edges.

        Parameters
        ----------
        angle : float
        pdir : tuple[float, float, float]
        pt : tuple[float, float, float]
        face_indices : list[int]
        """
        if angle != 0.0:
            d = _gp.gp_Dir(pdir[0], pdir[1], pdir[2])
            pln = _gp.gp_Pln(_gp.gp_Pnt(pt[0], pt[1], pt[2]), d)
            raw_faces = self._raw('Face')
            if not isinstance(face_indices[0], int):  # coordinate positions
                face_indices = self.nearest('Face', face_indices)
            b = _BRepOffsetAPI.BRepOffsetAPI_DraftAngle(self.shape)
            for face_index in face_indices:
                b.Add(_TopoDS_face(raw_faces[face_index]), d, angle, pln)
            b.Build()
            self.shape = b.Shape()

    def volume(self):
        """
        Returns the volume of the solid

        Returns
        -------
        float : the volume of the solid

        """
        g1 = _GProp_GProps()
        _brepgprop_VolumeProperties(self.shape, g1)
        return g1.Mass()  # Returns volume when density hasn't been set

    def simplify(self, skip_edges=0, skip_faces=0, skip_fits=0,
                 stopat=-1, tolerance=1e-3):
        """
        Fuses edges that are C1 continuous and share a vertex.  Fuses
        faces in the same domain that share an edge.  It's currently
        slow, because FacesIntersector is slow.  (It's not the python
        code.)  May want to remove internal edges and internal vertices
        later. ***

        Parameters
        ----------
        skip_edges : int, optional (default is 0)
        skip_faces : int, optional (default is 0)
        skip_fits : int, optional (default is 0)
        stopat : int, optional (default is -1)
        tolerance : float, optional (default is 1e-3)

        """

        """
        # Seemed simple, but didn't work.  Glancing through the
        # C-code, I don't think BOP_Refiner is a fusing algorithm.
        b = BOP_Refiner()
        b.SetShape(self.shape)
        b.Do()
        print 'Removed', b.NbRemovedVertices(), 'vertices'
        print 'Removed', b.NbRemovedEdges(), 'edges'
        self.shape = b.Shape()
        """

        """
        # Seemed simple, but didn't work
        b1 = BlockFix_BlockFixAPI()
        b1.SetShape(self.shape)
        b1.SetTolerance(tolerance)
        b1.Perform()
        self.shape = b1.Shape()
        """

        # Fuse Edges first
        if not skip_edges:
            b = _TopOpeBRepTool_FuseEdges(self.shape)
            self.shape = b.Shape()

        # Fuse Faces second (not easy)
        if not skip_faces:
            edge_map = _TopTools.TopTools_IndexedDataMapOfShapeListOfShape()
            _TopExp_MapShapesAndAncestors(self.shape, _TopAbs.TopAbs_EDGE,
                                          _TopAbs.TopAbs_FACE, edge_map)
            raw_edges = self._raw('Edge')
            common_faces = {}
            new_faces = []
            pairs = []
            merge_count = 0
            for rec, raw_edge in enumerate(raw_edges):
                # if stopat >= 0 and rec == stopat:
                if rec == stopat >= 0:
                    break
                # print('raw edge', rec, end='')
                logger.info(str(('raw edge', rec)))
                l1 = edge_map.FindFromKey(raw_edge)
                f1 = l1.First()  # Assumes only two faces per edge
                f2 = l1.Last()
                h1 = f1.__hash__()
                h2 = f2.__hash__()
                if h1 == h2:  # Avoid seam edges
                    # print('Seam')
                    logger.info("\tSeam")
                    continue
                elif h1 > h2:
                    pair = (h2, h1)
                else:
                    pair = (h1, h2)
                if pair in pairs:
                    # print('Skipped')
                    logger.info("\tSkipped")
                    continue
                else:
                    pairs.append(pair)
                if _raw_faces_same_domain(f1, f2, skip_fits):
                    # print('Merge')
                    logger.info("\tMerge")
                    merge_count += 1
                    if f1 not in common_faces:
                        if f2 not in common_faces:
                            new_faces.append(_raw_faces_merge(f1, f2))
                            index = len(new_faces) - 1
                            common_faces[f1] = index
                            common_faces[f2] = index
                        else:
                            index = common_faces[f2]
                            # Changed to sewed faces to handle recursive edge
                            # changes from ShapeFix
                            # to_merge = (new_faces[index], f1)
                            b = _BRepBuilderAPI.BRepBuilderAPI_Sewing()
                            b.Add(new_faces[index])
                            b.Add(f1)
                            b.Perform()
                            s = Shell(b.SewedShape())
                            nf1, nf2 = s._raw('Face')
                            new_faces[index] = _raw_faces_merge(nf1, nf2)
                            common_faces[f1] = index
                    elif f2 not in common_faces:
                        index = common_faces[f1]
                        # Changed to sewed faces to handle recursive edge
                        # changes from ShapeFix
                        # to_merge = (new_faces[index], f2)
                        b = _BRepBuilderAPI.BRepBuilderAPI_Sewing()
                        b.Add(new_faces[index])
                        b.Add(f2)
                        b.Perform()
                        s = Shell(b.SewedShape())
                        nf1, nf2 = s._raw('Face')
                        new_faces[index] = _raw_faces_merge(nf1, nf2)
                        common_faces[f2] = index
                    else:  # Both in common_faces
                        if common_faces[f1] == common_faces[f2]:
                            # print('Done already')
                            logger.info("\tDone already")
                        else:
                            index = common_faces[f1]
                            index2 = common_faces[f2]
                            b = _BRepBuilderAPI.BRepBuilderAPI_Sewing()
                            b.Add(new_faces[index])
                            b.Add(new_faces[index2])
                            b.Perform()
                            s = Shell(b.SewedShape())
                            nf1, nf2 = s._raw('Face')
                            new_faces[index] = _raw_faces_merge(nf1, nf2)
                            for k, v in common_faces.items():
                                if v == index2:
                                    common_faces[k] = index
                            new_faces[index2] = None

                else:
                    # print('Different')
                    logger.info("\tDifferent")

            if len(new_faces) <= 0:  # No common faces
                return
            else:
                # print("")
                # BRep_Builder may be faster than BRepBuilderAPI_Sewing
                raw_faces = self._raw('Face')
                for f in common_faces.keys():
                    raw_faces.remove(f)
                b = _BRepBuilderAPI.BRepBuilderAPI_Sewing(tolerance)
                for f in raw_faces:
                    b.Add(f)
                for f in new_faces:
                    if f:
                        b.Add(f)
                b.Perform()
                new_shell = b.SewedShape()
                if _raw_type(new_shell) == 'Shell':
                    b2 = _BRepBuilderAPI.BRepBuilderAPI_MakeSolid()
                    b2.Add(_TopoDS_shell(new_shell))
                    self.shape = b2.Solid()
                elif _raw_type(new_shell) == 'compound':
                    # print('Warning: simplify() returned compound')
                    logger.warning('Warning: simplify() returned compound')
                    s = Solid(new_shell)
                    css = s._raw('Shell')
                    c = _TopoDS.TopoDS_Compound()
                    b3 = _BRep_Builder()
                    b3.MakeCompound(c)
                    for cs in css:
                        b2 = _BRepBuilderAPI.BRepBuilderAPI_MakeSolid()
                        b2.Add(_TopoDS_shell(cs))
                        b3.Add(c, b2.Solid())
                    self.shape = c
                else:
                    # print('Warning: Wrong Sewed Shape after simplify():', \
                    #     _raw_type(new_shell))
                    msg = 'Warning: Wrong Sewed Shape after simplify(): %s' % \
                          str(_raw_type(new_shell))
                    logger.warning(msg)
                    self.shape = new_shell


"""
Primitives
----------

Philosophy
----------
OCC offers a variety of primitive input arguments.  Users typically
use 1-2 of them, and the others cause confusion for those who don't
use them.  Instead, only offer the variety that provides unique
topologies.  Those varieties with differing positions and orientations
are not used.  They can be arrived at with transformations.
"""


# Edge Primitives

def segment(pt1, pt2):
    """
    Returns an edge that is a segment from point1 to point2.
    Expects point1, point2

    Parameters
    ----------
    pt1 : tuple[float, float, float]
    pt2 : tuple[float, float, float]

    Returns
    -------
    Edge

    """
    return Edge(_BRepBuilderAPI.BRepBuilderAPI_MakeEdge(
            _gp.gp_Pnt(pt1[0], pt1[1], pt1[2]),
            _gp.gp_Pnt(pt2[0], pt2[1], pt2[2])).Edge())


def arc(rad, start_angle, end_angle):
    """
    Returns an edge that is an arc centered about (0.0, 0.0, 0.0) with
    given radius, start_angle, and end_angle.
    Expects radius, start_angle, end_angle

    Parameters
    ----------
    rad : float
    start_angle : float
    end_angle : float

    Returns
    -------
    Edge

    """
    return Edge(_BRepBuilderAPI.BRepBuilderAPI_MakeEdge(
            _GC_MakeArcOfCircle(
                _gp.gp_Circ(_gp.gp_Ax2(_gp.gp_Pnt(0.0, 0.0, 0.0),
                                       _gp.gp_Dir(0.0, 0.0, 1.0)),
                            rad),
                start_angle, end_angle, False).Value()).Edge())


def arc_ellipse(rad1, rad2, start_angle, end_angle):
    """
    Returns an edge that is an elliptical arc centered about (0.0,
    0.0, 0.0) with given major radius rad1, minor radius rad2,
    start_angle, and end_angle.  Expects rad1, rad2, start_angle,
    end_angle.

    Parameters
    ----------
    rad1 : float
    rad2 : float
    start_angle : float
    end_angle : float

    Returns
    -------
    Edge

    """
    if rad2 > rad1:
        # print('Error: Major radius ', rad1,
        #       ' must be greater than minor radius ', rad2)
        msg = 'Error: Major radius %s must be greater than minor radius %s' % \
              (str(rad1), str(rad2))
        logger.error(msg)
        sys.exit()
    return Edge(_BRepBuilderAPI.BRepBuilderAPI_MakeEdge(
            _GC_MakeArcOfEllipse(
                _gp.gp_Elips(_gp.gp_Ax2(_gp.gp_Pnt(0.0, 0.0, 0.0),
                                        _gp.gp_Dir(0.0, 0.0, 1.0)),
                             rad1, rad2),
                start_angle, end_angle, False).Value()).Edge())


def spline(pts, **options):
    """
    Returns an edge that is a 3D spline curve fitted through the
    passed points.
    Expects a list of points.

    Note: the name really ought to be fit_spline, or something like
    that to later allow someone to actually enter knots and such.
    Change if need be.

    Parameters
    ----------
    pts : list
    **options:
        min_degree
        max_degree
        continuity
        tolerance

    Returns
    -------
    Edge

    """
    if 'min_degree' not in options:
        options['min_degree'] = 3
    if 'max_degree' not in options:
        options['max_degree'] = 8
    if 'continuity' not in options:
        options['continuity'] = _GeomAbs.GeomAbs_C2
    if 'tolerance' not in options:
        options['tolerance'] = 1e-3

    num_pts = len(pts)
    tpts = _TColgp_Array1OfPnt(0, num_pts - 1)
    for count in range(num_pts):
        tpts.SetValue(count,
                      _gp.gp_Pnt(pts[count][0], pts[count][1], pts[count][2]))
    return Edge(_BRepBuilderAPI.BRepBuilderAPI_MakeEdge(
            _GeomAPI_PointsToBSpline(tpts,
                                     options['min_degree'],
                                     options['max_degree'],
                                     options['continuity'],
                                     options['tolerance']).Curve()).Edge())


def bezier(pts, weights=[]):
    """
    Returns an edge that is a Bezier curve fitted through pts.  Only
    the first and last points does it pass through.  The others are
    control points.  weights is a list pts long.  If unspecified, all
    points have the same weight.

    Parameters
    ----------
    pts : list
    weights : list[float], optionla (default is an empty list)

    """
    num_pts = len(pts)
    tpts = _TColgp_Array1OfPnt(0, num_pts - 1)
    for count in range(num_pts):
        tpts.SetValue(count, _gp.gp_Pnt(pts[count][0],
                      pts[count][1], pts[count][2]))
    if len(weights) == num_pts:
        tweights = _TColStd_Array1OfReal(1, num_pts)
        for count in range(num_pts):
            tweights.SetValue(count + 1, weights[count])
        retval = Edge(_BRepBuilderAPI.BRepBuilderAPI_MakeEdge(
                _Geom_BezierCurve(tpts, tweights).GetHandle()).Edge())
    else:
        retval = Edge(_BRepBuilderAPI.BRepBuilderAPI_MakeEdge(
                _Geom_BezierCurve(tpts).GetHandle()).Edge())

    return retval


def circle(rad):
    """
    Returns an edge that is a circle centered at (0.0, 0.0, 0.0) with
    given radius.  Expects a radius

    Parameters
    ----------
    rad : float
        The circle radius

    Returns
    -------
    Edge

    """
    return Edge(_BRepBuilderAPI.BRepBuilderAPI_MakeEdge(
            _gp.gp_Circ(_gp.gp_Ax2(_gp.gp_Pnt(0.0, 0.0, 0.0),
                                   _gp.gp_Dir(0.0, 0.0, 1.0)), rad)).Edge())


def ellipse(rad1, rad2):
    """
    Returns an edge that is an ellipse centered at (0.0, 0.0, 0.0)
    with major radius rad1 and minor radius rad2.

    Parameters
    ----------
    rad1 : float
        The first radius
    rad2 : float
        The second radius

    Returns
    -------
    Edge

    """
    if rad2 > rad1:
        # print('Error: Major radius ', rad1,
        #       ' must be greater than minor radius ', rad2)
        msg = 'Error: Major radius %s must be greater than minor radius %s' % \
              (str(rad1), str(rad2))
        logger.error(msg)
        sys.exit()
    return Edge(_BRepBuilderAPI.BRepBuilderAPI_MakeEdge(
            _gp.gp_Elips(_gp.gp_Ax2(_gp.gp_Pnt(0.0, 0.0, 0.0),
                                    _gp.gp_Dir(0.0, 0.0, 1.0)),
                         rad1, rad2)).Edge())


# Wire Primitives

def polygon(pts):
    """
    Returns a wire which is a polygon.
    Expects a list of points

    Parameters
    ----------
    pts : list

    Returns
    -------
    Wire

    """

    b = _BRepBuilderAPI.BRepBuilderAPI_MakePolygon()
    for count in range(len(pts)):
        b.Add(_gp.gp_Pnt(pts[count][0], pts[count][1], pts[count][2]))
    return Wire(b.Wire())


def rectangle(dx, dy):
    """
    Returns a wire in the shape of a rectangle.  The lower left
    coordinate is (0,0).

    Parameters
    ----------
    dx : float
        The x dimension
    dy : float
        The y dimension

    Returns
    -------
    Wire


    """
    return polygon([(0.0, 0.0, 0.0),
                    (dx, 0.0, 0.0),
                    (dx, dy, 0.0),
                    (0.0, dy, 0.0),
                    (0.0, 0.0, 0.0)])


def ngon(rad, n):
    """
    Returns a wire which is an ngon (e.g. 6gon is a hexagon) in the x-y
    plane.  Expects a radius and a number of sides

    Parameters
    ----------
    rad : float
        The ngon radius
    n : int
        The number of sides

    Returns
    -------
    Wire

    """

    angle = 0.0
    pts = []
    for count in range(n + 1):
        angle += (2 * _math.pi / n)
        pts.append((rad * _math.cos(angle), rad * _math.sin(angle), 0.0))
    return polygon(pts)


def helix(rad, angle, turns, eps=1e-12):
    """
    Returns a wire that is a helix centered at (0.0, 0.0, 0.0) with
    given radius, helix angle, and number of turns.

    turns currently must be an integer multiple of 0.25.

    This used to return an edge.  I found a way for an exact edge, but
    the underlying curve was a spline, and it degenerated over many
    turns.  I replaced it with a wire that is a spline over quarter
    turns and replicated.

    Parameters
    ----------
    rad : float
        The radius
    angle : float
    turns : <tbc/unclear>
    eps : float, optional (default is 1e-12)

    Returns
    -------
    Wire

    """

    # This routine breaks the helix into quarter circles of beziers.
    # It is exact, since a properly weighted bezier generates a
    # circle.

    # fits and returns a wire.
    full_angle = _math.pi / 2
    frac_parts = 4 * turns  # Change if full_angle changes
    num_parts = int(frac_parts)
    rem_parts = frac_parts - num_parts
    if abs(rem_parts) > eps:
        # print('Error: Fractional turns not currently supported.')
        logger.error('Error: Fractional turns not currently supported.')
        sys.exit()

    # Calculate a quarter helix using a weighted bezier
    z0 = rad * full_angle * _math.tan(angle)
    e1 = bezier([(rad, 0.0, 0.0), (rad, rad, z0 / 2), (0.0, rad, z0)],
                [1.0, 1.0 / _math.sqrt(2.0), 1.0])

    # Replicate the edge, spinning and translating, to make a helix
    retval = []
    for count in range(num_parts):
        locale = e1.copy()
        locale.rotatez(count * full_angle)
        locale.translate((0.0, 0.0, count * z0))
        retval.append(locale)
    return Wire(retval)


# Face Primitives

def plane(w1, inner_wires=[]):
    """
    Returns a face which is a plane.

    w1 is a wire that bounds the outside of the face
    inner_wires are a list of wires that are holes in the face

    Expects all wires are planarized.

    Parameters
    ----------
    w1 : <tbc>
    inner_wires : list, optional (default is an empty list)

    Returns
    -------
    Face

    """
    # w1 must be planar!
    ow1 = _TopoDS_wire(w1.shape)
    # ow1.Orientation(TopAbs_EXTERNAL) # This made them disappear
    b = _BRepBuilderAPI.BRepBuilderAPI_MakeFace(ow1)
    for inner_wire in inner_wires:
        iw = _TopoDS_wire(inner_wire.shape)
        # iw.Orientation(TopAbs_EXTERNAL) # This didn't help
        b.Add(iw)
    if not b.IsDone():
        raise NameError('FaceError')
    else:
        retval = Face(b.Face())
        # This is a poor way to fix an orientation problem ***
        if len(inner_wires) > 0:
            retval.fix()
        return retval


def face_from(f1, w1):
    """
    Returns a face whose underlying geometry is the same underlying
    geometry of f1 but is bounded by the closed wire w1.

    Trim is a misnomer.  w1 can be beyond the original face.

    Parameters
    ----------
    f1 : Face
    w1 : Wire

    Returns
    -------
    Face

    """
    s = _BRep_Tool.Surface(_TopoDS_face(f1.shape))
    b = _BRepBuilderAPI.BRepBuilderAPI_MakeFace(s, _TopoDS_wire(w1.shape))
    return Face(b.Face())


def filling(w1, **options):
    """
    Returns a face which is a 3D surface fit to the wire w1.  Warning:
    OCC may modify the wire slightly to fit the surface.  Expects a
    closed curved wire

    Parameters
    ----------
    w1
    **options
        degree
        max_degree
        continuity

    Returns
    -------
    Face

    """
    call_options = {}
    if 'degree' in options:
        call_options['Degree'] = options['degree']
    if 'max_degree' in options:
        call_options['MaxDeg'] = options['max_degree']
    if 'continuity' in options:
        occ_cont = [_GeomAbs.GeomAbs_C0, _GeomAbs.GeomAbs_C1,
                    _GeomAbs.GeomAbs_C2][continuity]
    else:
        occ_cont = _GeomAbs.GeomAbs_C0
    if 'num_pts' in options:
        call_options['NbPtsOnCur'] = options['num_pts']
    if 'num_iters'in options:
        call_options['NbIter'] = options['num_iters']
    if 'anisotropy' in options:
        call_options['Anisotropie'] = options['anisotropy']
    if 'tolerance2d'in options:
        call_options['Tol2d'] = options['tolerance2d']
    if 'tolerance3d' in options:
        call_options['Tol3d'] = options['tolerance3d']
    if 'tolerance_angle' in options:
        call_options['TolAng'] = options['tolerance_angle']
    if 'tolerance_curve' in options:
        call_options['TolCurv'] = options['tolerance_curve']
    if 'max_segments' in options:
        call_options['MaxSegments'] = options['max_segments']

    raw_edges = w1._raw('Edge')
    b = _BRepOffsetAPI.BRepOffsetAPI_MakeFilling(**call_options)
    for raw_edge in raw_edges:
        b.Add(_TopoDS_edge(raw_edge), occ_cont)
    b.Build()
    return Face(b.Shape())


def slice_(s1, x=None, y=None, z=None):
    """
    Returns a slice of solid s1.  A slice is a list of faces derived
    from a plane cutting through s1.

    x can be the plane.  It's up to you to make sure the plane extends
    beyond s1's bounds.  If not, only specify one of x, y, or z as a
    float.  For example, x = 5.0 specifies the plane with any value of
    y or z that always has x = 5.0.

    Parameters
    ----------
    s1 : Solid
    x : float or Face, optional (default is None)
    y : float, optional (default is None)
    z : float, optional (default is None)

    Returns
    -------
    list[Face]

    """
    if isinstance(x, Face):
        p1 = x
    else:
        xmin, ymin, zmin, xmax, ymax, zmax = s1.bounds()
        if x:
            w1 = polygon([(x, ymin, zmin),
                          (x, ymax, zmin),
                          (x, ymax, zmax),
                          (x, ymin, zmax),
                          (x, ymin, zmin)])
        elif y:
            w1 = polygon([(xmin, y, zmin),
                          (xmax, y, zmin),
                          (xmax, y, zmax),
                          (xmin, y, zmax),
                          (xmin, y, zmin)])
        else:
            w1 = polygon([(xmin, ymin, z),
                          (xmax, ymin, z),
                          (xmax, ymax, z),
                          (xmin, ymax, z),
                          (xmin, ymin, z)])
        p1 = plane(w1)

    b1 = _BRepAlgoAPI.BRepAlgoAPI_Common(s1.shape, p1.shape)
    s2 = Solid(b1.Shape())
    return s2.subshapes('Face')


# Solid Primitives

def box(dx, dy, dz):
    """
    Returns a solid box.

    The box fills the x-direction from 0 to dx,
    the y-direction from 0 to dy,
    and the z-direction from 0 to dz.

    Parameters
    ----------
    dx : float
    dy : float
    dz : float

    Returns
    -------
    Solid

    """
    return Solid(_BRepPrimAPI.BRepPrimAPI_MakeBox(dx, dy, dz).Shape())


def wedge(dx, dy, dz, lx, xmax=None, zmin=None, zmax=None):
    """
    Returns a solid wedge.
    Expects dx, dy, dz, lx -or- dx, dy, dz, xmin, xmax, zmin, zmax

    dx, dy, and dz follow the box conventions.

    If only lx is given, dx defines the xlength at y=0 and lx defines
    the xlength at y=dy.

    If xmin, xmax, zmin, and zmax are given, xmin and xmax define the
    x wedge limits at y=dy, and zmin and zmax define the z wedge
    limits at y=dy.

    The limits at y=0 follow the box convention.

    Parameters
    ----------
    dx : float
    dy : float
    dz : float
    lx : float
    xmax : float, optional (default is None)
    zmin : float, optional (default is None)
    zmax : float, optional (default is None)

    Returns
    -------
    Solid

    """

    if xmax is None and zmin is None and zmax is None:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeWedge(
                dx, dy, dz, lx).Shape())
    else:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeWedge(
                dx, dy, dz, lx, xmax, zmin, zmax).Shape())


def cylinder(rad, height, angle=None):
    """
    Returns a solid cylinder.

    If angle is given, it limits the cylinder in the x-y plane.

    Parameters
    ----------
    rad : float
        The cylinder radius
    height : float
        The cylinder height
    angle : float, optional, default is None

    Returns
    -------
    Solid

    """

    if angle is None:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeCylinder(
                rad, height).Shape())
    else:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeCylinder(
                rad, height, angle).Shape())


def sphere(rad, angle1=None, angle2=None, angle3=None):
    """
    Returns a solid sphere.

    rad is the sphere radius.
    If only angle1 is given, angle1 limits the sphere in the x-y plane.
    If only angle1 and angle2 are given, they limit the sphere to a
    lower latitude (angle1) and an upper latitude (angle2).
    If all three angles are given, angle1 limits the x-y plane, and
    angle2 and angle3 limit the latitudes.

    Parameters
    ----------
    rad : float
        The sphere radius
    angle1 : float, optional (default is None)
    angle2 : float, optional (default is None)
    angle3 : float, optional (default is None)

    Returns
    -------
    Solid

    """

    if angle1 is None and angle2 is None and angle3 is None:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeSphere(rad).Shape())
    elif angle2 is None and angle3 is None:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeSphere(
                rad, angle1).Shape())
    elif angle3 is None:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeSphere(
                rad, angle1, angle2).Shape())
    else:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeSphere(
                rad, angle1, angle2, angle3).Shape())


def cone(rad1, rad2, height, angle=None):
    """
    Returns a solid cone.

    Parameters
    ----------
    rad1 : float
        radius at z=0.
    rad2 : float
        radius at z=height.
    height : float
        the cone height.

    Returns
    -------
    Solid

    """
    if angle is None:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeCone(
                rad1, rad2, height).Shape())
    else:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeCone(
                rad1, rad2, height, angle).Shape())


def bezier_cone(rad1, rad2, height, angle=None):
    """
    Returns a solid cone where the faces are plane or splines.

    I found cone pretty buggy when fillets were needed.  This should
    yield an identical solid, but it sometimes was nicer to fillets.

    I think this would be even more robust if I knew the proper
    coefficients to make a bezier a cone instead of revolving it.
    Surfaces of revolution have their own problems.

    Parameters
    ----------
    rad1 : float
    rad2 : float
    height : float
    angle : float, optional (default is None)

    Returns
    -------
    <tbc>

    """
    if angle is None:
        angle = 2.0 * _math.pi
    e1 = bezier([(rad1, 0.0, 0.0), (rad2, 0.0, height)])
    w1 = polygon([(rad2, 0.0, height),
                  (0.0, 0.0, height),
                  (0.0, 0.0, 0.0),
                  (rad1, 0.0, 0.0)])
    w1 = Wire([e1, w1])
    return revol(plane(w1), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle)


def torus(rad1, rad2, angle1=None, angle2=None, angle3=None):
    """
    Returns a solid torus.

    If only angle1 is given, angle1 limits the extrusion to angle1
    radians, instead of 2*pi radians.
    If only angle1 and angle2 are given, they limit the torus to a
    lower latitude (angle1) and an upper latitude (angle2).
    If all three angles are given, angle1 limits the extrusion, and
    angle2 and angle3 limit the latitudes.

    Parameters
    ----------
    rad1 : float
        distance from torus center to extruded circle center
    rad2 : float
        extruded circle radius
    angle1 : float, optional (default is None)
    angle2 : float, optional (default is None)
    angle3 : float, optional (default is None)

    Returns
    -------
    Solid

    """
    if angle1 is None and angle2 is None and angle3 is None:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeTorus(rad1, rad2).Shape())
    elif angle2 is None and angle3 is None:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeTorus(
                rad1, rad2, angle1).Shape())
    elif angle3 is None:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeTorus(
                rad1, rad2, angle1, angle2).Shape())
    else:
        return Solid(_BRepPrimAPI.BRepPrimAPI_MakeTorus(
                rad1, rad2, angle1, angle2, angle3).Shape())


def prism(s, pdir):
    """
    Returns a solid which is an extrusion of a face along a direction,
    or a shell which is an extrusion of a wire,
    or a face which is an extrusion of an edge,
    or an edge which is an extrusion of a vertex.

    Expects a shape to be extruded and a prism direction (dx, dy, dz).
    Currently ignores shell to composite solid possibilities.

    Parameters
    ----------
    s : Vertex, Edge, Wire or Face
        The shape to extrude
    pdir : tuple[float, float, float]
        The extrusion direction

    Returns
    -------
    Edge, Face, Shell or Solid, depending on the input shape type

    """
    b = _BRepPrimAPI.BRepPrimAPI_MakePrism(
        s.shape, _gp.gp_Vec(pdir[0], pdir[1], pdir[2]), True)
    b.Build()
    if s.stype == 'Vertex':
        return Edge(b.Shape())
    elif s.stype == 'Edge':
        return Face(b.Shape())
    elif s.stype == 'Wire':
        return Shell(b.Shape())
    elif s.stype == 'Face':
        return Solid(b.Shape())
    else:
        # print('Error: Improper type for prism', s.stype)
        logger.error('Error: Improper type for prism: s' % str(s.stype))


def revol(s, pabout, pdir, angle):
    """
    Returns a solid which is a revolution of a face,
    or a shell which is a revolution of a wire,
    or a face which is a revolution of an edge,
    or an edge which is a revolution of a vertex.

    Expects a shape to be revolved, an about point, an about
    direction, and the angle to revolve the shape.

    Parameters
    ----------
    s : Vertex, Edge, Wire or Face
    pabout : tuple[float, float, float]
    pdir : tuple[float, float, float]
    angle: float

    Returns
    -------
    Edge, Face, Shell or Solid, depending on the input shape type

    """
    b = _BRepPrimAPI.BRepPrimAPI_MakeRevol(
        s.shape, _gp.gp_Ax1(_gp.gp_Pnt(pabout[0], pabout[1], pabout[2]),
                            _gp.gp_Dir(pdir[0], pdir[1], pdir[2])), angle, True)
    b.Build()
    if s.stype == 'Vertex':
        return Edge(b.Shape())
    elif s.stype == 'Edge':
        return Face(b.Shape())
    elif s.stype == 'Wire':
        return Shell(b.Shape())
    elif s.stype == 'Face':
        return Solid(b.Shape())
    else:
        # print('Error: Improper type for prism', s.stype)
        logger.error('Error: Improper type for revol: s' % str(s.stype))


def loft(ws, ruled=False, stype='Solid'):
    """
    Returns a solid or shell which is a fit of a list of closed wires.
    Expects a list of closed wires.

    I found OCC's BRepOffsetAPI_ThruSections buggy when each wire
    profile wasn't planar.

    Parameters
    ----------
    ws : list[Wire]
    ruled : bool, optional (default is False)
    stype : str, optional (default is 'Solid')
        The resulting shape type

    Returns
    -------
    Shell or Solid, depending on the value of stype

    """

    if stype == 'Shell':
        b = _BRepOffsetAPI.BRepOffsetAPI_ThruSections(False, ruled)
    else:
        b = _BRepOffsetAPI.BRepOffsetAPI_ThruSections(True, ruled)
    for w in ws:
        b.AddWire(_TopoDS_wire(w.shape))
    b.Build()
    if stype == 'Shell':
        return Shell(b.Shape())
    else:
        return Solid(b.Shape())


def plane_loft(ws, stype='Solid'):
    """
    Returns a solid or shell which is a fit of a list of closed wires.
    Expects a list of closed wires.

    It assumes the generating wires fit in a plane, and it assumes
    each connection face is a plane.  All wires should have the same
    number of points.

    Currently, loft() often returns bsplines when the face should be
    planar.  This forces planar faces for the rare occasions when a
    loft should only have planar faces.  It would be better to find a
    routine that simplifies bsplines into primitives when possible
    ***.

    Parameters
    ----------
    ws : list[Wire]
    stype : str, optional (default is 'Solid')

    Returns
    -------
    Shell or Solid, depending on the value of stype

    """

    profiles = []
    for w in ws:
        vs = w.subshapes('Vertex')
        profile = []
        for v in vs:
            profile.append(v.center())
        profile.append(profile[0])
        profiles.append(profile)
    faces = []
    for pt_index in range(len(profiles[0]) - 1):
        for profile_index in range(len(profiles) - 1):
            p = polygon([
                        profiles[profile_index][pt_index],
                        profiles[profile_index][pt_index + 1],
                        profiles[profile_index + 1][pt_index + 1],
                        profiles[profile_index + 1][pt_index],
                        profiles[profile_index][pt_index]])
            try:
                faces.append(plane(p))
            except NameError:
                # print('Error: Not Planar')
                logger.error('Error: Not Planar')
                sys.exit()
                # The loft must have slightly changed edges or vertices,
                # because this was a mess.
                # w1 = polygon([profiles[profile_index][pt_index],
                #              profiles[profile_index][pt_index + 1]])
                # w2 = polygon([profiles[profile_index + 1][pt_index],
                #              profiles[profile_index + 1][pt_index + 1]])
                # faces.append(loft([w1, w2], 1))

    if stype == 'Solid':
        faces.append(plane(polygon(profiles[0])))
        faces.append(plane(polygon(profiles[-1])))
    s = Shell(faces)
    if stype == 'Solid':
        s = Solid([s])
    s.fix()
    return s


def pipe(profile, spine, continuous=False, transition='sharp',
         stype='Solid', **options):
    """
    Returns a solid which is an extrusion of a closed wire profile
    along a wire spine.  Extrusion at discontinuities is controlled
    with the transition option.
    Expects a profile and a spine.

    For discontinuous spines, profile may be a list of profiles to be
    evaluated along the spine.  This forces a certain normal to the
    spine, which can be helpful for spines which don't sit in a plane.

    If the spine is continuous, change continuous to 1 to avoid bugs.

    Make sure the profile sits on the spine and is oriented
    perpendicular to the spine's direction.  When you don't do this, I
    didn't understand the returned value.

    Parameters
    ----------
    profile
    spine
    continuous : bool, optional (default is False)
    transition : str, optional (default is 'sharp')
    stype : str, optional (default is 'solid')
    **options

    Returns
    -------
    Shell or Solid, depending on the value of stype

    """

    if continuous:
        if stype == 'Shell':
            b = _BRepOffsetAPI.BRepOffsetAPI_MakePipe(
                _TopoDS_wire(spine.shape), profile.shape)
            b.Build()
            return Shell(b.Shape())
        else:
            # Only works with planar profile ***
            b = _BRepOffsetAPI.BRepOffsetAPI_MakePipe(
                _TopoDS_wire(spine.shape), plane(profile).shape)
            b.Build()
            return Solid(b.Shape())

    else:
        raw_modes = {'round': _BRepBuilderAPI.BRepBuilderAPI_RoundCorner,
                     'sharp': _BRepBuilderAPI.BRepBuilderAPI_RightCorner,
                     'transform': _BRepBuilderAPI.BRepBuilderAPI_Transformed}
        b = _BRepOffsetAPI.BRepOffsetAPI_MakePipeShell(
            _TopoDS_wire(spine.shape))
        # b.SetTolerance(1e-4, 1e-4, 1e-2) # Default
        # b.SetTolerance(1e-6, 1e-6, 1e-4) # Didn't help
        if 'contact' in options:
            contact = options['contact']
        else:
            contact = False
        if 'correct' in options:
            correct = options['correct']
        else:
            correct = False
        if isinstance(profile, list):
            for p in profile:
                b.Add(p.shape, contact, correct)
        else:
            b.Add(profile.shape, contact, correct)
        b.SetTransitionMode(raw_modes[transition])
        b.Build()
        if stype == 'Shell':
            return Shell(b.Shape())
        else:
            b.MakeSolid()
            return Solid(b.Shape())


def helical_solid(profile, rad, angle, turns):
    """
    Returns a profile spun in a helix.  Why not use pipe?  Pipe
    changed the orientation of the profile.  This routine fixes the
    orientation correctly.

    profile is in the xy plane.  The helix will pass through (0,0).

    Turns must be an integer multiple of 0.25

    This routine only generates a quarter helix solid, then replicates
    and boolean merges to make the full solid.  Therefore, it is very
    expensive.  There must be a better way.  I am also uncertain how
    interpolation is done along the spine.  It may not be exact.

    Parameters
    ----------

    profile :
    rad : float
        Helix radius
    angle : float
    turns : float
        Number of turns of the helix

    Returns
    -------

    Solid

    """

    # Create a quarter of the solid
    local_turns = 0.25
    spine = helix(rad, angle, local_turns)
    # Orient the profile normal to the helix
    profile1 = profile.copy()
    # profile1.rotatex(_math.pi/2 + angle) # This made you have to
    # cut everything
    profile1.scaley(1.0 / _math.cos(angle))
    profile1.rotatex(_math.pi / 2)
    profile1.translate((rad, 0.0, 0.0))
    profiles = []
    for count in range(2):
        local_profile = profile1.copy()
        local_profile.rotatez(count * _math.pi / 2)
        local_profile.translate((0.0, 0.0,
                                 (count * rad * _math.pi / 2 *
                                  _math.tan(angle))))
        profiles.append(local_profile)
    quarter_thread = pipe(profiles, spine, continuous=False)

    # Spin and translate the quarter into the full
    retval = quarter_thread.copy()
    for count in range(1, int(round(turns * 4))):
        local_thread = quarter_thread.copy()
        local_thread.rotatez((count % 4) * _math.pi / 2)
        local_thread.translate((0.0, 0.0,
                                count * rad * _math.pi / 2 * _math.tan(angle)))
        retval = retval + local_thread
    return retval


# Useful functions that return arbitrary shapes

def offset(s1, dist, tolerance=1e-3, join='arc', mode='skin'):
    """
    Returns a list of solids which compose the offset from a solid
    or a list of faces which compose the offset from a face

    Both BRepOffsetAPI_MakeOffsetShape and BRepOffsetAPI_MakeOffset
    fail under way too many normal conditions ***

    Parameters
    ----------
    s1 : Solid or Face
    dist : float
        Offsetting distance
    tolerance : float, optional (default is 1e-3)
    join : str, optional (default is 'arc')
    mode : str, optional (default is 'skin')
    """
    j = {'arc': _GeomAbs.GeomAbs_Arc,
         'tan': _GeomAbs.GeomAbs_Tangent,
         'int': _GeomAbs.GeomAbs_Intersection}[join]
    k = {'skin': _BRepOffset.BRepOffset_Skin,
         'pipe': _BRepOffset.BRepOffset_Pipe,
         'rectoverso': _BRepOffset.BRepOffset_RectoVerso}[mode]
    if s1.stype == 'Solid':
        b = _BRepOffsetAPI.BRepOffsetAPI_MakeOffsetShape(
                s1.shape, dist, tolerance, k, False, False, j)
        raw_shape = b.Shape()
        ss = []
        if _raw_type(raw_shape) == 'compound':
            ex = _TopExp_Explorer(raw_shape, _TopAbs.TopAbs_SOLID)
            while ex.More():
                ss.append(Solid(ex.Current()))
                ex.Next()
        elif _raw_type(raw_shape) == 'Solid':
            ss.append(Solid(raw_shape))
        else:
            # print('Warning: Unexpected type', _raw_type(raw_shape))
            logger.warning('Warning: Unexpected type %s' %
                           str(_raw_type(raw_shape)))
        return ss

    elif s1.stype == 'Face':
        s1.shape.Orientation(_TopAbs.TopAbs_FORWARD)
        rawf = _TopoDS_face(s1.shape)
        surf = _BRep_Tool_Surface(rawf)
        b = _BRepOffsetAPI.BRepOffsetAPI_MakeOffset(rawf, j)
        b.Perform(dist)
        raw_shape = b.Shape()

        # This worked too
        # b = BRepFill_OffsetWire(rawf, j)
        # b.Perform(dist)
        # s = b.Shape()

        fs = []
        if _raw_type(raw_shape) == 'compound':  # Resulting wires broken
            ex = _TopExp_Explorer(raw_shape, _TopAbs.TopAbs_WIRE)
            while ex.More():
                bf = _BRepBuilderAPI.BRepBuilderAPI_MakeFace(
                    surf, _TopoDS_wire(ex.Current()))
                fs.append(Face(bf.Face()))
                ex.Next()
        elif raw_shape.ShapeType() == _TopAbs.TopAbs_EDGE:  # Over-simplified
            bw = _BRepBuilderAPI.BRepBuilderAPI_MakeWire()
            bw.Add(raw_shape)
            bf = _BRepBuilderAPI.BRepBuilderAPI_MakeFace(
                surf, _TopoDS_wire(bw.Wire()))
            fs.append(Face(bf.Face()))
        elif raw_shape.ShapeType() == _TopAbs.TopAbs_WIRE:
            bf = _BRepBuilderAPI.BRepBuilderAPI_MakeFace(
                surf, _TopoDS_wire(raw_shape))
            fs.append(Face(bf.Face()))
        return fs

    else:
        # print('Error: Only solid or face allowed for offset')
        logger.error('Error: Only solid or face allowed for offset')
