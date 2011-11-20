" Vim plugin for automating some translation tasks.
" Author:  Rich Wareham <rjw57@cantab.net>
" License: This file is placed in the public domain.

function! s:PrepareTranslationLine()
python << EOF

import vim
import re

# Get the current editing position
pos = vim.current.window.cursor

# Get the current line's words
non_word_pattern = re.compile('\W+', flags=re.UNICODE)
words = re.split(non_word_pattern, vim.current.line.decode('utf-8'))

# This is a list of new lines to append after this one
new_lines = [ u'| ..' ]

# We want a new line per word:
is_first_word = True
for w in [x for x in words if x is not None and len(x) > 0]:
  new_lines.append(u'| :word:`%s:`' % (w,))

  # If this is the first word, save the position to move to later
  if is_first_word:
    is_first_word = False
    pos = (pos[0]+2, 10 + len(w))

# Add translation line
new_lines.extend([ u'| ..', u'| :trans:``', u'| ..' ])

# Append the lines
vim.current.range.append([x.encode('utf-8') for x in new_lines])

# Move to the first word
vim.current.window.cursor = pos

EOF
endfunction

if !exists(":TransPrepare")
  command TransPrepare :call s:PrepareTranslationLine()
endif
if !exists(":TP")
  command TP :call s:PrepareTranslationLine()
endif
