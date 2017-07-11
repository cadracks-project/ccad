#!/usr/bin/python
# coding: utf-8

r"""Miscellaneous parts

This example shows how to inherit a Part class and reuse
its geometry property to create another geometry.

Created as a learning exercise when learning ccad (G. Florent)

"""

from __future__ import division

import ccad.model as cm
import ccad.display as cd


class Tube(cm.Part):
    r"""A simple tube

    Parameters
    ----------
    outer_diameter : float
        The tube outer diameter
    inner_diameter : float
        The tube inner diameter
    length : float
        The tube length

    """
    def __init__(self, outer_diameter, inner_diameter, length):
        self.outer_diameter = outer_diameter
        self.inner_diameter = inner_diameter
        self.length = length

    @property
    def geometry(self):
        r"""Part geometry

        Returns
        -------
        Solid : the tube as a ccad Solid

        """
        return cm.cylinder(self.outer_diameter / 2, self.length) - \
            cm.cylinder(self.inner_diameter / 2, self.length)


class TubeWithTail(Tube):
    r"""A tube with a 'tail'

    TubeWithTail is a subclass of Tube

    Parameters
    ----------
    outer_diameter : float
        The tube outer diameter
    inner_diameter : float
        The tube inner diameter
    length : float
        The tube length
    tail_length : float
        The length of the tail beyond the tube outer surface
    tail_thickness : float
        The thickness of the tail
    fillet_radius : float
        The radius of the fillet at the junction between the tube and the tail

    """
    def __init__(self, outer_diameter, inner_diameter, length, tail_length,
                 tail_thickness, fillet_radius):
        super(TubeWithTail, self).__init__(outer_diameter, inner_diameter,
                                           length)
        self.tail_length = tail_length
        self.tail_thickness = tail_thickness
        self.fillet_radius = fillet_radius

    @property
    def geometry(self):
        r"""Part geometry

        Returns
        -------
        Solid

        """
        tail = cm.box(self.tail_length + (self.outer_diameter / 2 +
                                          self.inner_diameter / 2) / 2,
                      self.tail_thickness, self.length)
        tail.translate((0., -self.tail_thickness / 2, 0.))
        tail.translate(((self.outer_diameter / 2 + self.inner_diameter / 2) / 2,
                        0, 0))
        return cm.fillet_fuse(super(TubeWithTail, self).geometry, tail, 2.)


class TubeWithTwoTails(Tube):
    r"""A tube with two 'tail's that are symmetrical to the YZ plane

    TubeWithTwoTails is a subclass of Tube

    Parameters
    ----------
    outer_diameter : float
        The tube outer diameter
    inner_diameter : float
        The tube inner diameter
    length : float
        The tube length
    tail_length : float
        The length of the tail beyond the tube outer surface
    tail_thickness : float
        The thickness of the tail
    tail_spacing : float
        The gap between the 2 tails
    fillet_radius : float
        The radius of the fillet at the junction between the tube and the tail

    """
    def __init__(self, outer_diameter, inner_diameter, length, tail_length,
                 tail_thickness, tail_spacing, fillet_radius):
        super(TubeWithTwoTails, self).__init__(outer_diameter, inner_diameter,
                                               length)
        self.tail_length = tail_length
        self.tail_thickness = tail_thickness
        self.tail_spacing = tail_spacing
        self.fillet_radius = fillet_radius

    @property
    def geometry(self):
        r"""Part geometry

        Returns
        -------
        Solid : the tube with 2 tails as a ccad Solid

        """
        # Create the tails
        left_tail = cm.box(self.tail_length + self.outer_diameter / 2,
                           self.tail_thickness, self.length)
        right_tail = cm.box(self.tail_length + self.outer_diameter / 2,
                            self.tail_thickness, self.length)
        # Position the tails
        left_tail.translate((0, -self.tail_spacing / 2 - self.tail_thickness,
                             0))
        right_tail.translate((0, self.tail_spacing / 2, 0))

        # Create the tube
        # TODO : why not use Tube
        tube_ = cm.cylinder(self.outer_diameter / 2, self.length) -\
            cm.cylinder(self.inner_diameter / 2, self.length)

        # Remove the part of the tails that are inside the tube
        trimmed_tails = left_tail + right_tail -\
            cm.cylinder(self.inner_diameter / 2, self.length)

        # Fuse the tube and the tails
        union = tube_ + trimmed_tails
        union.fillet(0.5, [10, 37])
        union.fillet(2.5, [21, 47])

        return union


