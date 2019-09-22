"""
GMSH CAD support module
=======================
:synopsis: Manipulates ``.geo`` input files for ``gmsh``.

.. moduleauthor:: Pavel Ferkl <pavel.ferkl@gmail.com>
"""
from __future__ import print_function, division
import os
import re
import shutil
import subprocess as sp
import numpy as np
NAMES = {
    'point': 'Point',
    'line': 'Line',
    'line_loop': 'Line Loop',
    'surface': 'Plane Surface',
    'surface_loop': 'Surface Loop',
    'volume': 'Volume',
    'periodic_surface_X': 'Periodic Surface',
    'periodic_surface_Y': 'Periodic Surface',
    'physical_surface': 'Physical Surface',
    'physical_volume': 'Physical Volume'
}
NAME_LIST = [
    'point',
    'line',
    'line_loop',
    'surface',
    'surface_loop',
    'volume',
    'periodic_surface_X',
    'periodic_surface_Y',
    'physical_surface',
    'physical_volume'
]


def findall_top(regex, text):
    """Like ``re.findall``, but returns only top level group in list.

    Args:
        regex (str): regex patern
        text (str): text to search for patern

    Returns:
        list: list of all matches
    """
    matches = re.finditer(regex, text)
    lst = []
    for match in matches:
        lst.append(match.group(0))
    return lst


def read_geo(geo_file, plane_surface=True):
    """Read ``gmsh`` input file and extract geometry information.

    Uses regular expressions. Some geo files use Surface, some Plane Surface.
    You should specify what you want to read.

    Args:
        geo_file (str): input filename
        plane_surface (bool, optional): input file contains "Plane Surface"
            keyword

    Returns:
        dict: dictionary with read lines separated into points, lines, etc.
    """
    with open(geo_file, "r") as text_file:
        text = text_file.read()
        sdat = {}
        rexp = {}
        rexp['point'] = r'Point\s?[(][0-9]+[)]\s[=]\s[{](.*?)[}][;]'
        rexp['line'] = r'Line\s?[(][0-9]+[)]\s[=]\s[{][0-9]+[,]\s?[0-9]+[}][;]'
        rexp['line_loop'] = (
            r'Line\sLoop\s?[(][0-9]+[)]\s[=]\s[{]([+-]?[0-9]+[,]?\s?)+[}][;]'
        )
        if plane_surface:
            rexp['surface'] = (
                r'Plane\sSurface\s?[(][0-9]+[)]\s[=]\s[{]([0-9]+[,]?\s?)+[}][;]'
            )
        else:
            rexp['surface'] = (
                r'(Surface\s[(][0-9]+[)]\s[=]\s[{]([0-9]+[,]?)+[}][;])'
                + r'(?!.*Physical.*)',
            )
        rexp['physical_surface'] = (
            r'Physical\sSurface\s?[(][0-9]+[)]\s[=]\s[{]([0-9]+[,]?\s?)+[}][;]'
        )
        rexp['surface_loop'] = (
            r'Surface\sLoop\s?[(][0-9]+[)]\s[=]\s[{]([+-]?[0-9]+[,]?\s?)+[}][;]'
        )
        rexp['volume'] = (
            r'Volume\s?[(][0-9]+[)]\s[=]\s[{]([0-9]+[,]?\s?)+[}][;]'
        )
        rexp['physical_volume'] = (
            r'Physical\sVolume\s?[(]["][a-z]+["][)]\s[=]\s'
            + r'[{]([0-9]+[,]?\s?)+[}][;]'
        )
        for key in rexp:
            sdat[key] = findall_top(rexp[key], text)
        return sdat


def fix_strings(strings):
    """Remove negative signs (orientation) from loops.

    Used for OpenCASCADE kernel compatibility.

    Args:
        strings (list): list of line or surface loops in string format
    """
    for i, line in enumerate(strings):
        strings[i] = re.sub('[-]', '', line)


