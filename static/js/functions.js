// Global Constants

BaseinputOptions = ['None', 'All', 'Web Interface', 'OSC2MIDI']
BaseoutputOptions = ['None', 'All']
ModeOptions = ['Thru', 'Mapped']


function build_options(element, options, activeOption) {
  var $el = element
  $el.empty() // remove old options
  $.each(options, function(i) {
    $el.append($("<option></option>")
       .attr("value", options[i]).text(options[i]));
  $('#'+$el.attr("id")+' option[value="'+activeOption+'"]').attr('selected','selected')
  })
}

function build_options_fromDict(element, options, activeOption) {
  var $el = element
  $el.empty() // remove old options
  $.each(options, function(key,value) {
    $el.append($("<option></option>")
       .attr("value", value).text(key)
     );
  $('#'+$el.attr("id")+' option[value="'+activeOption+'"]').attr('selected','selected')
  })
}

function getIOoptions(type, availableIO) {
  io_options = []
  switch (type) {
    case 'outputs':
      $.each(BaseoutputOptions, function(i) {
        io_options.push(BaseoutputOptions[i])
      });
      break
    case 'inputs':
      $.each(BaseinputOptions, function(i) {
        io_options.push(BaseinputOptions[i])
      });
      break
  }
  $.each(availableIO, function(i) {
    io_options.push(availableIO[i])
  });
  return io_options
}
