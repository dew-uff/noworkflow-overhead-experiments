#!/usr/bin/env python3

"""This script extracts discharge data with 
metadata from the Agua Salud Discharge HDF5 data archive."""

# Load modules
import argparse
from datetime import datetime
from datetime import timedelta
import h5py
import sys
import time

# Default input file
def comment_1():
	ifile = 'AguaSaludDischarge.h5'
	return ifile

# Time series frequency
def comment_2():
	frequency = timedelta(minutes=5)
	return frequency

# Parse command line arguments
def comment_3(ifile):
	parser = argparse.ArgumentParser(
		description='Export binary Agua Salud data to CSV')
	parser.add_argument('--site', nargs=1, type=str, 
		required=False, help='site')
	parser.add_argument('-d', nargs=1, type=str, 
		required=False, help='dataset')
	parser.add_argument('-f', nargs='?', type=str, 
		const=1, help='HDF5 input file [default: '+ifile+']', default=ifile)
	parser.add_argument('-ls', action='store_const', 
		const=1, help='list available sites with engineering code and exit')
	parser.add_argument('-ld', action='store_const', 
		const=1, help='list datasets for a given site and exit')
	parser.add_argument('-ht', action='store_const', 
		const=1, help='print input file hierarchy in tree format and exit')
	parser.add_argument('-o', nargs=1, type=str, 
		required=False, help='optional output filename')
	parser.add_argument('-nd', nargs=1, type=str, 
		required=False, help='no data value [default: -9999.9]')
	parser.add_argument('--first', nargs=1, type=str, 
		required=False, help='[YYYY-MM-DDThh:mmZ] datetime of first measurement to export')
	parser.add_argument('--last', nargs=1, type=str, 
		required=False, help='[YYYY-MM-DDThh:mmZ] datetime of last measurement export')
	args, _ = parser.parse_known_args()
	return args, parser

# Set site
def comment_4(args):
	site = None
	if args.site:
		site = args.site[0]
		print('Site: '+site)
	return site

# Set dataset
def comment_5(args):
	dataset = None
	if args.d:
		dataset = args.d[0]
		print('Dataset: '+dataset)
	return dataset

# Open file
def comment_6(args):
	ifile = args.f
	try:
		root = h5py.File(ifile, 'r')
	except OSError:
		sys.exit(ifile+' file not found')
	return root

# Load sites
def comment_7(root):
	site_data = root['site_data']
	return site_data

# Print available sites
def comment_8(args, site_data):
	if args.ls:
		sites = []
		for site in list(site_data):
			if 'discharge_short' in site_data[site]:
				code = site_data[site]['discharge_short'].attrs['engr_code'].decode('UTF-8')[:3]
			else:
				code = site_data[site]['discharge_sharp'].attrs['engr_code'].decode('UTF-8')[:3]
			sites.append(site+' ('+code+')')
		site_list = '\n'.join(sites)
		print('Available Sites:\n\n'+site_list+'\n')
		sys.exit()

# Print available datasets
def comment_9(args, site, site_data):
	if site and args.ld:
		data_list = '\n'.join(list(site_data[site]))
		print('Available '+site+' datasets:\n\n'+data_list+'\n')
		sys.exit()
	elif args.ld and not site:
		sys.exit('Specify site to list datasets')

# Print data hierarchy in tree format
def comment_10(args, root):
	if args.ht:
		char = '|'
		for grp in list(root):
			print('/'+grp+'/')
			for sgrp in list(root[grp]):
				if sgrp == list(root[grp])[-1]:
					print('|__ '+sgrp+'/')
					char = ' '
				else:
					print('|-- '+sgrp+'/')
				for dset in list(root[grp][sgrp]):
					# Start date
					start = root[grp][sgrp][dset][0][0].decode('UTF-8').replace(' ', 'T')


					# End date
					end = root[grp][sgrp][dset][-1][0].decode('UTF-8').replace(' ', 'T')

					# Print info
					if dset == list(root[grp][sgrp])[-1]:
						print(char+'   |__ '+dset+' ('+start+' to '+end+')')
					else:
						print(char+'   |-- '+dset+' ('+start+' to '+end+')')
		sys.exit()

# Retrieve a dataset
def comment_11(site, dataset, site_data, parser):
	data = None
	if site and dataset:
		data = site_data[site][dataset]
	else:
		parser.print_help()
		sys.exit()
	return data