def save_geo(geo_file, sdat, opencascade=True):
    """Save ``gmsh`` CAD geometry input to file.

    Input is a dictionary with prepared string lines.

    Args:
        geo_file (str): filename
        sdat (dict): characterized geometry in string format
        opencascade (bool, optional): prepend OpenCASCADE keyword if True
    """
    with open(geo_file, "w") as fhl:
        if opencascade:
            fhl.write('SetFactory("OpenCASCADE");\n')
        for key in NAME_LIST:
            if key in sdat:
                for line in sdat[key]:
                    fhl.write("{}\n".format(line))


def geo2brep(geo_file, brep_file):
    """Convert ``gmsh`` CAD geometry to BREP format.

    ``gmsh`` is used for the conversion. A temporary file ``geo2brep.geo`` is
    created (overwrites existing file if it exists).

    Args:
        geo_file (str): input filename
        brep_file (str): output filename
    """
    wfile = 'geo2brep.geo'
    with open(wfile, "w") as fhl:
        fhl.write('SetFactory("OpenCASCADE");\n')
        fhl.write('Merge "{}";\n'.format(geo_file))
        fhl.write('Save "{}";\n'.format(brep_file))
    sp.Popen(['gmsh', wfile, '-parse_and_exit']).wait()
    os.remove(wfile)


def brep2geo(brep_file, geo_file):
    """Convert BREP CAD geometry to ``gmsh`` native format.

    ``gmsh`` is used for the conversion. A temporary file ``brep2geo.geo`` is
    created (overwrites existing file if it exists).

    Args:
        brep_file (str): input filename
        geo_file (str): output filename
    """
    wfile = 'brep2geo.geo'
    with open(wfile, "w") as fhl:
        fhl.write('SetFactory("OpenCASCADE");\n')
        fhl.write('Merge "{}";\n'.format(brep_file))
    sp.Popen(['gmsh', wfile, '-0']).wait()
    shutil.move(wfile + '_unrolled', geo_file)
    os.remove(wfile)


def extract_data(sdat):
    """Extract ``gmsh`` geometry data read by :func:`read_geo`.

    Only coordinates are taken from points. Point sizing if any is discarded.

    Opposite of :func:`collect_strings`.

    Args:
        sdat(dict): geometry data in string format

    Returns:
        dict: extracted geometry data
    """
    edat = {}
    for key in sdat:
        lines = dict()
        for line in sdat[key]:
            part = line.split("(")
            if key == "physical_volume":
                ind = part[1].split(")")[0]  # ID of the element
                if ind == '"cells"':
                    ind = 1
                elif ind == '"walls"':
                    ind = 2
            else:
                ind = int(part[1].split(")")[0])  # ID of the element
            fraction = line.split("{")
            fraction = fraction[1].split("}")
            fraction = fraction[0].split(",")
            if key == "point":  # point data consists of floats
                # ignore the optional fourth argument (defines mesh coarseness)
                fraction = np.array(fraction[0:3])
                fraction = fraction.astype(np.float)
                for j, number in enumerate(fraction):
                    if abs(number) < 1e-8:
                        fraction[j] = 0
            else:  # other data consists of integers
                fraction = np.array(fraction)
                fraction = np.absolute(fraction.astype(np.int)).tolist()
            lines[ind] = fraction
        edat[key] = lines
    return edat


def collect_strings(edat):
    """Convert extracted data to string format.

    Opposite of :func:`extract_data`.

    Args:
        edat(dict): extracted geometry data

    Returns:
        dict: geometry data in string format
    """
    sdat = {}
    for key in edat:
        sdat[key] = []
        if key == 'periodic_surface_X':
            for j in edat[key]:
                sdat[key].append(
                    '{0} {{{1}}} = {{{2}}} Translate{{-1,0,0}};'.format(
                        NAMES[key], j[0], j[1]
                    )
                )
        elif key == 'periodic_surface_Y':
            for j in edat[key]:
                sdat[key].append(
                    '{0} {{{1}}} = {{{2}}} Translate{{0,-1,0}};'.format(
                        NAMES[key], j[0], j[1]
                    )
                )
        else:
            for i, j in edat[key].items():
                j = ','.join(str(e) for e in j)
                sdat[key].append('{0} ({1}) = {{{2}}};'.format(
                    NAMES[key], i, j
                ))
    return sdat