class TubeWithGuide(cm.Part):
    r"""A (big) tube joined to an external and parallel other tube

    Parameters
    ----------
    outer_diameter : float
        The tube outer diameter
    inner_diameter : float
        The tube inner diameter
    length : float
        The tube length
    small_hole_diameter : float
    small_hole_distance_to_od : float
        The distance between the outer surface of the main tube and the outer
        surface of the smaller tube
    thickness_around_small_hole : float
        The minimal material thickness around the small hole

    """
    def __init__(self, outer_diameter, inner_diameter, length,
                 small_hole_diameter, small_hole_distance_to_od,
                 thickness_around_small_hole):
        self.outer_diameter = outer_diameter
        self.inner_diameter = inner_diameter
        self.length = length
        self.small_hole_diameter = small_hole_diameter
        self.small_hole_distance_to_od = small_hole_distance_to_od
        self.thickness_around_small_hole = thickness_around_small_hole

    @property
    def geometry(self):
        r"""Part geometry

        Returns
        -------
        Solid : the tube with a guide as a ccad solid

        """
        main_cyl = cm.cylinder(self.outer_diameter / 2, self.length)
        small_tube = cm.cylinder(self.thickness_around_small_hole +
                                 self.small_hole_diameter / 2 + 0.1,
                                 self.length)
        small_hole = cm.cylinder(self.small_hole_diameter / 2, self.length)
        small_tube.translate((self.outer_diameter/2 +
                              self.small_hole_distance_to_od +
                              self.small_hole_diameter/2,
                              0, 0))
        small_hole.translate((self.outer_diameter/2 +
                              self.small_hole_distance_to_od +
                              self.small_hole_diameter/2,
                              0, 0))

        return cm.fillet_fuse(main_cyl, small_tube, 200) -\
            cm.cylinder(self.inner_diameter / 2, self.length) - small_hole


class TubeEnd(cm.Part):
    r"""A part to finish a tube, aka a tube cap

    Parameters
    ----------
    big_diameter : float
    small_diameter : float
    small_diameter_length : float
    big_diameter_length : float

    """
    def __init__(self, big_diameter, small_diameter, small_diameter_length,
                 big_diameter_length):
        self.big_diameter = big_diameter
        self.small_diameter = small_diameter
        self.small_diameter_length = small_diameter_length
        self.big_diameter_length = big_diameter_length

    @property
    def geometry(self):
        r"""Geometry creation

        Returns
        -------
        Solid : the tube end as a ccad Solid

        """
        return cm.cylinder(self.big_diameter / 2, self.big_diameter_length) \
            + cm.cylinder(self.small_diameter / 2, self.big_diameter_length +
                          self.small_diameter_length)


class TubeEndWithHole(TubeEnd):
    r"""A TubeEnd with a central hole

    TubeEndWithHole inherits TubeEnd and uses its geometry property

    Parameters
    ----------
    big_diameter : float
    small_diameter : float
    small_diameter_length : float
    big_diameter_length : float
    hole_diameter : float

    """
    def __init__(self, big_diameter, small_diameter, small_diameter_length,
                 big_diameter_length, hole_diameter):
        super(TubeEndWithHole, self).__init__(big_diameter, small_diameter,
                                              small_diameter_length,
                                              big_diameter_length)
        self.hole_diameter = hole_diameter

    @property
    def geometry(self):
        r"""Geometry creation, using the geometry of the TubeEnd parent class

        Returns
        -------
        Solid : the tube end with hole as a ccad solid

        """
        return super(TubeEndWithHole, self).geometry - \
            cm.cylinder(self.hole_diameter / 2, self.big_diameter_length +
                        self.small_diameter_length)


