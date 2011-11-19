import cgi
import sys
import re

try:
  from itertools import izip_longest
except ImportError:
  from itertools import zip_longest as izip_longest

def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

###### DATA MODEL

class ParseError(Exception):
  def __init__(self, msg):
    self.msg = msg
  
  def __str__(self):
    return self.msg

class Line(object):
  def __init__(self, raw_text):
    self.raw_text = raw_text

  def __str__(self):
    return self.raw_text

class BlankLine(Line): pass
class PlainLine(Line): pass

class SpecialLine(Line):
  # special lines do not appear in the output
  def __str__(self):
    return ''

class CommentLine(SpecialLine): pass
class RoleLine(SpecialLine): pass

def split_half_lines(text):
  half_lines = []
  current_half_line = []

  half_line_end_sep = re.compile(r'\s\s+$')
  for w, s in grouper(2, re.split('(\W+)', text, flags=re.UNICODE)):
    current_half_line.append((w,s))

    if s is not None and len(current_half_line) > 0 and re.search(half_line_end_sep, s) is not None:
      half_lines.append(current_half_line)
      current_half_line = []

  if len(current_half_line) > 0:
    half_lines.append(current_half_line)

  return half_lines

class TextLine(Line):
  GENDER_TABLE = {
      'm': 'masculine',
      'f': 'feminine',
      'n': 'neuter',
  }

  QUANTITY_TABLE = {
      's': 'singular',
      'd': 'dual',
      'p': 'plural',
  }

  CASE_TABLE = {
      'n': 'nominative',
      'a': 'accusitive',
      'g': 'genitive',
      'd': 'dative',
      'i': 'instrumental',
  }

  def _parse_int_pronoun_inflection_spec(self, spec):
    if len(spec) != 2:
      raise ParseError('Error parsing interrogative pronoun inflection: %s' % (spec,))

    try:
      return ', '.join([
          TextLine.CASE_TABLE[spec[0]],
          TextLine.GENDER_TABLE[spec[1]], 
      ])
    except KeyError:
      raise ParseError('Error parsing interrogative pronoun inflection: %s' % (spec,))

  def _parse_12_pronoun_inflection_spec(self, spec):
    if len(spec) != 2:
      raise ParseError('Error parsing pronoun inflection: %s' % (spec,))

    try:
      return ', '.join([
          TextLine.CASE_TABLE[spec[0]],
          TextLine.QUANTITY_TABLE[spec[1]], 
      ])
    except KeyError:
      raise ParseError('Error parsing pronoun inflection: %s' % (spec,))

  def _parse_noun_inflection_spec(self, spec):
    if len(spec) != 3:
      raise ParseError('Error parsing noun inflection: %s' % (spec,))

    try:
      return ', '.join([
          TextLine.CASE_TABLE[spec[0]],
          TextLine.QUANTITY_TABLE[spec[1]], 
          TextLine.GENDER_TABLE[spec[2]], 
      ])
    except KeyError:
      raise ParseError('Error parsing noun inflection: %s' % (spec,))

  def __init__(self, raw_text, text, line_no):
    super(TextLine, self).__init__(raw_text)
    self.line_no = line_no
    self.translation = None
    self.word_analysis = []
    self.text = text

    # split line into half lines
    self.half_lines = split_half_lines(self.text)

  def words(self):
    return re.split('\W+', self.text, flags=re.UNICODE)

  def parse_analysis(self, word, analysis):
    """Return a tuple describing the class of the word and some html of the anlyais."""

    fields = re.split(r':\s*', analysis)
    if fields[0] != word:
      raise ParseError('Malformed description for %s: %s' % (word, analysis))

    if len(fields) < 2 or len(fields[1].strip()) == 0:
      # no discussion of this word yet,
      return None

    if len(fields) < 3:
      raise ParseError('No conclusion in analysis: %s' % (analysis,))

    if len(fields) > 3:
      raise ParseError('Too many fields in analysis: %s' % (analysis,))
    
    discussion, conclusion = fields[1:]

    # Try to determine word class by looking at discussion
    word_class = 'unknown'
    display_class = 'unknown'

    discussion_words = discussion.split(' ')
    verb_match = re.match(r'([0-9IV]+) (.*)', discussion)
    noun_match = re.match(r'([nagdi][sp][mnf]+) (.*)', discussion)
    adjective_match = re.match(r'(adj\.+) (.*)', discussion)
    pronoun_word = 'pron.'
    conj_word = 'conj.'
    adv_word = 'adv.'
    prep_word = 'prep.'
    anom_word = 'anom.'
    spec_word = 'spec.'
    
    discussion_html = []

    if conj_word in discussion_words:
      word_class = 'conjunctive'
      display_class = 'conjunctive'
      discussion_words.remove(conj_word)
    elif anom_word in discussion_words:
      word_class = 'anomalous'
      display_class = 'anomalous'
      discussion_words.remove(anom_word)

      try:
        root = discussion_words[-1]
      except IndexError:
        raise ParseError('No root word in analysis: %s' % (discussion,))
      discussion_words = discussion_words[:-1]

      discussion_html.extend(discussion_words)
      discussion_words = []
      discussion_html.append('of <i>' + root + '</i>')
    elif adv_word in discussion_words:
      word_class = 'adverb'
      display_class = 'adverb'
      discussion_words.remove(adv_word)
    elif prep_word in discussion_words:
      word_class = 'preposition'
      display_class = 'preposition'
      discussion_words.remove(prep_word)

      if len(discussion_words) > 0:
        with_what = discussion_words[0]
        discussion_words = discussion_words[1:]

        if with_what[0:2] != 'w.':
          raise ParseError('Could not parse preposition with clause: %s' % (with_what,))

        try:
          cases = []
          for c in with_what[2:].split('.'):
            if len(c) > 0:
              cases.append(TextLine.CASE_TABLE[c])
          discussion_html.append('with ' + ', '.join(cases))
        except KeyError:
          raise ParseError('Could not parse preposition with clause: %s' % (with_what,))

    elif pronoun_word in discussion_words:
      discussion_words.remove(pronoun_word)

      if 'dem.' in discussion_words:
        discussion_words.remove('dem.')
        word_class = 'pronoun demonstrative-pronoun'
        display_class = 'pronoun (demonstrative)'
        discussion_html.append(self._parse_noun_inflection_spec(discussion_words[0]))
        discussion_words = discussion_words[1:]
      elif 'int.' in discussion_words:
        discussion_words.remove('int.')
        word_class = 'pronoun interrogative-pronoun'
        display_class = 'pronoun (interrogative)'
        discussion_html.append(self._parse_int_pronoun_inflection_spec(discussion_words[0]))
        discussion_words = discussion_words[1:]
      elif 'pers.' in discussion_words:
        discussion_words.remove('pers.')
        word_class = 'pronoun personal-pronoun'
        display_class = 'pronoun (personal)'

        if '1' in discussion_words:
          discussion_words.remove('1')
          discussion_html.append('first person, ')
          discussion_html.append(self._parse_12_pronoun_inflection_spec(discussion_words[0]))
          discussion_words = discussion_words[1:]
        elif '2' in discussion_words:
          discussion_words.remove('2')
          discussion_html.append('second person, ')
          discussion_html.append(self._parse_12_pronoun_inflection_spec(discussion_words[0]))
          discussion_words = discussion_words[1:]
        elif '3' in discussion_words:
          discussion_words.remove('3')
          discussion_html.append('third person, ')
          discussion_html.append(self._parse_noun_inflection_spec(discussion_words[0]))
          discussion_words = discussion_words[1:]
        else:
          word_class = 'error'
          discussion_html.append('MISSING PERSON ')

      else:
        discussion_html.append('UNKNOWN CLASS OF PRONOUN ')
        word_class = 'error'
    elif spec_word in discussion_words:
      word_class = 'special'
      display_class = 'special'
      discussion_words.remove(spec_word)
      discussion_html.extend(discussion_words)
      discussion_words = []
    elif adjective_match is not None:
      discussion_words.remove(adjective_match.group(1))
      word_class = 'adjective'
      display_class = 'adjective'

      spec = discussion_words[0]
      discussion_words = discussion_words[1:]
      discussion_html.append(self._parse_noun_inflection_spec(spec) + ' ')

      if 'w.' in discussion_words:
        discussion_words.remove('w.')
        discussion_html.append('(weak)')
      #elif 's.' in discussion_words:
      #  discussion_words.remove('s.')
      #  discussion_html.append('(strong)')
      #else:
      #  word_class = 'error'
      #  discussion_html.append('STRONG OR WEAK?')

      try:
        root = discussion_words[-1]
      except IndexError:
        raise ParseError('No root word in analysis: %s' % (discussion,))
      discussion_words = discussion_words[:-1]
      discussion_html.append('of <i>' + root + '</i>')
    elif verb_match is not None:
      verb_class = verb_match.group(1)
      discussion_words.remove(verb_class)

      word_class = 'verb verb-class-%s' % (verb_class,)

      inflection = ['class %s' % (verb_class,)]

      if 'inf.'  in discussion_words:
        inflection.append('infinitive')
        discussion_words.remove('inf.')
      elif 'pret.' in discussion_words:
        inflection.append('preterite')
        discussion_words.remove('pret.')
      else:
        inflection.append('present')

      if '3' in discussion_words:
        inflection.append('third person')
        discussion_words.remove('3')
      elif '2' in discussion_words:
        inflection.append('second person')
        discussion_words.remove('2')
      elif '1' in discussion_words:
        inflection.append('first person')
        discussion_words.remove('1')

      if 'subj.' in discussion_words:
        inflection.append('subjunctive')
        discussion_words.remove('subj.')

      if 'pl.' in discussion_words:
        inflection.append('plural')
        discussion_words.remove('pl.')

      discussion_html.append(', '.join(inflection))

      try:
        root = discussion_words[-1]
      except IndexError:
        raise ParseError('No root word in analysis: %s' % (discussion,))
      discussion_words = discussion_words[:-1]

      display_class = 'verb (%s)' % (root,)
      # discussion_html.append('of <i>' + root + '</i>')
    elif noun_match is not None:
      spec = noun_match.group(1)
      discussion_words.remove(spec)

      word_class = 'noun'
      display_class = 'noun'

      discussion_html.append(self._parse_noun_inflection_spec(spec) + ' ')

      if 'prop.' in discussion_words:
        discussion_words.remove('prop.')
        display_class += ' (proper)'
        if len(discussion_words) > 2:
          raise ParseError('More discussion than necessary?: %s' % (discussion,))
      else:
        try:
          root = discussion_words[-1]
        except IndexError:
          raise ParseError('No root word in analysis: %s' % (discussion,))
        discussion_words = discussion_words[:-1]
        display_class += ' (<em>' + root + '</em>)'
        # discussion_html.append('of <i>' + root + '</i>')
    else:
      discussion_html.append(cgi.escape(discussion))

    # is the remainder a note?
    remainder = ' '.join(discussion_words)
    remainder_match = re.match(r'^\((.*)\)$', remainder)
    if remainder_match is not None:
      discussion_html.append('<div class="oe-analysis-note">%s</div>' % (remainder_match.group(1)))
    elif len(discussion_words) > 0:
      word_class = 'error'
      discussion_html.append('EXTRANEOUS DETAIL')
      discussion_html.append(' '.join(discussion_words))

    html = ''.join([
      '<div class="oe-analysis-conclusion">%s</div>' % (cgi.escape(fields[2]),),
      '<div class="oe-analysis-class">%s</div>' % (display_class,),
      '<div class="oe-analysis-discussion">%s</div>' % (' '.join(discussion_html),),
    ])

    return (word_class, html)

  def html(self):
    lines = [ '<div class="oe-text-line">' ]

    lines.append('<div class="oe-text-line-number">%s</div>' % (self.line_no,))
    lines.append('<div class="oe-text-original">')

    have_analysis = len(self.word_analysis) > 0
    analysis_iter = self.word_analysis.__iter__()

    for hl in self.half_lines:
      if len(self.half_lines) > 1:
        lines.append('<span class="oe-text-half-line">')

      for word, sep in hl:
        word_class = 'unknown'
        discussion_html = None

        if len(word) > 0 and have_analysis:
          analysis = next(analysis_iter)
          try:
            pa = self.parse_analysis(word, analysis)
          except ParseError as pe:
            raise ParseError('Error parsing %s: %s' % (analysis, pe.msg))
          if pa is not None:
            word_class, discussion_html = pa
        else:
          if sep is None:
            sep = ''
          if word is None:
            word = ''
          word_class = ''
          discssion_html = None

        lines.append('<span class="oe-word"><span class="%s">%s</span>%s'
            % (' '.join(['oe-word-class-'+x for x in word_class.split()]), cgi.escape(word), cgi.escape(sep)))
        if discussion_html is not None:
          lines.append('<span class="oe-word-analysis">%s</span>' % (discussion_html,))
        lines.append('</span>')

      if len(self.half_lines) > 1:
        lines.append('</span>')

    lines.append('</div>')

    if self.translation is not None:
      lines.append('<div class="oe-text-translation">')
      translation_half_lines = split_half_lines(self.translation)
      for hl in translation_half_lines:
        words = ''
        for w, s in hl:
          words += w
          if s is not None:
            words += s
        if len(translation_half_lines) > 1:
          lines.append('<span class="oe-text-half-line">%s</span>' % (words,))
        else:
          lines.append(words)
      lines.append('</div>')

    lines.append('</div>')

    return '\n'.join(lines)

  def __str__(self):
    return '.. raw:: html\n\n  ' + '\n  '.join(self.html().split('\n')) + '\n\n'