def surfaces_in_plane(edat, coord, direction):
    """Finds surfaces that lie completely in specified plane.

    Plane must be normal to one of cartesian axes.

    Args:
        edat (dict): extracted geometry data
        coord (float): point on the chosen axis
        direction (int): order of coordinate axis

    Returns:
        list: line loops in specified plane
    """
    points_in_plane = []
    for i, point in edat['point'].items():
        if point[direction] == coord:
            points_in_plane.append(i)
    lines_in_plane = []
    for i, line in edat['line'].items():
        if line[0] in points_in_plane and line[1] in points_in_plane:
            lines_in_plane.append(i)
    line_loops_in_plane = []
    for i, line_loop in edat['line_loop'].items():
        log = True
        for line in line_loop:
            if line not in lines_in_plane:
                log = False
        if log:
            line_loops_in_plane.append(i)
    return line_loops_in_plane


def other_surfaces(edat, surfs):
    """Find boundary surfaces, which are not in ``surfs``.

    Assumes that inner surfaces are shared by two volumes. Remove duplicates
    before calling this function.

    Args:
        edat (dict): extracted geometry data
        surfs (list): list of surfaces, which should not be returned

    Returns:
        list: boundary surfaces, which are not in ``surfs``
    """
    all_surfaces = []
    for surface_loops in edat['volume'].values():
        for surface_loop in surface_loops:
            for surfaces in edat['surface_loop'][surface_loop]:
                all_surfaces += edat['surface'][surfaces]
    count = dict()
    for surface in all_surfaces:
        if surface in count:
            count[surface] += 1
        else:
            count[surface] = 1
    surf = [
        i for i, j in count.items() if j == 1
        and i not in surfs
    ]
    return surf


def periodic_surfaces(edat, surfaces, vec, eps=1e-8):
    """Find periodic surface pairs in specified direction.

    Only linear periodicity is supported. Checks for surfaces with points
    offset by specified vector within a tolerance.

    Args:
        edat (dict): extracted geometry data
        surfaces (list): boundary surfaces
        vec (ndarray): offset vector specification
        eps (float, optional): tolerance

    Returns:
        list: periodic surface pairs
    """
    surface_points = dict()  # point IDs for each boundary surface
    boundary_points = dict()  # dictionary with only boundary points
    for surface in surfaces:
        surface_points[surface] = []
        for line in edat['line_loop'][surface]:
            for point in edat['line'][line]:
                if point not in surface_points[surface]:
                    surface_points[surface] += [point]
                if point not in boundary_points:
                    boundary_points[point] = edat['point'][point]
    # sort point IDs so that you can compare later
    for point in surface_points.values():
        point.sort()
    # dictionary with ID of periodic point for each point that has one
    periodic_points = dict()
    for i, point in boundary_points.items():
        for j, secondpoint in boundary_points.items():
            if np.sum(np.abs(point + vec - secondpoint)) < eps:
                periodic_points[i] = j
    psurfs = []  # list of periodic surface pairs (IDs)
    for i, surface in surface_points.items():
        # Try to create surface using IDs of periodic points. Use None if there
        # is no periodic point in specified direction.
        per_surf = [
            periodic_points[point] if point in periodic_points else None
            for point in surface
        ]
        if None not in per_surf:
            per_surf.sort()  # sort so you can find it
            # use ID of current surface and find ID of periodic surface
            psurfs.append(
                [
                    i,
                    list(surface_points.keys())[
                        list(surface_points.values()).index(per_surf)
                    ]
                ]
            )
    return psurfs


