# Export Agua Salud Rainfall Data

Use `export_rainfall.py` to extract rainfall data with metadata from the Agua Salud Rainfall [HDF5](https://www.hdfgroup.org/solutions/hdf5) data archive.

## Data Description

The `AguaSaludRainfall.h5` file contains rainfall data collected as part of the [Panama Canal Watershed Experiment: Agua Salud Project](https://www.jstor.org/stable/wateresoimpa.12.4.0017). The file contains accumulated 15-minute tipping bucket rain gage measurements and 15-minute interpolated rainfall amounts for each experimental watershed.

### Collection

We measured rainfall at 5 locations around the main Agua Salud area and 1 location in Soberania National Park adjacent to a *Saccharum Spontaneum* grassland (see site map below). Each location consisted of a cluster of 2 to 4 tipping-bucket rain gages spaced approximately 2-meters apart. We measured the majority of rainfall data using Davis 0.254-mm tipping bucket rain gages. Field technicians temporarily replaced Davis rain gages with 0.2-mm Onset or 1.0-mm Novalynx rain gages in the event of equipment failure, tampering, or theft.

Panama has a tropical climate with distinct wet and dry seasons. The wet season typically begins in early May and ends by mid-December. Field technicians retrieved data monthly during the wet season, but rarely during the dry season.

### Processing

Field technicians collected raw time-stamped tips from the field. Observations in the field indicated that any particular gage was more likely to underreport rainfall due to clogging by insects. We employed a *maximum storm-event total* method to generate a single rainfall record for each gage-cluster. We summed accumulated tips in bins of 15-minutes to create records of 15-minute rainfall for each gage in a cluster. We split each gage record into a series of discrete storm events assuming 3-hours of rainfall cessation indicated the end of an isolated storm-event. We chose the storm-event with the greatest rainfall total for each set of overlapping storm events at the same gage-cluster.

Gage data can be extracted from the archive by using the dataset command line argument like this: `-d gage_data`.

### Interpolation

Rainfall patterns on the Panamanian Isthmus exhibit a positive gradient Northward. We generated 15-minute interpolated rainfall statistics using Universal Kriging to accomodate regional trend. We found an exponential semivariogram model with a sill of 300 mm, nugget of 0.254 mm, and a range of 7000 m avoided negative values.

We employed random cross-validation to estimate model error for every 15-minute period in which all available gages reported rainfall. We randomly dropped a gage from the network and predicted rainfall at the missing gage by retraining the model using the remaining gages. This method resulted in a root mean squared error of 3.485 mm over 15-minutes at the missing gage.

We incorporated additional rain data from the [Celestino Meterological Station](https://biogeodb.stri.si.edu/physical_monitoring/research/aguasalud) beginning in 2015. The addition of these data reduced root mean squared error to 3.008 mm.

We generated the final set of interpolated rainfall data for every 15-minute period in which at least 3 gages reported rainfall (including zero rainfall). Any period with less than 3 operational gages resulted in no-data (-9.999 by default).

Interpolated data can be extracted from the archive by using the dataset command line argument like this: `-d krig_data`.

### Site Description

![Elevation Map](sites_elevation.png)
![Landcover Map](sites_landcover.png)

## Dependencies

python 3.6+

h5py

### Linux
In a python3 enivronment:  

    python3 -m pip install h5py
    python3 export_rainfall.py [options]

### Windows

Download and install [Anaconda3](https://www.anaconda.com/). Open the `export_rainfall.py` script in Spyder. Select **Run > Configuration per file...** Select the checkmark next to **Command line options:** and enter command line arguments in the text field. Select **Run**.

### CUAHSI JupyterHub

These data are available for download from [HydroShare](http://www.hydroshare.org) with a HydroShare account. To export these data from a web browser using CUAHSI JupyterHub go to the resource landing page located [here](https://www.hydroshare.org/resource/269ca6fb52fd4168adf5adf19cfa610b) after signing into your Hydroshare account. Select **Open with...** on the right side of the landing page. Select **CUAHSI JupyterHub**. Read and accept the terms of use to sign-in with your Hydroshare account. Authorize read and write permissions. Select the **Python 3.7 - Scientific** server and **Start**. Find the drop down on the right labeled **New** and select **Terminal**. Navigate to `~/downloads/269ca6fb52fd4168adf5adf19cfa610b/269ca6fb52fd4168adf5adf19cfa610b/data/contents`. From here you can export data using `python3 export_rainfall.py [options]`.

## Usage

	usage: export_rainfall.py [-h] [-s S] [-d D] [-f [F]] [-ls] [-ld] [-ht]
							[-o O] [-nd ND] [--first FIRST] [--last LAST]

	Export binary Agua Salud data to CSV

	optional arguments:
	-h, --help     show this help message and exit
	-s S           site
	-d D           dataset
	-f [F]         HDF5 input file [default: AguaSaludRainfall.h5]
	-ls            list available sites with engineering codes and exit
	-ld            list datasets for a given site and exit
	-ht            print input file hierarchy in tree format and exit
	-o O           optional output filename
	-nd ND         no data value [default: -9999.9]
	--first FIRST  [YYYY-MM-DDThh:mmZ] datetime of first measurement to
					export
	--last LAST    [YYYY-MM-DDThh:mmZ] datetime of last measurement export

### Example

	python export_rainfall.py --site MOS -d gage_data --first 2010-01-01T01:00Z --last 2010-01-02T01:00Z
	Site: MOS
	Dataset: gage_data
	Start export: 2010-01-01 01:00:00
	End export: 2010-01-02 01:00:00
	Exporting 289 measurements...
	Wrote output data to MOS_gage_data.csv

### Sample Output

	# site: MOS
	# dataset: gage_data
	# gage_latitude: -79.767° [wgs84]
	# gage_longitude: 9.229° [wgs84]
	# no_data_value: -9999.9
	# description: Tipping bucket rain gage precipitation
	# datetime: Instantaneous measurement time - ISO 8601 Standard date-time string YYYY-MM-DD hh:mmZ
	# rainfall: Depth of rainfall over last 15 minutes in millimeters [mm]
	# 
	datetime,rainfall
	2013-02-02 17:00Z,0.0
	2013-02-02 17:15Z,0.0

## Data hierarchy and available date ranges

### Groups

	/site_data/ARN/
	/site_data/COF/
	/site_data/CTD/
	/site_data/CUT/
	/site_data/FOR/
	/site_data/MOS/
	/site_data/NAT/
	/site_data/PAS/
	/site_data/PR2/
	/site_data/RAS/
	/site_data/SAC/
	/site_data/SEC/
	/site_data/TEK/
	/site_data/TKU/

The hierarchical data structure is grouped by site. The top-level site below root is `/site_data/`. Below `/site_data/` are 14 groups, 13 of which correspond to an experimental watershed. Site PR2 (Property 2) is a rainfall gage only site.

### Datasets

Each group contains 1 or 2 datasets. `gage_data` is a 1-dimensional array containing rainfall measurements from a gage cluster local to that site. `krig_data` is a 1-dimensional array of interpolated and spatially aggregated catchment-wide rainfall statistics for a particular experimental watershed.

	$ ./export_rainfall.py -ht
	/site_data/
	├── ARN/
	│   ├── gage_data (2008-06-15T17:00Z to 2018-12-04T15:15Z)
	│   └── krig_data (2008-06-21T11:15Z to 2017-12-16T08:30Z)
	├── COF/
	│   └── krig_data (2008-06-21T11:15Z to 2017-12-16T08:30Z)
	├── CTD/
	│   └── krig_data (2008-06-21T11:15Z to 2017-12-16T08:30Z)
	├── CUT/
	│   └── krig_data (2008-06-21T11:15Z to 2017-12-16T08:30Z)
	├── FOR/
	│   └── krig_data (2008-06-21T11:15Z to 2017-12-16T08:30Z)
	├── MOS/
	│   ├── gage_data (2008-06-15T17:00Z to 2018-12-04T15:15Z)
	│   └── krig_data (2008-06-21T11:15Z to 2017-12-16T08:30Z)
	├── NAT/
	│   └── krig_data (2008-06-21T11:15Z to 2017-12-16T08:30Z)
	├── PAS/
	│   └── krig_data (2008-06-21T11:15Z to 2017-12-16T08:30Z)
	├── PR2/
	│   └── gage_data (2008-06-15T17:00Z to 2018-12-04T15:15Z)
	├── RAS/
	│   ├── gage_data (2008-06-15T17:00Z to 2018-12-04T15:15Z)
	│   └── krig_data (2008-06-21T11:15Z to 2017-12-16T08:30Z)
	├── SAC/
	│   └── gage_data (2008-06-15T17:00Z to 2018-12-04T15:15Z)
	├── SEC/
	│   └── krig_data (2008-06-21T11:15Z to 2017-12-16T08:30Z)
	├── TEK/
	│   ├── gage_data (2008-06-15T17:00Z to 2018-12-04T15:15Z)
	│   └── krig_data (2008-06-21T11:15Z to 2017-12-16T08:30Z)
	└── TKU/
	    └── krig_data (2008-06-21T11:15Z to 2017-12-16T08:30Z)

These datasets contain arrays of compound data types typically consisting of two components: a null-terminated ASCII character string containing an ISO 8601 formatted datetime and a 32-bit float containing a measurement value. Interpolated data includes spatially aggregated statistics for catchment-wide rainfall. Associated attributes are added to output CSV files as commented header lines by default when using `export_rainfall.py`.

### Attributes

Each group and dataset has a number of metadata attributes with full descriptions. The data format, contents, and metadata can be explored using `h5dump`.

	$ h5dump -A -d /site_data/ARN/krig_data AguaSaludRainfall.h5 HDF5 "AguaSaludRainfall.h5" {
	DATASET "/site_data/ARN/krig_data" {
	DATATYPE  H5T_COMPOUND {
		H5T_STRING {
			STRSIZE 18;
			STRPAD H5T_STR_NULLPAD;
			CSET H5T_CSET_ASCII;
			CTYPE H5T_C_S1;
		} "datetime";
		H5T_IEEE_F32LE "minimum";
		H5T_IEEE_F32LE "maximum";
		H5T_IEEE_F32LE "median";
		H5T_IEEE_F32LE "mean";
		H5T_IEEE_F32LE "stdev";
		H5T_IEEE_F32LE "portion";
	}
	DATASPACE  SIMPLE { ( 332630 ) / ( 332630 ) }
	ATTRIBUTE "krig_cells" {
		DATATYPE  H5T_STD_I16LE
		DATASPACE  SCALAR
		DATA {
		(0): 60
		}
	}
	ATTRIBUTE "metadata" {
		DATATYPE  H5T_STRING {
			STRSIZE 700;
			STRPAD H5T_STR_NULLPAD;
			CSET H5T_CSET_ASCII;
			CTYPE H5T_C_S1;
		}
		DATASPACE  SCALAR
		DATA {
		(0): "
			description: Aggregated rainfall statistics derived from kriging
			datetime: Instantaneous measurement time - ISO 8601 Standard date-time string YYYY-MM-DD hh:mmZ
			minimum: Catchment-wide minimum depth of rainfall over last 15 minutes in millimeters [mm]
			maximum: Catchment-wide maximum depth of rainfall over last 15 minutes in millimeters [mm]
			median: Areal median depth of catchment-wide rainfall over last 15 minutes in millimeters [mm]
			mean: Areal mean depth of catchment-wide rainfall over last 15 minutes in millimeters [mm]
			stdev: Standard deviation of around areal mean rainfall over last 15 minutes in millimeters [mm]
			portion: Relative portion of catchment grid cells with non-zero rainfall\000"
		}
	}
	ATTRIBUTE "no_data_value" {
		DATATYPE  H5T_IEEE_F32LE
		DATASPACE  SCALAR
		DATA {
		(0): -9999.9
		}
	}
	}
	}

# "Raw" unprocessed rainfall data

The archive `raw_rain_data.tar.xz` contains data that represent different levels of preprocessing for the gage and interpolated rainfall data found in `AguaSaludRainfall.h5`. Each rainfall collection site consisted of one or more tipping bucket rain gages. The number and brand of individual rain gages varied among sites and may have changed throughout the year. A [Hobo data logger](https://www.onsetcomp.com/) recorded the number of tips at each rain bucket. The `.csv` files found in `01_exported_hobo_files` contain recorded tips exported from `.hobo` files using [Hoboware](https://www.onsetcomp.com/products/software/hoboware). These files use a naming convention like: `ARNR20080617_2009-01-10_DG1.csv`. The first three characters indicate the site code (`ARN`), followed by the launch date (`20080617`), the date the data were downloaded (`2009-01-10`), the type of gage (`D`), and the gage number (`G1`). Gage types include [Davis](https://www.davisinstruments.com/) 0.254 mm (`D`), [Onset](https://www.onsetcomp.com/) 0.2 mm (`O`), and [Novalynx](https://novalynx.com/) 1.0 mm (`N`) tipping bucket rain gages. Gage numbers include `G1`, `G2`, `G3`, and `G4`.

We used `BinRain.py` to inspect and merge individual records of rain gage tips into continuous 15-minute records. `02_binned_and_merged_15min_data` contains these binned data in `.csv` format. We used `BinRain.py` to remove tips from consistently over or under reporting gages. `BinRain.py` regularizes the data by merging together continuous discrete rainfall events from each component gage. In all cases, we preferred the gage that reported the highest storm total rainfall for a particular event.

Field technicians typically collected these data using a field laptop set to UTC time. However, software updates or new equipment sometimes resulted in 5-hour discrepancies due to time zone differences between Panama and UTC or 12 to 24-hour differences due to changing from a base-12 to base-24 hour clock. We used a Time Series Data Editor developed by [Aguaveo LLC](https://www.aquaveo.com/) to visually inspect and correct the 15-minute binned data for time dispcrepancies. `03_time_series_files` contains the `.ts` files before and after time correction. `.ts` files are ASCII text files containing the data in tab-separated format.