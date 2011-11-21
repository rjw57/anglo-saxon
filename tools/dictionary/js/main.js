var dictionary = null;

$(document).ready(function() {
  loading_dialog = $('#loading_dialog').dialog({
    modal: true, resizable: false, draggable: false,
    beforeClose: function() { return dictionary; },
  });

  $('#search').bind('input', function() {
    query = $('#search').attr('value').trim().toLowerCase();
    results_elem = $('#search-results');

    // Empty the results display
    results_elem.empty();

    // No query? We're done.
    if(query.length == 0) {
      return;
    }

    // Generate a list of objects representing the search results. Each object
    // has a score attribute and id attribute.
    results = [];
    for(word_id in dictionary) {
      // Remove 'q's (macrons) from word ids
      norm_word_id = word_id.replace(/q/g, '');

      score = -1; // no match

      // exact match?
      if(norm_word_id == query) {
        score = 100;
      } else if(0 === norm_word_id.indexOf(query)) {
        // partial match, score based on remaining letter count
        score = 100 / (1 + norm_word_id.length - query.length);
      } else {
        // search entries
        entries = dictionary[word_id].entries;
        for(entry_idx in entries) {
          entry_text = entries[entry_idx].toLowerCase();
          if(-1 != entry_text.indexOf(query))
          {
            score = 25;
          }
        }
      }

      // skip negative score
      if(score < 0) {
        continue;
      }

      results.push({'score': score, 'id': word_id });
    }

    if(results.length > 300) {
      results = results.slice(0, 300);
    }

    // sort by _ascending_ score and then normalised word if
    results = results.sort(function(a,b) {
      // sort by score
      if(a.score !== b.score) {
        return b.score - a.score;
      }

      // then by id
      a_id = a.id.replace(/q/g, '');
      b_id = b.id.replace(/q/g, '');
      if(a_id === b_id) {
        return 0;
      }
      return a_id < b_id ? -1 : 1;
    });

    for(result_idx in results) {
      var result = results[result_idx];
      var word_id = result.id;

      var head = dictionary[word_id].head;
      var entries = dictionary[word_id].entries;

      var result_elem = $('<div class="result">')
      result_elem.append($('<div class="head">').text(head));

      var entries_elem = $('<div class="entries">');
      
      if(entries.length > 1) {
        var list_elem = $('<ol>');
        for(idx in entries) {
          list_elem.append($('<li>').html(entries[idx]));
        }
        entries_elem.append(list_elem)
      } else {
        entries_elem.append($('<p>').html(entries[0]));
      }

      // filter any links to fill in the search box
      entries_elem.find('a[href*="#word_"]').each(function() {
        var target = $(this).attr('href').replace(/^.*#word_/, '');
        target = target.replace(/_[ivx]+$/, '');
        target = target.replace(/_/g, ' ');
        $(this).attr('href', '#');
        $(this).click(function() {
          $('#search').attr('value', target).trigger('input');
        });
      });

      result_elem.append(entries_elem);
      results_elem.append(result_elem);
    }
  });

  $('#search').focus();
  $('form').submit(function() { return false; });

  $.getJSON('dictionary.json', function(data, textStatus) {
    $('#loading_dialog').text('Loaded');
    loading_dialog.dialog('close');
    dictionary = data;
  });
});