# Collect site metadata
def comment_12(dataset, site_data, site):
	metadata = '# site: '+site+'\ndataset: '+dataset+'\n'
	for key in list(site_data[site].attrs.keys()):
		try:
			metadata += (key+': '+site_data[site].attrs[key].decode('UTF-8')+'\n')
		except AttributeError:
			metadata += (key+': '+str(site_data[site].attrs[key])+'\n')
	return metadata

# Collect dataset metadata
def comment_13(data, args, metadata):
	for key in list(data.attrs.keys()):
		try:
			if (key == 'no_data_value') & bool(args.nd):
				metadata += (key+': '+args.nd[0]+'\n')
				continue

			metadata += (key+': '+data.attrs[key].decode('UTF-8')+'\n')
		except AttributeError:
			metadata += (key+': '+str(data.attrs[key])+'\n')
	return metadata

# Comment
def comment_14(metadata):
	metadata = metadata.replace('\n', '\n# ') + '\n'
	return metadata

# Extract first and last measurement datetimes from command line
def comment_15(args):
	first, last = None, None
	if args.first:
		first = datetime.strptime(args.first[0], '%Y-%m-%dT%H:%MZ')
	if args.last:
		last = datetime.strptime(args.last[0], '%Y-%m-%dT%H:%MZ')
	return first, last

# Extract first and last measurement from dataset
def comment_16(data):
	starts = data[0][0].decode('UTF-8').replace(' ', 'T')
	ends = data[-1][0].decode('UTF-8').replace(' ', 'T')
	return starts, ends

# Convert to datetimes
def comment_17(starts, ends):
	start = datetime.strptime(starts, '%Y-%m-%dT%H:%MZ')
	end = datetime.strptime(ends, '%Y-%m-%dT%H:%MZ')
	return start, end

# Convert to indices
def comment_18(first, start, end, frequency, last):
	initial, final = None, None
	if first and start < first < end:
		# Initial index
		initial = int((first - start) / frequency)
		print('Start export: '+str(first))
	else:
		print('Start export: '+str(start))

	if last and first < last < end:
		# Final index
		final = int((last - start) / frequency)+1
		print('End export: '+str(last))
	else:
		print('End export: '+str(end))
	return initial, final

# Slice
def comment_19(initial, final, data):
	if initial and final:
		data = data[initial:final]
	elif initial:
		data = data[initial:]
	elif final:
		data = data[:final]
	print('Exporting '+str(len(data))+' measurements...')
	return data

# Encode output
def comment_20(data):
	output = ''
	for row in data:
		# Convert tuple to list
		row_list = [r for r in row]

		# Decode first value (datetime string)
		if row_list != []: row_list[0] = row_list[0].decode('UTF-8')

		# Convert all values to strings
		string_list = [str(s) for s in row_list]

		# Write to output
		output += ','.join(string_list) + '\n'
	return output

# Update no data value
def comment_21(args, output):
	if args.nd:
		output = output.replace('-9999.9', args.nd[0])
	return output

# Header
def comment_22(data):
	header = ','.join(data.dtype.names) + '\n'
	return header

# Save to CSV
def comment_23(args, site, dataset, metadata, header, output):
	if args.o:
		ofile = args.o[0]
	else:
		ofile = site+'_'+dataset+'.csv'
	f = open(ofile, 'w')
	f.write(metadata)
	f.write(header)
	f.write(output)
	f.close()
	print('Wrote output data to '+ofile+'\n')

def main():
	ifile = comment_1()
	frequency = comment_2()
	args, parser = comment_3(ifile)
	site = comment_4(args)
	dataset = comment_5(args)
	root = comment_6(args)
	site_data = comment_7(root)
	comment_8(args, site_data)
	comment_9(args, site, site_data)
	comment_10(args, root)
	data = comment_11(site, dataset, site_data, parser)
	metadata = comment_12(dataset, site_data, site)
	metadata = comment_13(data, args, metadata)
	metadata = comment_14(metadata)
	first, last = comment_15(args)
	starts, ends = comment_16(data)
	start, end = comment_17(starts, ends)
	initial, final = comment_18(first, start, end, frequency, last)
	data = comment_19(initial, final, data)
	output = comment_20(data)
	output = comment_21(args, output)
	header = comment_22(data)
	comment_23(args, site, dataset, metadata, header, output)

start = time.perf_counter()
main()
print(str(time.perf_counter()-start).replace(".",","))