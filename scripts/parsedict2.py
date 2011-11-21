from BeautifulSoup import BeautifulSoup

import json
import logging
import re
import sys
import unicodedata

log = logging.getLogger()

def main():
  logging.basicConfig(level = logging.INFO)

  if len(sys.argv) < 3:
    print('Usage: parsedict.py [dict1.html [dict2.html ...]] output.json')
    sys.exit(1)

  entry_dict = dict()

  for filename in sys.argv[1:-1]:
    log.info('Processing: ' + filename)
    process(filename, entry_dict)

  log.info('Read %s entries.' % (len(entry_dict),))

  open(sys.argv[-1], 'wb').write(json.dumps(entry_dict))

def process(filename, entry_dict):
  html = open(filename, 'rb').read()
  soup = BeautifulSoup(html)

  # Loop over all paragraph elements in the file
  log.info('Searching for entry paragraphs')
  last_entry = None

  word_anchor_name_re = re.compile(r'^word_(ge_)?([\w_]+)(_[ivx]+)?$')
  entry_count_re = re.compile(r'^\s*[IVX]+\.\s*$')

  # The current entry (kept in scope here for continuation paragraphs)
  entry = None

  paras = soup.findAll(name='p')
  log.debug('Found %i paragraphs in file.' % (len(paras),))
  for para in paras:
    # If this a continuation paragraph?
    is_continuation = (u'class', u'second') in para.attrs
    if is_continuation:
      # Use the last entry
      if entry is None:
        log.error('Continuation paragraph with no preceeding entry: ' + str(para))
        continue

      # Remove the class attribute since it is of no use to us
      para.attrs.remove((u'class', u'second'))
    else:
      # An entry has a <b class="entry">...</b> clause
      contained_entry = para.find(name='b', attrs={'class': 'entry'})
      if contained_entry is None:
        continue
      entry = contained_entry

      # Remove the entry from the paragraph
      entry.extract()

      # Strip superscripts from entries
      for t in entry.findAll('sup'):
        t.extract()

      # Remove correction markup
      for t in entry.findAll('ins'):
        t.replaceWith(t.renderContents())

    # Extract the entry text (i.e. the word)
    entry_text = entry.string
    if entry_text is None:
      log.error('Entry is empty: "%r" in "%r".' % (entry, para))
      continue
    entry_text = entry_text.strip()
    if len(entry_text) == 0:
      log.error('Entry is only whitespace: "%r" in "%r".' % (entry, para))
      continue

    # Convert the word to something useful for a dictionary key
    entry_key = to_word_id(entry_text)

    # Ensure an array of entries in the entry dict
    if entry_key not in entry_dict:
      entry_dict[entry_key] = { 'head': entry_text, 'entries': list() }

    # We don't care about page numbers
    for t in para.findAll(name='span', attrs={'class': 'pagenum'}):
      t.extract()

    # We don't care about entry counts
    for t in para.findAll(name='b'):
      if t.string is None:
        continue
      if entry_count_re.match(t.string) is not None:
        t.extract()

    # We don't care about anchors in the entry markup:
    for t in para.findAll(name='a', attrs={'name': word_anchor_name_re}):
      t.replaceWith(t.renderContents())

    # Append this entry
    entry_dict[entry_key]['entries'].append(para.renderContents().strip())

def to_word_id(word):
  """Convert an entry with macrons, non-ASCII characters, etc to an ASCII id."""

  # Normalise combining macron
  word_id = unicodedata.normalize('NFD',word).lower()

  # Replace combining macron
  word_id = word_id.replace(u'\u0304', 'q')

  # Ash => ae
  word_id = word_id.replace(u'\u00e6', 'ae')

  # Eth and thorn => th
  word_id = word_id.replace(u'\u00f0', 'th') # eth
  word_id = word_id.replace(u'\u00fe', 'th') # thorn

  return word_id

if __name__ == '__main__':
  main()