def identify_duplicity(edat, key, number, eps):
    """Core algorithm for removing duplicities.

    User should call :func:`remove_duplicity` instead.

    Args:
        edat (dict): extracted geometry data
        key (str): type of geometry
        number (str): number type (float or integer)
        eps (float): tolerance

    Returns:
        dict: duplicit objects
    """
    dupl = dict()
    if number == 'float':
        for i, item1 in edat[key].items():
            for j, item2 in edat[key].items():
                if i != j and i > j and np.sum(np.abs(item1 - item2)) < eps:
                    if i not in dupl:
                        dupl[i] = []
                    dupl[i].append(j)
    elif number == 'integer':
        for i, item1 in edat[key].items():
            for j, item2 in edat[key].items():
                if i != j and i > j and sorted(item1) == sorted(item2):
                    if i not in dupl:
                        dupl[i] = []
                    dupl[i].append(j)
    else:
        raise Exception('number argument must be float or integer')
    return dupl


def remove_duplicit_ids_from_keys(edat, dupl, key):
    """Removes duplicit IDs from IDs of entities.

    Args:
        edat (dict): extracted geometry data
        dupl (dict): duplicit objects
        key (str): type of geometry
    """
    for i in dupl:
        del edat[key][i]


def remove_duplicit_ids_from_values(edat, dupl, key):
    """Removes duplicit IDs from values of entities.

    Args:
        edat (dict): extracted geometry data
        dupl (dict): duplicit objects
        key (str): type of geometry
    """
    for values in edat[key].values():
        for j, value in enumerate(values):
            if value in dupl:
                values[j] = min(dupl[value])


def remove_duplicity(edat, eps=1e-10):
    """Removes duplicit points, lines, etc.

    Args:
        edat (dict): extracted geometry data
        eps (float): tolerance
    """
    # points
    dupl = identify_duplicity(edat, 'point', 'float', eps)
    remove_duplicit_ids_from_keys(edat, dupl, 'point')
    remove_duplicit_ids_from_values(edat, dupl, 'line')
    # lines
    dupl = identify_duplicity(edat, 'line', 'integer', eps)
    remove_duplicit_ids_from_keys(edat, dupl, 'line')
    remove_duplicit_ids_from_values(edat, dupl, 'line_loop')
    # line loops
    dupl = identify_duplicity(edat, 'line_loop', 'integer', eps)
    remove_duplicit_ids_from_keys(edat, dupl, 'line_loop')
    remove_duplicit_ids_from_keys(edat, dupl, 'surface')
    remove_duplicit_ids_from_values(edat, dupl, 'surface_loop')
    # there are no duplicit volumes


def split_loops(edat, key):
    """Makes sure that line and surface loops contain only one loop.

    Surfaces and volumes with holes are instead defined in Surface and Volume
    entries, respectively. Needed because gmsh unrolls geometry in a way, which
    is unusable with OpenCASCADE kernel.

    This function is slow. It does not catch all loops.

    Args:
        edat (dict): extracted geometry data
        key (str): type of geometry
    """
    if key == 'line_loop':
        key2 = 'surface'
    elif key == 'surface_loop':
        key2 = 'volume'
    else:
        raise Exception('can be called only for line_loop or surface_loop')
    for i, item1 in edat[key].items():
        for j, item2 in edat[key].items():
            if i != j and set(item2).issubset((set(item1))):
                for value in item2:
                    item1.remove(value)
                edat[key][i] = item1
                edat[key2][i] = [i, j]
                break


