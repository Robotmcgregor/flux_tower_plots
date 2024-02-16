#!/usr/bin/env python

"""
MIT License

Copyright (c) 2020 Rob McGregor

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the 'Software'), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.


THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# import modules
from __future__ import print_function, division
import pandas as pd
import glob
import os
import shutil
import warnings

warnings.filterwarnings("ignore")


def concat_list_to_df_fn(list_a):
    """ Define the method used to concatenate the data to a dataframe based on the length of the list.

    @param list_a: list object or a list of list object.
    @return df_concat: pandas dataframe object crated from the input list or list of lists (list_a):
    """
    # print('list_a: ', list_a)
    if len(list_a) <= 1:
        df_concat = pd.DataFrame(list_a[0]).transpose()

    else:
        # df_concat = pd.concat(list_a)
        df_concat = pd.DataFrame.from_records(list_a)

    return df_concat


def glob_dir_fn(zonal_dir):
    """  Search a specified Directory (zonal stats) and concatenate all records to a DataFrame.

    @param zonal_dir: list object containing the path to the fractional cover zonal stats directory.
    @return df_concat: pandas data frame object - all zonal stats csv files concatenated together.
    """

    # create an empty list
    list_df = []

    for file in glob.glob(zonal_dir + '\\*'):
        # read in all zonal stats csv
        df = pd.read_csv(file)
        # append all zonal stats DataFrames to a list.
        list_df.append(df)

    df_concat = pd.concat(list_df)
    df_concat.dropna(axis=0, inplace=True)
    return df_concat


def add_tile_column_fn(df_concat):
    """ Create a tile feature from the image variables.

    @param df_concat: pandas data frame object - all zonal stats csv files concatenated together.
    @return df_concat: processed pandas data frame object with an additional feature - tile.
    """

    image_list = df_concat['image'].tolist()
    tile_list = []
    for i in image_list:
        beginning = i[8:11]
        end = i[12:15]
        tile = beginning + end
        tile_list.append(tile)
        # print(tile)

    df_concat['tile'] = tile_list

    return df_concat


def value_counts_fn(df_concat):
    """ Preform value counts function on the DataFrame and rename the new feature (0) to 'count'.

    @param df_concat: pandas data frame object
    @return df_vc: pandas data frame object created from the series_vc, index has been reset and the value count
    feature has been renamed to 'count'.
    """
    # calculate value counts of features site and tile.
    series_vc = df_concat[['comp_site', 'tile']].value_counts()
    df_vc = pd.DataFrame(series_vc)

    # reset index
    df_vc.reset_index(inplace=True)

    # change column header
    df_vc.rename(columns={0: 'count'}, inplace=True)

    return df_vc


def select_top_row_fn(df_vc, site):
    """ Subset the DataFrame based on site names and select the top observation (highest count value), and concatenated
    to a new DataFrame (output_top_zonal_stats_tiles).

    @param site: sting object containing the site name.
    @param df_vc: pandas data frame object created from the series_vc, index has been reset and the value count
    feature has been renamed to 'count'.
    @return output_top_zonal_stats_tiles: pandas dat frame object housing the complete list of site, tile and count
    information for the tiles which had the most non null zonalStats observations.
    """

    tile = df_vc.loc[df_vc['comp_site'] == site, 'tile'].iloc[0]

    return site, tile


def sort_plots_fn(export_dir, final_plot_outputs, final_interactive_outputs, comp_site, tile):
    """ Using the outputTopZonalStatsTiles dataframe, copy all plots (bare ground, all bands and interactive) to new
    folders titled finalPlot and finalInteractive.

    @param tile: string object containing the Landsat tile.
    @param comp_site: string object containing the site name including property and prop tag information.
    @param export_dir: string object containing the export directory path for all outputs (command argument).
    @param final_plot_outputs: string object containing the sorted plots to be exported within the export directory.
    @param final_interactive_outputs: string object containing the sorted plots to be exported within the export
    directory.
    """

    for bare_plot in glob.glob(export_dir + '\\plots\\BG_plot_' + str(comp_site) + '_' + str(tile) + '*.png'):

        shutil.copy(bare_plot, final_plot_outputs)

    for inter_plot in glob.glob(export_dir + '\\plots\\All_B_interp_' + str(comp_site) + '_' + str(tile) + '*.png'):

        shutil.copy(inter_plot, final_plot_outputs)

    for interactive_plot in glob.glob(
            export_dir + '\\plots\\interactive\\*' + str(comp_site) + '_' + str(tile) + '_interactive.html'):

        shutil.copy(interactive_plot, final_interactive_outputs)


def main_routine(export_dir, zonal_dir):
    """ This script determines which Landsat tile had the most non null zonal statistics records per site and files
    those plots (bare ground, all bands and interactive) into final output folders.

    @param zonal_dir: string object containing the directory path to the processed zonal stats csv files.
    @param export_dir: string object containing the export directory path for all outputs.
    """

    # output folder paths
    final_plot_outputs = export_dir + '\\final_plots'

    final_interactive_outputs = export_dir + '\\final_interactive'

    # call the glob dir function to concatenate all csv files.
    df_concat = glob_dir_fn(zonal_dir)

    df_concat = add_tile_column_fn(df_concat)

    # Call the value_counts function
    df_vc = value_counts_fn(df_concat)
    # Create a list of unique site names
    unique_site = df_vc.comp_site.unique().tolist()

    # loop through the list of unique sites
    for site in unique_site:
        # Call the select_top_row_fn function to subset the dataframe based on site names and select the top observation
        # (highest count value).
        comp_site, tile = select_top_row_fn(df_vc, site)

        # call the sort_plots_fn function to copy plots (bare ground, all bands and interactive) with the highest number
        # of fc zonal stat hits to new sub-directories.
        sort_plots_fn(export_dir, final_plot_outputs, final_interactive_outputs, comp_site, tile)


if __name__ == "__main__":
    main_routine()
