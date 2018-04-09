#!/usr/bin/env python
# coding: utf-8

r"""Planar net"""

from __future__ import print_function
import networkx as nx
import matplotlib.pyplot as plt
import ccad.model as cm
import ccad.display as cd
import numpy as np
import copy
import pdb
import logging

logger = logging.getLogger(__name__)


class PlanarNet(nx.Graph):
    def __init__(self, **kwargs):
        """

        Parameters
        ----------
        pt : np.array (N x 2)
            points in the 0xy plane
        N : number of nodes of the first polygon
        l : edge length of the first polygon

        """
        self.folded = False
        pt = kwargs.pop('pt', [])
        N = kwargs.pop('N', 3)
        self.l = kwargs.pop('l', 1)
        if pt == []:
            al = (N - 2) * np.pi / (2 * N)
            self.r = np.sin(al) / np.sin(2 * np.pi / N)
            self.s = np.sqrt(self.r**2 - self.l**2/4.)
            t = np.linspace(0, N, N+1)
            u = 2 * np.pi * t / N
            pt = self.r * np.c_[np.cos(u), np.sin(u)]
        N = pt.shape[0]
        # conversion to 3D
        self.pt = np.c_[pt[:, 0], pt[:, 1], np.zeros(N)]
        w0 = cm.polygon(self.pt)
        face0 = cm.plane(w0)
        self.lfaces = [face0]
        self.nnode = 1
        nx.Graph.__init__(self)
        self.add_node(0,normal=face0.normal())
        self.add_node(0)
        self.pos = dict()
        self.pos[0] = face0.center()[0:2]

    def __repr__(self):
        st = 'PlanarNet :' + str(self.nnode) + '\n'
        if self.folded:
            st = st + 'Folded\n'
        for f in self.lfaces:
            st = st + f.__repr__()
        return st

    def __add__(self, other):
        # nodes relabeling
        if not (self.folded ^ other.folded):
            offset_nodes = np.max(np.array(self.node.keys()))+1
            other_nodes = np.array(self.node.keys())
            other_nodes_offset = other_nodes + offset_nodes
            mapping = dict(zip(list(other_nodes), list(other_nodes_offset)))
            other_translated = nx.relabel_nodes(other, mapping)
            other_translated.remove_node(0)
            other_translated.pos = dict(zip(list(other_nodes_offset),
                                            other.pos.values()))
            # graphs composition
            new = nx.compose(self, other_translated)
            pos = copy.copy(self.pos)
            other_translated_pos = other_translated.pos
            pos.update(other_translated_pos)
            new.pos = pos
            # extend ccad entities list of faces and shell
            new.lfaces = self.lfaces + other.lfaces
            new.shell = cm.Shell(new.lfaces)
            new.nnode = self.nnode + other.nnode

            return new
        else:
            logger.error('Impossible to add 2 PlanarNet '
                         'with different folded status')

    def __copy__(self):
        return self

    def translated(self, pdir):
        """ translation along pdir

        Parameter
        ---------
        pdir : (x,y,z)

        """
        new = copy.deepcopy(self)
        new.shell = cm.translated(self.shell, pdir)
        new.lfaces = new.shell.subshapes('Face')
        for k, f in enumerate(new.lfaces):
            new.pos[k] = f.center()[0:2]
        return new

    def rotated(self, pabout, angle):
        pass


    def plot(self,**kwargs):
        """ plot planarnet

        """

        bnodes = kwargs.pop('bnodes',False)
        bedges = kwargs.pop('bedges',False)
        blabels = kwargs.pop('blabels',False)

        for f in self.lfaces:
            f.plot(**kwargs)
            for k, e in enumerate(f.subshapes('Edge')):
                eps = self.l/15.
                xe, ye = e.center()[0:2]
                lv = e.subshapes('Vertex')
                p0 = np.array(lv[0].center())
                p1 = np.array(lv[1].center())
                pdir = p1-p0
                norm = np.cross(pdir, np.array([0, 0, 1]))
                norm = norm/np.linalg.norm(norm)
                plt.annotate(str(k), xy=(xe, ye),
                             xytext=(xe-norm[0]*eps, ye-norm[1]*eps),
                             color='b')
        if bnodes:
            nx.draw_networkx_nodes(self, self.pos, node_color='b', node_size=50, alpha=0.5)
        if bedges:
            nx.draw_networkx_edges(self, self.pos, width=3, edge_color='k')

        lpos = { k : (self.pos[k][0]+0.05, self.pos[k][1]+0.05) for k in self.pos}

        if blabels:
            nx.draw_networkx_labels(self, lpos, font_size=18)

    def replicate(self, iface=0, iedge=0, angle=np.pi):
        """  replicate face iface along edge iedge

        Parameters
        ----------

        iface : int
            face index
        iedge : int
            edge index
        angle : float
            folding angle

        Notes
        -----
        add a node in the graph

        """
        self.nnode = self.nnode + 1
        # create a new face from face with index iface
        new_face = self.lfaces[iface].copy()
        # get the active edge of iface
        # points : edge termination
        # vedge : edge vector (non normalized)
        # axed : mirror axis orthogonal to vedge
        ed = self.lfaces[iface].subshapes('Edge')[iedge]
        points = ed.poly()
        vedge = np.array(points[1]) - np.array(points[0])
        axed = np.cross(vedge, np.array([0, 0, 1]))
        # mirror new face w.r.t axed
        new_face = cm.mirrored(new_face, ed.center(), axed)
        # modify normal orientation
        new_face = cm.rotated(new_face, new_face.center(), (1, 0, 0), np.pi)

        # append new face in PlanarNet.lfaces
        # update underlying graph
        # node position at centroid of the face

        self.lfaces.append(new_face)
        node_num = self.nnode - 1
        self.add_node(node_num,normal=new_face.normal())
        self.pos[node_num] = new_face.center()[0:2]
        self.add_edge(iface, node_num, angle=angle, iedge=iedge)
        self.shell = cm.Shell(self.lfaces)

    def expand(self,iface,iedge,nedges,sign=1,angle=np.pi):
        """ expand face iface along edge iedge

        Parameters
        ----------
        iface : int
        iedge : int
        nedges : int
        angle : float

        """

        self.nnode = self.nnode + 1
        # get the selected edge of the selected face
        ed = self.lfaces[iface].subshapes('Edge')[iedge]
        points = ed.poly()
        z0 = points[0][0]+1j*points[0][1]
        z1 = points[1][0]+1j*points[1][1]

        lz = [z0, z1]
        for  k in range(nedges-2):
            dz = lz[-2]-lz[-1]
            lz.append(lz[-1]+ np.abs(dz)*np.exp(1j*(np.angle(dz)+sign*(nedges-2)*np.pi/nedges)))
        lpts = []
        for k in range(nedges):
            lpts.append((np.real(lz[k]),np.imag(lz[k]),0.0))
        lpts.append(lpts[0])
        new_face = cm.plane(cm.polygon(lpts))
        if new_face.normal()[2]==-1:
            new_face = cm.plane(cm.polygon(lpts[::-1]))
        self.lfaces.append(new_face)
        node_num = self.nnode - 1
        self.add_node(node_num,normal=new_face.normal())
        self.pos[node_num] = new_face.center()[0:2]
        self.add_edge(iface, node_num, angle=angle, iedge=iedge)
        self.shell = cm.Shell(self.lfaces)

    def fold(self, reverse=False):
        """ fold edges of the PlanarNet

        Returns
        -------
        A solid or a compound of faces

        Notes
        -----
        This method fold the planar net w.r.t to the edge angles.
        It yields a shell member

        """

        for edge in self.edges():
            if0 = edge[0]
            if1 = edge[1]
            ag = self.edge[if0][if1]['angle']
            # handle folding direction
            if reverse:
                angle = -ag
            else:
                angle = ag
            iedge = self.edge[if0][if1]['iedge']
            ed = self.lfaces[if0].subshapes('Edge')[iedge]
            points = ed.poly()
            pdir = np.array(points[1]) - np.array(points[0])
            pabout = ed.center()

            # create 2 subgraphs
            self.remove_edge(if0, if1)
            lgraphs = list(nx.connected_component_subgraphs(nx.Graph(self)))

            ln0 = lgraphs[0].node.keys()
            ln1 = lgraphs[1].node.keys()
            self.add_edge(if0, if1, angle=ag, iedge=iedge)
            if if1 in ln1:
                lfaces1 = ln1
            else:
                lfaces1 = ln0
            # fold all faces in set lfaces1
            for f in lfaces1:
                self.lfaces[f] = cm.rotated(self.lfaces[f], pabout, pdir, angle)

        # update faces centroid in the Graph

        for iface in self.node:
            face = self.lfaces[iface]
            self.pos[iface] = face.center()[0:2]

        # creates the shell
        self.shell = cm.Shell(self.lfaces)
        if reverse:
            self.folded = False
        else:
            self.folded = True
            asolid = cm.Solid([self.shell])
            if asolid.check():
                vertices = asolid.subshapes('Vertex')
                edges = asolid.subshapes('Edge')
                faces = asolid.subshapes('Face')
                Euler = len(vertices)-len(edges)+len(faces)
                print("closed shape")
                print("V",len(vertices))
                print("E",len(edges))
                print("F",len(faces))
                print("Euler check (2): V-E+F :",Euler)

            else:
                print("open shape")

            return asolid

    def display(self, folded=True):
        viewer = cd.view()
        if folded:
            viewer.display(self.shell)
        else:
            viewer.display(self.shell)
        cd.start()

if __name__ == "__main__":
    p1 = PlanarNet()
    alpha = np.pi-np.arccos(1/3.)
    p1.replicate(iedge=0, angle = alpha)
    p1.replicate(iedge=1, angle = alpha)
    p1.replicate(iedge=2, angle = alpha)
    tetra = p1.fold()
    tetra.to_html('tetraedre.html')