class TubeEndWithBlindHole(TubeEnd):
    r"""A TubeEnd with a central hole that is open only at the bigger diameter
    end

    Parameters
    ----------
    big_diameter : float
    small_diameter : float
    small_diameter_length : float
    big_diameter_length : float
    hole_diameter : float
    hole_depth : float

    """
    def __init__(self, big_diameter, small_diameter, small_diameter_length,
                 big_diameter_length, hole_diameter, hole_depth):
        super(TubeEndWithBlindHole, self).__init__(big_diameter, small_diameter,
                                                   small_diameter_length,
                                                   big_diameter_length)
        self.hole_diameter = hole_diameter
        self.hole_depth = hole_depth

    @property
    def geometry(self):
        r"""Geometry creation, using the geometry of the TubeEnd parent class

        Returns
        -------
        Solid : the tube end with blind hole as a ccad solid

        """
        return super(TubeEndWithBlindHole, self).geometry - \
            cm.cylinder(self.hole_diameter / 2, self.hole_depth)


class TubeEndWithBlindHoleAndLip(TubeEndWithBlindHole):
    r"""A TubeEnd with a central hole that is open only at the bigger diameter
    end and with a lip at the hole entrance (e.g. to accomodate a bearing)

    Inherits TubeEndWithBlindHole and uses its geometry

    Parameters
    ----------
    big_diameter : float
    small_diameter : float
    small_diameter_length : float
    big_diameter_length : float
    hole_diameter : float
    hole_depth : float
    lip_length : float
        The lip dimension along the main tube axis
    lip_od : float
        The lip outer diameter. Its inner diameter is the same as the
        hole diameter.

    """
    def __init__(self, big_diameter, small_diameter, small_diameter_length,
                 big_diameter_length, hole_diameter, hole_depth, lip_length,
                 lip_od):
        super(TubeEndWithBlindHoleAndLip, self).__init__(big_diameter,
                                                         small_diameter,
                                                         small_diameter_length,
                                                         big_diameter_length,
                                                         hole_diameter,
                                                         hole_depth)
        self.lip_length = lip_length
        self.lip_od = lip_od

    @property
    def geometry(self):
        r"""Geometry creation, using the geometry of the TubeEndWithBlindHole
        parent class

        Returns
        -------
        Solid : the tube end with blind hole and lip as a ccad Solid

        """
        base_part = super(TubeEndWithBlindHoleAndLip, self).geometry
        lip = Tube(outer_diameter=self.lip_od,
                   inner_diameter=self.hole_diameter,
                   length=self.lip_length).geometry
        base_part.translate((0, 0, self.lip_length))
        return base_part + lip


if __name__ == "__main__":
    v1 = cd.view()
    te = TubeEnd(big_diameter=10., small_diameter=8., small_diameter_length=20.,
                 big_diameter_length=10.).geometry
    tewh = TubeEndWithHole(big_diameter=10., small_diameter=8.,
                           small_diameter_length=20., big_diameter_length=10.,
                           hole_diameter=2.).geometry
    tube = Tube(outer_diameter=10, inner_diameter=8, length=2).geometry
    tube_with_tail = TubeWithTail(outer_diameter=10, inner_diameter=8, length=2,
                                  tail_length=30., tail_thickness=2.,
                                  fillet_radius=2.).geometry
    tube_with_2_tails = TubeWithTwoTails(outer_diameter=10, inner_diameter=8,
                                         length=2, tail_length=30.,
                                         tail_thickness=2., tail_spacing=2.,
                                         fillet_radius=2.).geometry
    tube_with_guide = TubeWithGuide(outer_diameter=12, inner_diameter=10,
                                    length=2, small_hole_diameter=2,
                                    small_hole_distance_to_od=-2,
                                    thickness_around_small_hole=1.).geometry
    tube_with_blind_hole_and_lip = \
        TubeEndWithBlindHoleAndLip(big_diameter=8, small_diameter=6,
                                   small_diameter_length=30,
                                   big_diameter_length=2, hole_diameter=3,
                                   hole_depth=20, lip_length=1,
                                   lip_od=4).geometry
    v1.display(tube_with_blind_hole_and_lip)
    # te.to_step("tube_end.step")
    cd.start()
