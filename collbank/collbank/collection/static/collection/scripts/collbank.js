(function ($) {
  $(function () {
    $(document).ready(function () {
      $('#id_DCtype').bind('keyup', type_change);
      $('#id_DCtype').bind('change', type_change);
      $('#id_subtype >option').show();
    });
  });
})(django.jQuery);

// based on the type, action will be loaded

var $ = django.jQuery.noConflict();

function type_change() {
  // Get the value of the selected [DCtype]
  var dctype_type = $('#id_DCtype').val();
  // Create the URL that is needed
  var url_prefix = $(".container").attr("url_home");
  var sUrl = url_prefix + "subtype_choices/?dctype_type=" + dctype_type;
  // Make a request to get all subtype choices for this DCtype
  $.ajax({
    "type": "GET",
    "url": sUrl,
    "dataType": "json",
    "cache": false,
    "success": function (json) {
      $('#id_subtype >option').remove();
      for (var j = 0; j < json.length; j++) {
        $('#id_subtype').append($('<option></option>').val(json[j][0]).html(json[j][1]));
      }
    }
  })(jQuery);
}