def move_to_box(infile, wfile, outfile, mvol):
    """Moves periodic closed foam to periodic box.

    Uses gmsh, specifically boolean operations and transformations from
    OpenCASCADE. The result is unrolled to another geo file so that it can be
    quickly read and worked with in the follow-up work. Operations are
    performed two times. First for walls (first half of volumes) and then for
    cells.

    Save output to ``outfile``.

    Args:
        infile (str): input filename
        wfile (str): working filename
        outfile (str): output filename
        mvol (int): number of volumes
    """
    with open(wfile, 'w') as wfl:
        hvol = int(mvol / 2)
        wfl.write('SetFactory("OpenCASCADE");\n\n')
        wfl.write('Include "{0}";\n\n'.format(infile))
        wfl.write('Block({0}) = {{-1,-1,-1,3,3,1}};\n'.format(mvol + 1))
        wfl.write('Block({0}) = {{-1,-1, 1,3,3,1}};\n'.format(mvol + 2))
        wfl.write('Block({0}) = {{-1,-1, 0,3,3,1}};\n'.format(mvol + 3))
        wfl.write('Block({0}) = {{-1,-1,-1,3,1,3}};\n'.format(mvol + 4))
        wfl.write('Block({0}) = {{-1, 1,-1,3,1,3}};\n'.format(mvol + 5))
        wfl.write('Block({0}) = {{-1, 0,-1,3,1,3}};\n'.format(mvol + 6))
        wfl.write('Block({0}) = {{-1,-1,-1,1,3,3}};\n'.format(mvol + 7))
        wfl.write('Block({0}) = {{ 1,-1,-1,1,3,3}};\n'.format(mvol + 8))
        wfl.write('Block({0}) = {{ 0,-1,-1,1,3,3}};\n'.format(mvol + 9))
        wfl.write('\n')
        wfl.write(
            'zol() = BooleanIntersection'
            + '{{Volume{{1:{0}}};}}'.format(hvol)
            + '{{Volume{{{0}}};}};\n'.format(mvol + 1)
        )
        wfl.write(
            'zoh() = BooleanIntersection'
            + '{{Volume{{1:{0}}};}}'.format(hvol)
            + '{{Volume{{{0}}};}};\n'.format(mvol + 2)
        )
        wfl.write(
            'zin() = BooleanIntersection'
            + '{{Volume{{1:{0}}}; Delete;}}'.format(hvol)
            + '{{Volume{{{0}}};}};\n'.format(mvol + 3)
        )
        wfl.write('Translate{0,0, 1}{Volume{zol()};}\n')
        wfl.write('Translate{0,0,-1}{Volume{zoh()};}\n\n')
        wfl.write(
            'yol() = BooleanIntersection'
            + '{Volume{zol(),zoh(),zin()};}'
            + '{{Volume{{{0}}};}};\n'.format(mvol + 4)
        )
        wfl.write(
            'yoh() = BooleanIntersection'
            + '{Volume{zol(),zoh(),zin()};}'
            + '{{Volume{{{0}}};}};\n'.format(mvol + 5)
        )
        wfl.write(
            'yin() = BooleanIntersection'
            + '{Volume{zol(),zoh(),zin()}; Delete;}'
            + '{{Volume{{{0}}};}};\n'.format(mvol + 6)
        )
        wfl.write('Translate{0, 1,0}{Volume{yol()};}\n')
        wfl.write('Translate{0,-1,0}{Volume{yoh()};}\n\n')
        wfl.write(
            'xol() = BooleanIntersection'
            + '{Volume{yol(),yoh(),yin()};}'
            + '{{Volume{{{0}}};}};\n'.format(mvol + 7)
        )
        wfl.write(
            'xoh() = BooleanIntersection'
            + '{Volume{yol(),yoh(),yin()};}'
            + '{{Volume{{{0}}};}};\n'.format(mvol + 8)
        )
        wfl.write(
            'xin() = BooleanIntersection'
            + '{Volume{yol(),yoh(),yin()}; Delete;}'
            + '{{Volume{{{0}}};}};\n'.format(mvol + 9)
        )
        wfl.write('Translate{ 1,0,0}{Volume{xol()};}\n')
        wfl.write('Translate{-1,0,0}{Volume{xoh()};}\n\n')
        wfl.write(
            'zol2() = BooleanIntersection'
            + '{{Volume{{{0}:{1}}};}}'.format(hvol + 1, mvol)
            + '{{Volume{{{0}}}; Delete;}};\n'.format(mvol + 1)
        )
        wfl.write(
            'zoh2() = BooleanIntersection'
            + '{{Volume{{{0}:{1}}};}}'.format(hvol + 1, mvol)
            + '{{Volume{{{0}}}; Delete;}};\n'.format(mvol + 2)
        )
        wfl.write(
            'zin2() = BooleanIntersection'
            + '{{Volume{{{0}:{1}}}; Delete;}}'.format(hvol + 1, mvol)
            + '{{Volume{{{0}}}; Delete;}};\n'.format(mvol + 3)
        )
        wfl.write('Translate{0,0, 1}{Volume{zol2()};}\n')
        wfl.write('Translate{0,0,-1}{Volume{zoh2()};}\n\n')
        wfl.write(
            'yol2() = BooleanIntersection'
            + '{Volume{zol2(),zoh2(),zin2()};}'
            + '{{Volume{{{0}}}; Delete;}};\n'.format(mvol + 4)
        )
        wfl.write(
            'yoh2() = BooleanIntersection'
            + '{Volume{zol2(),zoh2(),zin2()};}'
            + '{{Volume{{{0}}}; Delete;}};\n'.format(mvol + 5)
        )
        wfl.write(
            'yin2() = BooleanIntersection'
            + '{Volume{zol2(),zoh2(),zin2()}; Delete;}'
            + '{{Volume{{{0}}}; Delete;}};\n'.format(mvol + 6)
        )
        wfl.write('Translate{0, 1,0}{Volume{yol2()};}\n')
        wfl.write('Translate{0,-1,0}{Volume{yoh2()};}\n\n')
        wfl.write(
            'xol2() = BooleanIntersection'
            + '{Volume{yol2(),yoh2(),yin2()};}'
            + '{{Volume{{{0}}}; Delete;}};\n'.format(mvol + 7)
        )
        wfl.write(
            'xoh2() = BooleanIntersection'
            + '{Volume{yol2(),yoh2(),yin2()};}'
            + '{{Volume{{{0}}}; Delete;}};\n'.format(mvol + 8)
        )
        wfl.write(
            'xin2() = BooleanIntersection'
            + '{Volume{yol2(),yoh2(),yin2()}; Delete;}'
            + '{{Volume{{{0}}}; Delete;}};\n'.format(mvol + 9)
        )
        wfl.write('Translate{ 1,0,0}{Volume{xol2()};}\n')
        wfl.write('Translate{-1,0,0}{Volume{xoh2()};}\n\n')
        wfl.write('Physical Volume ("walls") = {xol(),xoh(),xin()};\n')
        wfl.write('Physical Volume ("cells") = {xol2(),xoh2(),xin2()};\n\n')
    sp.Popen(['gmsh', wfile, '-0']).wait()
    shutil.move(wfile + '_unrolled', outfile)