###### RST parser

def parse(lines):
  records = []
  text_lines = []

  comment_pat = re.compile(r'\s*\.\.', flags=re.UNICODE)
  role_pat = re.compile(r'\s*:(\w+):`(.*)`\s*$', flags=re.UNICODE)

  for line in lines:
    if hasattr(line, 'decode'):
      line = line.decode('utf-8')

    r = PlainLine(line)

    if len(line.strip()) == 0:
      r = BlankLine(line)
    elif len(line) >= 2 and line[0:2] == '| ':
      remainder = line[2:]
      role_match = re.match(role_pat, remainder)
      comment_match = re.match(comment_pat, remainder)

      if comment_match is not None:
        r = CommentLine(line)
      elif role_match is not None:
        r = RoleLine(line)

        role, text = role_match.groups()
        if role == 'trans':
          text_lines[-1].translation = text
        if role == 'word':
          text_lines[-1].word_analysis.append(text)
      else:
        r = TextLine(line, remainder, len(text_lines) + 1)
        text_lines.append(r)

    if r is not None:
      records.append(r)

  return records

if __name__ == '__main__':
  in_file = open(sys.argv[1], 'r')
  out_file = open(sys.argv[2], 'w')

  try:
    records = parse(in_file.readlines())
    for r in records:
      try:
        out_file.write(str(r))
      except UnicodeEncodeError:
        l = r.__str__().encode('utf-8')
        out_file.write(l)
  except ParseError as e:
    print('Parse error: %s' % (e,))
    sys.exit(1)

