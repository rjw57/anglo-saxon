import re
import sys

# A word in a unicode sense
word_pattern = re.compile('\W+', re.UNICODE)

in_file = sys.stdin
out_file = sys.stdout

line_records = []

for line in in_file.readlines():
	line = unicode(line, 'utf-8')
	stripped_line = line.strip()

	record = { 'line': line }

	# What type is the line?
	if len(stripped_line) == 0:
		record['type'] = 'blank'
	elif stripped_line[0] == '#':
		record['type'] = 'comment'
	else:
		record['type'] = 'text'
	
	line_records.append(record)

# Output lines

for record in line_records:
	out_file.write(record['line'].encode('utf-8'))

	if record['type'] != 'text':
		continue

	new_lines = [u'\n']
	for word in re.split(word_pattern, record['line'].strip()):
		word = word.strip()
		if len(word) == 0:
			continue
		com = u'# w: %s:\n' % (word,)
		new_lines.append(com)

	new_lines.append(u'\n')
	out_file.writelines([x.encode('utf-8') for x in new_lines])