def create_walls(edat, wall_thickness=0.01):
    """Creates walls by shring each cell.

    Each vertex is moved by toward the cell centroid as:

    .. math::

        v_n = v_o + w (c - v_o)

    where :math:`v_n` is new vertex position, :math:`v_o` is old vertex
    position, :math:`w` is the ``wall_thickness``, and :math:`c` is the
    centroid position.

    Args:
        edat (dict): extracted geometry data
        wall_thickness (float, optional): shrinking parameter

    Returns:
        list: [cell data, wall data]
    """
    xdat = dict()  # new cell data
    xdat['point'] = dict()
    xdat['line'] = dict()
    xdat['line_loop'] = dict()
    xdat['surface'] = dict()
    xdat['surface_loop'] = dict()
    xdat['volume'] = dict()
    volume_points = dict()  # point IDs for each volume
    for volume in edat['surface_loop']:
        volume_points[volume] = []
        for surface in edat['surface_loop'][volume]:
            for line in edat['line_loop'][surface]:
                for point in edat['line'][line]:
                    if point not in volume_points[volume]:
                        volume_points[volume] += [point]
        volume_points[volume].sort()
    centroids = dict()  # centroid for each volume
    for volume in edat['surface_loop']:
        total = 0
        for point in volume_points[volume]:
            total += edat['point'][point]
        total /= len(volume_points[volume])
        centroids[volume] = total
    npoints = len(edat['point'])
    nlines = len(edat['line'])
    nsurfaces = len(edat['line_loop'])
    nvolumes = len(edat['surface_loop'])
    for volume in list(edat['surface_loop']):
        point_map = dict()  # mapping of old points to new points
        nvolumes += 1
        edat['surface_loop'][nvolumes] = []
        xdat['surface_loop'][nvolumes] = []
        for point in volume_points[volume]:
            npoints += 1
            edat['point'][npoints] = edat['point'][point] + wall_thickness * (
                centroids[volume] - edat['point'][point])
            xdat['point'][npoints] = edat['point'][point] + wall_thickness * (
                centroids[volume] - edat['point'][point])
            point_map[point] = npoints
        for surface in edat['surface_loop'][volume]:
            nsurfaces += 1
            edat['line_loop'][nsurfaces] = []
            xdat['line_loop'][nsurfaces] = []
            for line in edat['line_loop'][surface]:
                nlines += 1
                edat['line'][nlines] = [
                    point_map[edat['line'][line][0]],
                    point_map[edat['line'][line][1]],
                ]
                xdat['line'][nlines] = [
                    point_map[edat['line'][line][0]],
                    point_map[edat['line'][line][1]],
                ]
                edat['line_loop'][nsurfaces] += [nlines]
                xdat['line_loop'][nsurfaces] += [nlines]
            edat['surface'][nsurfaces] = [nsurfaces]
            edat['surface_loop'][nvolumes] += [nsurfaces]
            xdat['surface'][nsurfaces] = [nsurfaces]
            xdat['surface_loop'][nvolumes] += [nsurfaces]
        # edat['volume'][nvolumes] = [nvolumes]
        xdat['volume'][nvolumes] = [nvolumes]
        edat['volume'][volume] += [nvolumes]
    remove_duplicity(edat)
    remove_duplicity(xdat)
    return xdat, edat


