#!/usr/bin/env python2

from BeautifulSoup import BeautifulSoup
import glob
import json
import re
import sys

class ParseError(Exception):
  def __init__(self, message):
    self.message = message

  def __str__(self):
    return self.message

def main():
  word_dict = { }
  entry_dict = { }

  if len(sys.argv) < 3:
    print('Usage: parsedict.py [dict1.html [dict2.html ...]] output.json')
    sys.exit(1)

  for dict_filename in sys.argv[1:-1]:
    parse_dict(dict_filename, word_dict, entry_dict)

  print('Writing JSON to %s...' % (sys.argv[-1],))
  out_file = open(sys.argv[-1], 'w')
  out_file.write(json.dumps({ 'words': word_dict, 'entries': entry_dict }))

def parse_dict(source_html, word_dict, entry_dict):
  print('Loading ' + source_html)
  soup = BeautifulSoup(open(source_html).read())

  # Look for each entry in the dictionary
  print('Searching...')
  entries = soup.findAll(name='b', attrs={ 'class': 'entry' })

  for entry in entries:
    # An entry is either a reference to another entry or is a word.

    entry_str = ' '.join([x.string for x in entry.contents])
    entry_str = entry_str.strip()

    if entry_str not in entry_dict:
      entry_dict[entry_str] = [ ]

    # Is it a word entry?
    word_entry = parse_word_entry(entry)
    if word_entry is not None:
      if word_entry['id'] in word_dict:
        raise ParseError('Duplicate entry: %s (%s)' % (entry, word_entry))
      word_dict[word_entry['id']] = \
          [x.prettify() for x in word_entry['defs']]
      entry_dict[entry_str].extend(
          [x.prettify() for x in word_entry['defs']])
      continue

    # Is it a reference?
    ref_entry = parse_reference_entry(entry)
    if ref_entry is not None:
      entry_dict[entry_str].append(ref_entry['ref'].prettify())
      continue

    print('Warning: could not determine type of entry: %s' % (entry,))

def parse_word_entry(entry):
  word_name_pattern = re.compile(r'word_(ge_)?([\w]+)(_[ivx]+)?', re.U)

  # Words are surrounded by an <a> tag with a name which matches
  # word_name_pattern *and which is not an error*
  parent = entry.parent
  if parent.name != 'a':
    return None

  if (u'class', u'error') in parent.attrs:
    return None

  try:
    name_match = re.match(word_name_pattern, parent['name'])
  except KeyError:
    print('skipping weird entry: %s' % (entry,))
    return None

  if name_match is None:
    return None

  ge_prefix = name_match.group(1)
  word_id = name_match.group(2)
  word_num = name_match.group(3)

  if ge_prefix is not None:
    word_id = ge_prefix + word_id
  
  # For the main entry, there should be no secondary words
  if word_num is not None:
    raise ParseError('Unexpected secondary word entry: %s' % (entry,))

  parent_para = parent.parent
  if parent_para.name != 'p':
    raise ParseError('Word entry not surrounded by <p>:' % (parent,))

  word_paras = [parent_para]

  # Look for secondary paragraphs
  next_sib = word_paras[-1].nextSibling
  keep_going = True
  while keep_going and next_sib is not None:
    # Skip text
    if hasattr(next_sib, 'name'):
      if next_sib.name != 'p':
        keep_going = False
        continue
      if (u'class', u'second') not in next_sib.attrs:
        keep_going = False
        continue
      word_paras.append(next_sib)
    next_sib = next_sib.nextSibling

  return { 'id': word_id, 'defs': word_paras }

def parse_reference_entry(entry):
  # Reference entries have a <p> parent
  parent = entry.parent

  if parent.name == 'a' and (u'class', u'error') in parent.attrs:
    parent = parent.parent

  if parent.name != 'p':
    return None

  return { 'ref': parent }

if __name__ == '__main__':
  main()
