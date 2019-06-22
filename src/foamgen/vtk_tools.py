"""
VTK support module
==================
:synopsis: Geometry and mesh manipulation using VTK.

.. moduleauthor:: Pavel Ferkl <pavel.ferkl@gmail.com>
"""
from pathlib import Path
import vtk


def vtk_bin_to_ascii(fin, fout, origin, spacing):
    """Convert VTK file to ascii format.

    Intended for VTK files with 3D voxel data. Also adjusts origin and spacing.

    Args:
        fin (str): input filename
        fout (str): output filename
        origin (list): origin of coordinate system
        spacing (list): distance between the nodes in structured mesh
    """
    reader = vtk.vtkDataSetReader()
    reader.SetFileName(fin)
    reader.Update()
    data = vtk.vtkImageData()
    data.ShallowCopy(reader.GetOutput())
    data.SetOrigin(origin)
    data.SetSpacing(spacing)
    writer = vtk.vtkStructuredPointsWriter()
    if vtk.VTK_MAJOR_VERSION <= 5:
        writer.SetInputConnection(data.GetProducerPort())
    else:
        writer.SetInputData(data)
    writer.SetFileName(fout)
    writer.Write()


def stl_to_periodic_box(fin, fout, mins, sizes, render):
    """Move periodic STL into periodic box.

    Uses VTK to create foam in box with periodic boundary conditions.
    Divides the foam to 27 parts and reflects them over boundaries.

    Args:
        fin (str): filename of foam with all closed cells
        fout (str): filename of foam fully inside the box
        mins (list): origin coordinates
        sizes (list): box sizes
        render (bool): render scene if True
    """
    print("Moving STL to periodic box.")
    xmin, ymin, zmin = mins
    dx, dy, dz = sizes
    # print vtk.VTK_MAJOR_VERSION # Check the version
    # Read the file and create polydata
    reader = vtk.vtkSTLReader()
    reader.SetFileName(fin)
    # Define planes for clipping
    origins = [
        [xmin, ymin, zmin],
        [xmin, ymin, zmin],
        [xmin, ymin, zmin],
        [xmin+dx, ymin+dy, zmin+dz],
        [xmin+dx, ymin+dy, zmin+dz],
        [xmin+dx, ymin+dy, zmin+dz],
    ]
    normals = [
        [[-1, 0, 0], [0, -1, 0], [0, 0, -1], [-1, 0, 0], [0, -1, 0], [0, 0, -1]],
        [[+1, 0, 0], [0, -1, 0], [0, 0, -1], [-1, 0, 0], [0, -1, 0], [0, 0, -1]],
        [[+1, 0, 0], [0, -1, 0], [0, 0, -1], [+1, 0, 0], [0, -1, 0], [0, 0, -1]],
        [[-1, 0, 0], [0, +1, 0], [0, 0, -1], [-1, 0, 0], [0, -1, 0], [0, 0, -1]],
        [[+1, 0, 0], [0, +1, 0], [0, 0, -1], [-1, 0, 0], [0, -1, 0], [0, 0, -1]],
        [[+1, 0, 0], [0, +1, 0], [0, 0, -1], [+1, 0, 0], [0, -1, 0], [0, 0, -1]],
        [[-1, 0, 0], [0, +1, 0], [0, 0, -1], [-1, 0, 0], [0, +1, 0], [0, 0, -1]],
        [[+1, 0, 0], [0, +1, 0], [0, 0, -1], [-1, 0, 0], [0, +1, 0], [0, 0, -1]],
        [[+1, 0, 0], [0, +1, 0], [0, 0, -1], [+1, 0, 0], [0, +1, 0], [0, 0, -1]],

        [[-1, 0, 0], [0, -1, 0], [0, 0, +1], [-1, 0, 0], [0, -1, 0], [0, 0, -1]],
        [[+1, 0, 0], [0, -1, 0], [0, 0, +1], [-1, 0, 0], [0, -1, 0], [0, 0, -1]],
        [[+1, 0, 0], [0, -1, 0], [0, 0, +1], [+1, 0, 0], [0, -1, 0], [0, 0, -1]],
        [[-1, 0, 0], [0, +1, 0], [0, 0, +1], [-1, 0, 0], [0, -1, 0], [0, 0, -1]],
        [[+1, 0, 0], [0, +1, 0], [0, 0, +1], [-1, 0, 0], [0, -1, 0], [0, 0, -1]],
        [[+1, 0, 0], [0, +1, 0], [0, 0, +1], [+1, 0, 0], [0, -1, 0], [0, 0, -1]],
        [[-1, 0, 0], [0, +1, 0], [0, 0, +1], [-1, 0, 0], [0, +1, 0], [0, 0, -1]],
        [[+1, 0, 0], [0, +1, 0], [0, 0, +1], [-1, 0, 0], [0, +1, 0], [0, 0, -1]],
        [[+1, 0, 0], [0, +1, 0], [0, 0, +1], [+1, 0, 0], [0, +1, 0], [0, 0, -1]],

        [[-1, 0, 0], [0, -1, 0], [0, 0, +1], [-1, 0, 0], [0, -1, 0], [0, 0, +1]],
        [[+1, 0, 0], [0, -1, 0], [0, 0, +1], [-1, 0, 0], [0, -1, 0], [0, 0, +1]],
        [[+1, 0, 0], [0, -1, 0], [0, 0, +1], [+1, 0, 0], [0, -1, 0], [0, 0, +1]],
        [[-1, 0, 0], [0, +1, 0], [0, 0, +1], [-1, 0, 0], [0, -1, 0], [0, 0, +1]],
        [[+1, 0, 0], [0, +1, 0], [0, 0, +1], [-1, 0, 0], [0, -1, 0], [0, 0, +1]],
        [[+1, 0, 0], [0, +1, 0], [0, 0, +1], [+1, 0, 0], [0, -1, 0], [0, 0, +1]],
        [[-1, 0, 0], [0, +1, 0], [0, 0, +1], [-1, 0, 0], [0, +1, 0], [0, 0, +1]],
        [[+1, 0, 0], [0, +1, 0], [0, 0, +1], [-1, 0, 0], [0, +1, 0], [0, 0, +1]],
        [[+1, 0, 0], [0, +1, 0], [0, 0, +1], [+1, 0, 0], [0, +1, 0], [0, 0, +1]],
    ]
    # Define directions for moving clipped regions
    direction = [
        [dx, dy, dz],
        [0, dy, dz],
        [-dx, dy, dz],
        [dx, 0, dz],
        [0, 0, dz],
        [-dx, 0, dz],
        [dx, -dy, dz],
        [0, -dy, dz],
        [-dx, -dy, dz],
        [dx, dy, 0],
        [0, dy, 0],
        [-dx, dy, 0],
        [dx, 0, 0],
        [0, 0, 0],
        [-dx, 0, 0],
        [dx, -dy, 0],
        [0, -dy, 0],
        [-dx, -dy, 0],
        [dx, dy, -dz],
        [0, dy, -dz],
        [-dx, dy, -dz],
        [dx, 0, -dz],
        [0, 0, -dz],
        [-dx, 0, -dz],
        [dx, -dy, -dz],
        [0, -dy, -dz],
        [-dx, -dy, -dz],
    ]
    regions = []
    n = 27
    for j in range(n):
        polydata = reader
        # Clip it with all 6 planes
        for i in range(6):
            plane = vtk.vtkPlane()
            plane.SetOrigin(origins[i])
            plane.SetNormal(normals[j][i])
            clipper = vtk.vtkClipPolyData()
            clipper.SetInputConnection(polydata.GetOutputPort())
            clipper.SetClipFunction(plane)
            polydata = clipper
            polydata.Update()
        # Move it if not empty
        if polydata.GetOutput().GetLength() > 0:
            transform = vtk.vtkTransform()
            transform.Translate(direction[j])
            transformFilter = vtk.vtkTransformPolyDataFilter()
            transformFilter.SetTransform(transform)
            transformFilter.SetInputConnection(polydata.GetOutputPort())
            transformFilter.Update()
            regions.append(vtk.vtkPolyData())
            regions[j].ShallowCopy(transformFilter.GetOutput())
        else:
            regions.append(vtk.vtkPolyData())
            regions[j].ShallowCopy(polydata.GetOutput())
    # Append the all regions
    append_filter = vtk.vtkAppendPolyData()
    if vtk.VTK_MAJOR_VERSION <= 5:
        for j in range(n):
            append_filter.AddInputConnection(regions[j].GetProducerPort())
    else:
        for j in range(n):
            append_filter.AddInputData(regions[j])
    append_filter.Update()
    #  Remove any duplicate points
    clean_filter = vtk.vtkCleanPolyData()
    clean_filter.SetInputConnection(append_filter.GetOutputPort())
    clean_filter.Update()
    # One more rotation - not needed
    # transform = vtk.vtkTransform()
    # transform.Translate(-6,-6,-6)
    # transformFilter = vtk.vtkTransformPolyDataFilter()
    # transformFilter.SetTransform(transform)
    # transformFilter.SetInputConnection(clean_filter.GetOutputPort())
    # transformFilter.Update()
    # transform = vtk.vtkTransform()
    # transform.RotateWXYZ(90,1,0,0)
    # transform.RotateWXYZ(-90,0,1,0)
    # transformFilter2 = vtk.vtkTransformPolyDataFilter()
    # transformFilter2.SetTransform(transform)
    # transformFilter2.SetInputConnection(transformFilter.GetOutputPort())
    # transformFilter2.Update()
    # transform = vtk.vtkTransform()
    # transform.Translate(6,6,6)
    # transformFilter = vtk.vtkTransformPolyDataFilter()
    # transformFilter.SetTransform(transform)
    # transformFilter.SetInputConnection(transformFilter2.GetOutputPort())
    # transformFilter.Update()
    # Final data to be saved and displayed
    final_data = clean_filter
    # Write the file to disk
    ext = Path(fout).suffix[1:]
    if ext.lower() == 'stl':
        writer = vtk.vtkSTLWriter()
    elif ext.lower() == 'ply':
        writer = vtk.vtkPLYWriter()
    else:
        print(ext)
        raise Exception('Can write only stl or ply file.')
    writer.SetFileName(fout)
    writer.SetInputConnection(final_data.GetOutputPort())
    writer.Write()
    if render:
        # Create mappper and actor for rendering
        mapper = vtk.vtkPolyDataMapper()
        if vtk.VTK_MAJOR_VERSION <= 5:
            mapper.SetInput(final_data.GetOutput())
        else:
            mapper.SetInputConnection(final_data.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        # Create a rendering window and renderer
        ren = vtk.vtkRenderer()
        ren_win = vtk.vtkRenderWindow()
        ren_win.AddRenderer(ren)
        # Create a renderwindowinteractor
        iren = vtk.vtkRenderWindowInteractor()
        iren.SetRenderWindow(ren_win)
        # Assign actor to the renderer
        ren.AddActor(actor)
        # Enable user interface interactor
        iren.Initialize()
        ren_win.Render()
        iren.Start()