def restore_sizing(edat):
    """Add sizing info to all points.

    Adds fourth argument called "psize" to each point.

    Args:
        edat (dict): extracted geometry data
    """
    for ind in edat['point'].keys():
        edat['point'][ind] = list(edat['point'][ind]) + ['psize']


def prep_mesh_config(iname, oname, sizing, char_length=0.1):
    """Create file specifying meshing parameters.

    Sizing specified at points, edges and cells and implemented through
    thresholds.

    Additional info about gmsh mesh sizing `here
    <http://gmsh.info/doc/texinfo/gmsh.html#Specifying-mesh-element-sizes>`_.

    Args:
        iname (str): input filename
        oname (str): output filename
        sizing (list): mesh size near points, edges and in cells
        char_length (float, optional): gmsh Mesh.CharacteristicLengthMax
    """
    eps = 1e-6
    xmin = ymin = zmin = 0
    xmax = ymax = zmax = 1
    base = '{{{0}, {1}, {2}, {3}, {4}, {5}}}'
    with open(oname, "w") as fhl:
        fhl.write('Merge "{}";\n'.format(iname))
        fhl.write('e1() = Line In BoundingBox ' + base.format(
            xmin - eps, ymin - eps, zmin - eps,
            xmax + eps, ymax + eps, zmax + eps) + ';\n')
        fhl.write('Mesh.CharacteristicLengthMax = {0};\n'.format(char_length))
        fhl.write('psize = {0};\n'.format(sizing[0]))
        fhl.write('esize = {0};\n'.format(sizing[1]))
        fhl.write('csize = {0};\n'.format(sizing[2]))
        fhl.write('p1() = Point In BoundingBox ' + base.format(
            xmin - eps, ymin - eps, zmin - eps,
            xmax + eps, ymax + eps, zmax + eps) + ';\n')
        fhl.write('Field[1] = Distance;\n')
        fhl.write('Field[1].NodesList = {p1()};' + '\n')
        fhl.write('Field[2] = Threshold;\n')
        fhl.write('Field[2].IField = 1;\n')
        fhl.write('Field[2].LcMin = psize;\n')
        fhl.write('Field[2].LcMax = csize;\n')
        fhl.write('Field[2].DistMin = 0;\n')
        fhl.write('Field[2].DistMax = 3*csize;\n')
        fhl.write('Field[3] = Distance;\n')
        fhl.write('Field[3].NNodesByEdge = 10;\n')
        fhl.write('Field[3].EdgesList = {e1()};\n')
        fhl.write('Field[4] = Threshold;\n')
        fhl.write('Field[4].IField = 2;\n')
        fhl.write('Field[4].LcMin = esize;\n')
        fhl.write('Field[4].LcMax = csize;\n')
        fhl.write('Field[4].DistMin = 0;\n')
        fhl.write('Field[4].DistMax = 3*csize;\n')
        fhl.write('Field[5] = Min;\n')
        fhl.write('Field[5].FieldsList = {2, 4};' + '\n')
        fhl.write('Background Field = 5;\n')
        fhl.write('Mesh.CharacteristicLengthExtendFromBoundary = 0;\n')


