# Export Agua Salud Discharge Data

Use `export_discharge.py` to extract discharge data with metadata from the Agua Salud Discharge [HDF5](https://www.hdfgroup.org/solutions/hdf5) data archive.

## Data Description

The `AguaSaludDischarge.h5` file contains volumetric discharge data collected as part of the [Panama Canal Watershed Experiment: Agua Salud Project](https://www.jstor.org/stable/wateresoimpa.12.4.0017). The file contains accumulated 5-minute instantaneous discharge measurements for each experimental watershed.

### Collection

We used two-stage V-notch weirs equipped with pressure transducers to collect 5-minute discharge measurements. Each two-stage weir consisted of a concrete short-crested high-flow weir and a metal sharp-crested low-weir. We used non-vented In-Situ LevelTROLL pressure transducers with integrated data loggers to record instantaneous pressure measurements every 5 minutes. A field technician retrieved pressure measurements monthly and measured depth behind each weir using a staff gage. We collected barometric pressure data using an In-Situ BaroTROLL and removed daily barometric pressure fluctuations from the water pressure records. We used a Time Series Data Editor developed by AquaVeo as part of the Watershed Modeling System to convert pressure measurements to stage using field observed staff gage measurements. We used time series decomposition to remove systematic errors due to ephemeral woody debris clogging the weirs and sensor drift. We used discharge coefficients from [Ogden et al., 2017](https://doi.org/10.1061/(ASCE)HE.1943-5584.0001528) to convert stage measurements to discharge accounting for sedimentation.

### Site Description

![Elevation Map](sites_elevation.png)
![Landcover Map](sites_landcover.png)

## Dependencies

python 3.6+

h5py

### Linux
In a python3 enivronment:  

    python3 -m pip install h5py
    python3 export_discharge.py [options]

### Windows

Download and install [Anaconda3](https://www.anaconda.com/). Open the `export_discharge.py` script in Spyder. Select **Run > Configuration per file...** Select the checkmark next to **Command line options:** and enter command line arguments in the text field. Select **Run**.

### CUAHSI JupyterHub

These data are available for download from [HydroShare](http://www.hydroshare.org) with a HydroShare account. To export these data from a web browser using CUAHSI JupyterHub go to the resource landing page located [here](http://www.hydroshare.org/resource/282177bd87e7426e92899058f075359a) after signing into your Hydroshare account. Select **Open with...** on the right side of the landing page. Select **CUAHSI JupyterHub**. Read and accept the terms of use to sign-in with your Hydroshare account. Authorize read and write permissions. Select the **Python 3.7 - Scientific** server and **Start**. Find the drop down on the right labeled **New** and select **Terminal**. Navigate to `~/downloads/282177bd87e7426e92899058f075359a/282177bd87e7426e92899058f075359a/data/contents`. From here you can export data using `python3 export_discharge.py [options]`.

## Usage

	usage: export_discharge.py [-h] [-s S] [-d D] [-f [F]] [-ls] [-ld] [-ht]
							[-o O] [-nd ND] [--first FIRST] [--last LAST]

	Export binary Agua Salud data to CSV

	optional arguments:
	-h, --help     show this help message and exit
	-s S           site
	-d D           dataset
	-f [F]         HDF5 input file [default: AguaSaludDischarge.h5]
	-ls            list available sites with engineering code and exit
	-ld            list datasets for a given site and exit
	-ht            print input file hierarchy in tree format and exit
	-o O           optional output filename
	-nd ND         no data value [default: -9999.9]
	--first FIRST  [YYYY-MM-DDThh:mmZ] datetime of first measurement to export
	--last LAST    [YYYY-MM-DDThh:mmZ] datetime of last measurement export

### Example

	$ python export_discharge.py --site FOR -d discharge_sharp --first 2010-01-01T01:00Z --last 2010-01-02T01:00Z
	Site: FOR
	Dataset: discharge_sharp
	Start export: 2010-01-01 01:00:00
	End export: 2010-01-02 01:00:00
	Exporting 289 measurements...
	Wrote output data to FOR_discharge_sharp.csv

### Sample output

	# site: FOR
	# dataset: discharge_sharp
	# drainage_area: 144.87 hectares [ha]
	# weir_latitude: 9.20893° [wgs84]
	# weir_longitude: -79.7795° [wgs84]
	# no_data_value: -9999.9
	# engr_code: V02ASL
	# description: Stream discharge over sharp-crested weir
	# datetime: Instantaneous measurement time - ISO 8601 Standard date-time string YYYY-MM-DD hh:mmZ
	# discharge: Stream discharge over weir in cubic meters per second [m^3 s^-1]
	# quality: Numerical flag indicating sharp-crested weir measurement quality
	# -1: No data
	# 0 : Depth is within limits of weir box
	# 2 : Flow deviation greater than 1 liter per second from short-crested weir
	# 3 : Flow depth exceeded weir maximum depth of V-notch
	# 
	# 
	datetime,discharge,quality
	2010-01-01 01:00Z,-9999.9,2

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
	/site_data/RAS/
	/site_data/SAC/
	/site_data/SEC/
	/site_data/TEK/
	/site_data/TKU/

The hierarchical data structure is grouped by site. The top-level site below root is `/site_data/`. Below `/site_data/` are 13 groups corresponding to each experimental watershed.

### Datasets

Each of the site-corresponding groups contains 3 or 6 datasets. `depth_short` is a 1-dimensional array containing depth measurements above the invert of a high-flow short-crested weir. `depth_sharp` is a 1-dimensional array of depth measurments above the invert of a low-flow sharp-crested weir. `discharge_short` is a 1-dimensional array of discharge measurements derived using a weir rating curve and `depth_short` measurements. `discharge_sharp` is a 1-dimensional array of discharge measurements derived from `depth_sharp`. `field_discharge_short` and `field_discharge_sharp` contain field observed measurements of depth with correspondingly derived discharge for both short and sharp-crested weirs.

	$ python3 export_discharge.py -ht
	/site_data/
	├── ARN/
	│   ├── depth_short (2016-04-22T17:30Z to 2018-01-29T15:20Z)
	│   ├── depth_sharp (2016-04-22T17:30Z to 2018-01-29T15:20Z)
	│   ├── discharge_short (2016-04-22T17:30Z to 2018-01-29T15:20Z)
	│   ├── discharge_sharp (2016-04-22T17:30Z to 2018-01-29T15:20Z)
	│   ├── field_discharge_short (2016-04-22T17:00Z to 2018-01-29T15:00Z)
	│   └── field_discharge_sharp (2016-05-12T17:00Z to 2017-08-08T15:00Z)
	├── COF/
	│   ├── depth_short (2014-12-10T18:15Z to 2018-02-19T17:35Z)
	│   ├── discharge_short (2014-12-10T18:15Z to 2018-02-19T17:35Z)
	│   └── field_discharge_short (2014-12-10T18:00Z to 2018-02-19T17:00Z)
	├── CTD/
	│   ├── depth_short (2015-05-29T15:30Z to 2018-04-09T15:10Z)
	│   ├── discharge_short (2015-05-29T15:30Z to 2018-04-09T15:10Z)
	│   └── field_discharge_short (2015-05-29T15:00Z to 2018-04-09T15:00Z)
	├── CUT/
	│   ├── depth_short (2016-04-22T16:00Z to 2018-04-09T15:25Z)
	│   ├── depth_sharp (2016-04-22T16:00Z to 2018-04-09T15:25Z)
	│   ├── discharge_short (2016-04-22T16:00Z to 2018-04-09T15:25Z)
	│   ├── discharge_sharp (2016-04-22T16:00Z to 2018-04-09T15:25Z)
	│   ├── field_discharge_short (2016-04-22T16:00Z to 2018-04-09T15:00Z)
	│   └── field_discharge_sharp (2016-05-24T17:00Z to 2018-04-09T15:00Z)
	├── FOR/
	│   ├── depth_short (2009-03-20T14:45Z to 2018-03-22T16:25Z)
	│   ├── depth_sharp (2009-03-20T14:45Z to 2018-03-22T16:25Z)
	│   ├── discharge_short (2009-03-20T14:45Z to 2018-03-22T16:25Z)
	│   ├── discharge_sharp (2009-03-20T14:45Z to 2018-03-22T16:25Z)
	│   ├── field_discharge_short (2009-03-20T15:00Z to 2018-03-22T16:00Z)
	│   └── field_discharge_sharp (2009-03-20T14:00Z to 2017-03-08T15:00Z)
	├── MOS/
	│   ├── depth_short (2009-03-27T17:55Z to 2018-03-16T15:50Z)
	│   ├── depth_sharp (2009-03-27T17:55Z to 2018-03-16T15:50Z)
	│   ├── discharge_short (2009-03-27T17:55Z to 2018-03-16T15:50Z)
	│   ├── discharge_sharp (2009-03-27T17:55Z to 2018-03-16T15:50Z)
	│   ├── field_discharge_short (2009-03-27T17:00Z to 2018-03-16T15:00Z)
	│   └── field_discharge_sharp (2009-04-02T15:00Z to 2017-06-07T16:00Z)
	├── NAT/
	│   ├── depth_short (2009-03-07T21:30Z to 2018-02-05T17:05Z)
	│   ├── depth_sharp (2009-03-07T21:30Z to 2018-02-05T17:05Z)
	│   ├── discharge_short (2009-03-07T21:30Z to 2018-02-05T17:05Z)
	│   ├── discharge_sharp (2009-03-07T21:30Z to 2018-02-05T17:05Z)
	│   ├── field_discharge_short (2009-03-07T21:00Z to 2018-02-05T17:00Z)
	│   └── field_discharge_sharp (2009-04-21T15:00Z to 2018-02-05T17:00Z)
	├── PAS/
	│   ├── depth_short (2009-03-07T19:00Z to 2018-02-07T15:05Z)
	│   ├── depth_sharp (2009-03-07T19:00Z to 2018-02-07T15:05Z)
	│   ├── discharge_short (2009-03-07T19:00Z to 2018-02-07T15:05Z)
	│   ├── discharge_sharp (2009-03-07T19:00Z to 2018-02-07T15:05Z)
	│   ├── field_discharge_short (2009-03-07T19:00Z to 2018-02-07T15:00Z)
	│   └── field_discharge_sharp (2009-03-07T20:00Z to 2018-02-07T14:00Z)
	├── RAS/
	│   ├── depth_short (2009-03-20T16:50Z to 2018-01-24T17:45Z)
	│   ├── depth_sharp (2009-03-20T16:50Z to 2018-01-24T17:45Z)
	│   ├── discharge_short (2009-03-20T16:50Z to 2018-01-24T17:45Z)
	│   ├── discharge_sharp (2009-03-20T16:50Z to 2018-01-24T17:45Z)
	│   ├── field_discharge_short (2009-03-27T14:00Z to 2018-01-24T17:00Z)
	│   └── field_discharge_sharp (2009-03-20T16:00Z to 2009-03-20T16:00Z)
	├── SAC/
	│   ├── depth_short (2009-06-17T16:55Z to 2018-03-23T16:45Z)
	│   ├── depth_sharp (2009-06-17T16:55Z to 2018-03-23T16:45Z)
	│   ├── discharge_short (2009-06-17T16:55Z to 2018-03-23T16:45Z)
	│   ├── discharge_sharp (2009-06-17T16:55Z to 2018-03-23T16:45Z)
	│   ├── field_discharge_short (2009-06-17T16:00Z to 2018-03-23T16:00Z)
	│   └── field_discharge_sharp (2009-07-28T21:00Z to 2017-07-28T15:00Z)
	├── SEC/
	│   ├── depth_sharp (2009-04-23T18:00Z to 2018-02-05T16:55Z)
	│   ├── discharge_sharp (2009-04-23T18:00Z to 2018-02-05T16:55Z)
	│   └── field_discharge_sharp (2009-04-23T18:00Z to 2018-02-05T16:00Z)
	├── TEK/
	│   ├── depth_short (2009-01-17T21:20Z to 2018-02-08T16:15Z)
	│   ├── depth_sharp (2009-01-17T21:20Z to 2018-02-08T16:15Z)
	│   ├── discharge_short (2009-01-17T21:20Z to 2018-02-08T16:15Z)
	│   ├── discharge_sharp (2009-01-17T21:20Z to 2018-02-08T16:15Z)
	│   ├── field_discharge_short (2009-01-17T21:00Z to 2018-02-08T16:00Z)
	│   └── field_discharge_sharp (2009-04-22T15:00Z to 2017-08-28T17:00Z)
	└── TKU/
	    ├── depth_short (2009-04-07T16:15Z to 2018-02-08T15:05Z)
	    ├── depth_sharp (2009-04-07T16:15Z to 2018-02-08T15:05Z)
	    ├── discharge_short (2009-04-07T16:15Z to 2018-02-08T15:05Z)
	    ├── discharge_sharp (2009-04-07T16:15Z to 2018-02-08T15:05Z)
	    ├── field_discharge_short (2009-04-14T13:00Z to 2018-02-08T15:00Z)
	    └── field_discharge_sharp (2009-04-07T16:00Z to 2017-08-28T18:00Z)

These datasets contain arrays of compound data types typically consisting of three components: a null-terminated ASCII character string containing an ISO 8601 formatted datetime, a 32-bit float containing a measurement value, and a 32-bit integer containing a quality code. Associated attributes are added to output CSV files as commented header lines by default when using `export_discharge.py`.

### Attributes

Each group and dataset has a number of metadata attributes with full descriptions. The data format, contents, and metadata can be explored using `h5dump`.

	$ h5dump -A -d /site_data/ARN/discharge_sharp AguaSaludDischarge.h5
	HDF5 "AguaSaludDischarge.h5" {
	DATASET "/site_data/ARN/discharge_sharp" {
	DATATYPE  H5T_COMPOUND {
		H5T_STRING {
			STRSIZE 18;
			STRPAD H5T_STR_NULLPAD;
			CSET H5T_CSET_ASCII;
			CTYPE H5T_C_S1;
		} "datetime";
		H5T_IEEE_F32LE "discharge";
		H5T_STD_I32LE "quality";
	}
	DATASPACE  SIMPLE { ( 186311 ) / ( 186311 ) }
	ATTRIBUTE "datetime" {
		DATATYPE  H5T_STRING {
			STRSIZE 86;
			STRPAD H5T_STR_NULLPAD;
			CSET H5T_CSET_ASCII;
			CTYPE H5T_C_S1;
		}
		DATASPACE  SCALAR
		DATA {
		(0): "Instantaneous measurement time - ISO 8601 Standard date-time string YYYY-MM-DD hh:mmZ\000"
		}
	}
	ATTRIBUTE "description" {
		DATATYPE  H5T_STRING {
			STRSIZE 41;
			STRPAD H5T_STR_NULLPAD;
			CSET H5T_CSET_ASCII;
			CTYPE H5T_C_S1;
		}
		DATASPACE  SCALAR
		DATA {
		(0): "Stream discharge over sharp-crested weir\000"
		}
	}
	ATTRIBUTE "discharge" {
		DATATYPE  H5T_STRING {
			STRSIZE 65;
			STRPAD H5T_STR_NULLPAD;
			CSET H5T_CSET_ASCII;
			CTYPE H5T_C_S1;
		}
		DATASPACE  SCALAR
		DATA {
		(0): "Stream discharge over weir in cubic meters per second [m^3 s^-1]\000"
		}
	}
	ATTRIBUTE "engr_code" {
		DATATYPE  H5T_STRING {
			STRSIZE 7;
			STRPAD H5T_STR_NULLPAD;
			CSET H5T_CSET_ASCII;
			CTYPE H5T_C_S1;
		}
		DATASPACE  SCALAR
		DATA {
		(0): "V13ASL\000"
		}
	}
	ATTRIBUTE "no_data_value" {
		DATATYPE  H5T_IEEE_F32LE
		DATASPACE  SCALAR
		DATA {
		(0): -9999.9
		}
	}
	ATTRIBUTE "quality" {
		DATATYPE  H5T_STRING {
			STRSIZE 246;
			STRPAD H5T_STR_NULLPAD;
			CSET H5T_CSET_ASCII;
			CTYPE H5T_C_S1;
		}
		DATASPACE  SCALAR
		DATA {
		(0): "Numerical flag indicating sharp-crested weir measurement quality
			-1: No data
			0 : Depth is within limits of weir box
			2 : Flow deviation greater than 1 liter per second from short-crested weir
			3 : Flow depth exceeded weir maximum depth of V-notch
			\000"
		}
	}
	}
	}