#!/usr/bin/env python

"""
MIT License

Copyright (c) 2020 Rob McGregor, script modified from zzzz Grant Staben 2019

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
import pandas as pd
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure, output_file, save
from bokeh.layouts import column
from bokeh.plotting import figure
import geopandas as gpd
import warnings

warnings.filterwarnings("ignore")


def string_clean_upper_fn(dirty_string):
    """ Remove whitespaces and clean strings.

    @param dirty_string: string object that may have whitespaces, - or _.
    @return clean_string: processed string object.
    """

    str1 = dirty_string.replace('_', ' ')
    str2 = str1.replace('-', ' ')
    str3 = str2.upper()
    clean_string = str3.strip()
    return clean_string


def prop_name_extraction_fn(estate_series, site_code):
    """ Extract the property name from the geopandas series.

    @param estate_series: geopandas series object containing properties and properties code variables.
    @param site_code: string object containing the properties three letter code - read into the function.
    @return prop_label: string object containing the property name and code.
    """

    property_code_list = estate_series.PROP_TAG.tolist()
    prop_code_upper = string_clean_upper_fn(str(site_code))

    if prop_code_upper in property_code_list:
        prop_name = estate_series.loc[estate_series['PROP_TAG'] == prop_code_upper, 'PROPERTY'].item() #loc[0]

    else:
        prop_name = prop_code_upper

    properties = string_clean_upper_fn(str(prop_name))
    prop_label = properties + "_" + prop_code_upper

    return prop_label


def main_routine(export_dir, output_zonal_stats, complete_tile, plot_outputs, rolling_mean):
    """ Produce interactive time series plot from the Bokeh module from fractional cover zonal stats information.

    :param plot_outputs:
    :param pastoral_estate: string object containing the path to the pastoral estate shapefile.
    :param export_dir: string object containing the plot directory path.
    :param rolling_mean: integer object controlling the rolling mean.
    :param output_zonal_stats: pandas data frame object containing all fractional cover zonal stats records
    identified in the zonal_stats directory.
    :param complete_tile: string object containing the landsat tile name.
    :return output_file: interactive html file with three plots per site.
    """

    interactive_outputs = plot_outputs + '\\interactive'




    # # read in the estate shapefile and create series
    # estate = gpd.read_file(pastoral_estate)
    # estate_series = estate[['PROPERTY', 'PROP_TAG']]

    # subset DataFrame - drop all values less than 3 to reduce noise
    output_zonal_stats = output_zonal_stats[(output_zonal_stats['b1_count'] > 3)]

    # subset DataFrame - drop all values less than 1987
    output_zonal_stats = output_zonal_stats.loc[
        (output_zonal_stats['year'] >= 1987)]
    # output_zonal_stats.to_csv(export_dir_path + '\\outputZonal_greater1987.csv')

    for i in output_zonal_stats.site.unique():

        print(i)

        #name_ = i.replace('_', ' ')

        # convert all site names variables to a string.
        output_zonal_stats['dateTime'] = pd.to_datetime(output_zonal_stats[['year', 'month', 'day']])

        #site_code = str(i[:3])
        # select out only the landsat derived fractional cover values.
        #prop_label = prop_name_extraction_fn(estate_series, site_code)

        # subset DataFrame by the unique identifier 'site'.
        site_df = output_zonal_stats.loc[(output_zonal_stats.site == i)]

        date_sort_df = site_df.sort_values(['dateTime'])

        # format the image date for the hover tool
        date_sort_df['DateTime'] = date_sort_df['dateTime'].dt.strftime('%Y/%m/%d')

        # date_sort_df['DateTime'] = date_sort_df['site_date'].dt.strftime('%Y/%m/%d')

        # -----------------------------------------------Bare ground - band 1 ------------------------------------------

        # use all predicted fractional cover values to produce the fitted line
        sort_site_df = output_zonal_stats.loc[(output_zonal_stats.site == i)]
        sort_site_df.to_csv(export_dir + '\\sort_site_df_' + str(i) + '.csv')
        date_f = sort_site_df.sort_values(['dateTime'])

        date_fit = date_f['dateTime']

        mean_bg_fit = date_f['b1_mean']

        # create the rolling mean of the feature date_f from the bg_mean_f series - parameters:(5,center=True)
        mean_bg_rolling = mean_bg_fit.rolling(rolling_mean, center=True).mean()

        # set up the hover tool
        source2 = ColumnDataSource(date_sort_df)

        TOOLS = "pan,wheel_zoom,box_zoom,reset,save,".split(',')
        hover = HoverTool(tooltips=[('image date', '@DateTime'), ('Bare fraction', '@b1_mean{int}%')], names=["lsat"])
        TOOLS.append(hover)

        # set up the plots parameters
        s1 = figure(title='Fractional Cover Time Trace - Bare ground: ' + str(i) + '.',
                    x_axis_label='time',
                    y_axis_label='Bare Ground fraction %', x_axis_type='datetime', y_range=(0, 105),
                    plot_width=900, plot_height=250, tools=TOOLS)
        # plot the time series data
        s1.line(date_fit, mean_bg_rolling, color='red', line_width=3)
        s1.circle("dateTime", "b1_mean", source=source2, name="lsat", size=5, color='red', alpha=0.6, line_alpha=0.6,
                  line_color='black')

        # ----------------------------------- Photosynthetic vegetation band 2 -----------------------------------------

        output_zonal_stats = output_zonal_stats.loc[(output_zonal_stats['b2_count'] > 3)]
        output_zonal_stats.sort_values(['dateTime'])
        output_zonal_stats = output_zonal_stats.loc[(output_zonal_stats['year'] >= 1987)]

        pv_mean_f = date_f['b2_mean']
        pv_mean_fpd4 = pv_mean_f.rolling(rolling_mean, center=True).mean()

        # set up the hover tool
        source2 = ColumnDataSource(date_sort_df)

        TOOLS = "pan,wheel_zoom,box_zoom,reset,save,".split(',')

        hover = HoverTool(tooltips=[('image date', '@DateTime'), ('pv fraction', '@b2_mean{int}%')], names=["lsat"])

        TOOLS.append(hover)

        # set up the plots parameters
        s2 = figure(
            title='Fractional Cover Time Trace - Photosynthetic vegetation: ' + str(i) + '.',
            x_axis_label='time',
            y_axis_label='PV fraction %', x_axis_type='datetime', y_range=(0, 105),
            plot_width=900, plot_height=250, tools=TOOLS)
        # plot the time series data
        s2.line(date_fit, pv_mean_fpd4, color='green', line_width=3)
        s2.circle("dateTime", "b2_mean", source=source2, name="lsat", size=5, color='green', alpha=0.6, line_alpha=0.6,
                  line_color='black')

        # ------------------------------- Non - photosynthetic vegetation band 3 ---------------------------------------

        output_zonal_stats = output_zonal_stats[(output_zonal_stats['b3_count'] > 3)]
        output_zonal_stats.sort_values(['dateTime'])
        output_zonal_stats = output_zonal_stats[(output_zonal_stats['year'] >= 1987)]

        npv_mean_f = date_f['b3_mean']
        npv_mean_fpd4 = npv_mean_f.rolling(rolling_mean, center=True).mean()

        # set up the hover tool
        source2 = ColumnDataSource(date_sort_df)

        TOOLS = "pan,wheel_zoom,box_zoom,reset,save,".split(',')

        hover = HoverTool(tooltips=[('image date', '@DateTime'), ('npv fraction', '@b3_mean{int}%')], names=["lsat"])

        TOOLS.append(hover)

        # set up the plots parameters
        s3 = figure(
            title='Fractional Cover Time Trace - Non-photosynthetic vegetation: ' + str(i) + ' site (%s)' % str(i),
            x_axis_label='time',
            y_axis_label='NPV fraction %', x_axis_type='datetime', y_range=(0, 105),
            plot_width=900, plot_height=250, tools=TOOLS)
        # plot the time series data
        s3.line(date_fit, npv_mean_fpd4, color='blue', line_width=3)
        s3.circle("dateTime", "b3_mean", source=source2, name="lsat", size=5, color='blue', alpha=0.6, line_alpha=0.6,
                  line_color='black')

        output_file(interactive_outputs + '\\' + str(i) + '_' + str(complete_tile) + '_interactive.html')

        save(column(s1, s2, s3))


if __name__ == "__main__":
    main_routine()