def merge_and_label_geo(inames, oname):
    """Merge geometry files. Define periodic surfaces and physical volume.

    Assumes bounding box [0, 1] in all directions.

    Args:
        inames (list): input filenames
        oname (str): output filename
    """
    eps = 1e-6
    xmin = ymin = zmin = 0
    xmax = ymax = zmax = 1
    base = '{{{0}, {1}, {2}, {3}, {4}, {5}}}'
    base2 = '{{{0}, {1}, {2}}}'
    with open(oname, 'w') as fhl:
        for i, iname in enumerate(inames):
            fhl.write('Merge "{}";\n'.format(iname))
            fhl.write('v{}() = Volume In BoundingBox '.format(i + 1)
                      + base.format(xmin - eps, ymin - eps, zmin - eps,
                                    xmax + eps, ymax + eps, zmax + eps)
                      + ';\n')
            for j in range(i):
                fhl.write('v{0}() -= v{1}();\n'.format(i + 1, j + 1))
            fhl.write('Physical Volume({0}) = {{v{0}()}};\n'.format(i + 1))
        fhl.write('s1() = Surface In BoundingBox ' + base.format(
            xmin - eps, ymin - eps, zmin - eps,
            xmin + eps, ymax + eps, zmax + eps) + ';\n')
        fhl.write('s2() = Surface In BoundingBox ' + base.format(
            xmax - eps, ymin - eps, zmin - eps,
            xmax + eps, ymax + eps, zmax + eps) + ';\n')
        fhl.write('s3() = Surface In BoundingBox ' + base.format(
            xmin - eps, ymin - eps, zmin - eps,
            xmax + eps, ymin + eps, zmax + eps) + ';\n')
        fhl.write('s4() = Surface In BoundingBox ' + base.format(
            xmin - eps, ymax - eps, zmin - eps,
            xmax + eps, ymax + eps, zmax + eps) + ';\n')
        fhl.write('Periodic Surface {s2()} = {s1()} Translate'
                  + base2.format(xmax - xmin, 0, 0) + ';\n')
        fhl.write('Periodic Surface {s4()} = {s3()} Translate'
                  + base2.format(0, ymax - ymin, 0) + ';\n')
