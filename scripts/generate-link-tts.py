import csv

sourcefile = '../lib/ModeData/trips_attributes_nate.csv'
outfile = '../lib/LinkTravelTimesWithPrecision.py'

print('link_travel_times_prec4 = {', file=open(outfile, 'a+'))
with open(sourcefile) as f:
	reader = csv.reader(f)
	next(reader)
	for row in reader:
		olat = round(float(row[0]), 4)
		olng = round(float(row[1]), 4)
		dlat = round(float(row[2]), 4)
		dlng = round(float(row[3]), 4)
		duration = row[-1]
		print('({}, {}, {}, {}): {}, '.format(olng, olat, dlng, dlat, duration), file=open(outfile, 'a'))

print('}', file=open(outfile, 'a', newline=''))