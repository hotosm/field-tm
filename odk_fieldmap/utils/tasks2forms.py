#!/bin/python3

import os
import sys

from openpyxl import load_workbook


def task_areas_to_forms(indir, form_template):
    """
    Accepts a project directory, with a subdirectory
    called /geojson full of GeoJSON point files,
    each representing an individual task (e.g. a batch
    of buildings or amenities to be visited for data 
    collection) and returns a set of xlsforms, one for
    each task, with the appropriate references in 
    place for the Select from Map question in ODK.
    """
    geojsondir = os.path.join(indir, "geojson")
    print(geojsondir)
    if not os.path.exists(geojsondir):
        print("Can't find geojson subdirectory")
        # Maybe throw an exception
    filelist = os.listdir(geojsondir)
    # keep only the files that are GeoJSON
    # TODO: Maybe reject all non-point input files;
    # kind of a hassle involving a spatial lib
    # but perhaps worth it
    aois = [x for x in filelist if os.path.splitext(
        x)[1].lower() == ".geojson"]
    outdir = os.path.join(indir, "forms")
    if not os.path.exists(outdir):
        print(f"Making directory {outdir}")
        os.makedirs(outdir)
    for aoi in aois:
        prep_form(form_template, aoi, outdir)


def prep_form(form_template, AOIfile, outdir):
    """
    Creates a modified copy of an ODK xlsform to refer
    to a specific area and GeoJSON file of features.
    Only works with OSM_Buildings_ODK_v_0-1-0.xlsx
    """
    form_basename = os.path.splitext(os.path.basename(form_template))[0]
    print(form_basename)
    (AOIpath, AOIext) = os.path.splitext(AOIfile)
    AOIbasename = os.path.splitext(os.path.basename(AOIfile))[0]
    wb = load_workbook(filename=form_template)
    surveyws = wb["survey"]
    settingws = wb["settings"]

    settingws["A2"] = f"{AOIbasename}"
    settingws["B2"] = f"{AOIbasename}"
    surveyws["A9"] = f"select_one_from_file " f"{AOIbasename}{AOIext}"
    outfile = os.path.join(outdir, f"{AOIbasename}.xlsx")
    print(f"Writing: {outfile}")
    wb.save(outfile)


if __name__ == "__main__":
    """
    If run from CLI, takes two positional arguments
    1) An input directory full of individual GeoJSON
       files representing tasks
    2) A ODK-compatible xlsform template
    It then creates a subdirectory called 'forms'
    and populates it with xlsforms specifically 
    referencing the individual GeoJSON files.
    """
    indir = sys.argv[1]
    formfile = sys.argv[2]
    print("here goes")
    task_areas_to_forms(indir, formfile)
