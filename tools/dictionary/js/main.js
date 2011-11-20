var dictionary = null;

$(document).ready(function() {
  loading_dialog = $('#loading_dialog').dialog({
    modal: true, resizable: false, draggable: false,
    beforeClose: function() { return dictionary; },
  });

  $('#search').bind('input', function() {
    query = $('#search').attr('value').trim();
    results = $('#search_results');

    results.empty();
    if(query.length == 0) {
      return;
    }

    words = []
    for(word_id in dictionary.words) {
      // Remove 'q's (macrons) from word ids
      norm_word_id = word_id.replace(/q/g, '');
      if(0 === norm_word_id.indexOf(query)) {
        words.push(word_id);
      }
    }
    if(words.length > 300) {
      return;
    }

    words = words.sort(function(a,b) {
      a = a.replace(/q/g, '');
      b = b.replace(/q/g, '');

      if(a === b) {
        return 0;
      }

      return a < b ? -1 : 1;
    });

    result_list = []
    for(word_id_idx in words) {
      word_id = words[word_id_idx];

      entries = dictionary.words[word_id];
      for(idx in entries) {
        result_list.push(entries[idx]);
      }
    }

    console.log('Search: ' + query + ' -> ' + result_list.length.toString() + ' results');

    for(idx in result_list) {
      results.append(result_list[idx]);
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
