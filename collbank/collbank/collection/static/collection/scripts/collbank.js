var django = {
  "jQuery": jQuery.noConflict(true)
};
var jQuery = django.jQuery;
var $ = jQuery;


(function ($) {
  $(function () {
    $(document).ready(function () {
      var i = 0,    // COunter
        sIdDC = "", // ID
        sIdSub = "";

      for (i = 0; i < 10; i++) {
        sIdDC = "id_collection12m_resource-" + i.toString() + "-DCtype";
        sIdSub = "id_collection12m_resource-" + i.toString() + "-subtype";
        if ($('#' + sIdDC).length > 0) {
          // Bind the keyup and change events
          $('#' + sIdDC).bind('keyup change', ru.collbank.type_change);
          $('#' + sIdSub + ' >option').show();
          $('#' + sIdDC).each(function () { ru.collbank.type_change(this); });
        }
      }
      // Add 'copy' action to inlines
      ru.collbank.tabinline_add_copy();
      // Add 'collection-resource-closed' classes to all RESOURCES shown
      ru.collbank.inlineresources_add_closed();
    });
  });
})(django.jQuery);

// based on the type, action will be loaded

var $ = django.jQuery.noConflict();


//var $ = jQuery;

var ru = (function ($, ru) {
  "use strict";

  ru.collbank = (function ($, config) {
    // Define variables for ru.collbank here
    var loc_example = "";

    // Private methods specification
    var private_methods = {
      /**
       * methodNotVisibleFromOutside - example of a private method
       * @returns {String}
       */
      methodNotVisibleFromOutside: function () {
        return "something";
      }
    }

    // Public methods
    return {
      type_change: function (el) {
        // Figure out how we are called
        if (el.type === "change" || el.type === "keyup") {
          // Need to get the element proper
          el = this;
        }
        // Get the value of the selected [DCtype]
        // var dctype_type = $('#id_DCtype').val();
        var dctype_type = $(el).val();
        var sIdSub = $(el).attr("id").replace("DCtype", "subtype");
        var subtype_type = $("#" + sIdSub).val();
        // Create the URL that is needed
        var url_prefix = $(".container[url_home]").attr("url_home");
        if (url_prefix === undefined) {
          url_prefix = $("#container").attr("url_home");
        }
        var sUrl = url_prefix + "subtype_choices/?dctype_type=" + dctype_type;
        // Define the options
        var ajaxoptions = {
          type: "GET",
          url: sUrl,
          dataType: "json",
          async: false,
          success: function (json) {
            $('#' + sIdSub + ' >option').remove();
            for (var j = 0; j < json.length; j++) {
              $('#' + sIdSub).append($('<option></option>').val(json[j][0]).html(json[j][1]));
            }
            // Set the selected value correctly
            $("#" + sIdSub).val(parseInt(subtype_type, 10));
          }
        };
        // Execute the ajax request SYNCHRONOUSLY
        $.ajax(ajaxoptions);
        // Do something else to provide a break point
        var k = 0;
      },

      /**
       * tabinline_add_copy
       *   Add a COPY button to all tabular inlines available
       */
      tabinline_add_copy : function() {
        $(".tabular .related-widget-wrapper").each(
          function (idx, obj) {
            // Find the first <a> child
            var chgNode = $(this).children("a").first();
            var sHref = $(chgNode).attr("href");
            if (sHref !== undefined) {
              // Remove from /change onwards
              var iChangePos = sHref.lastIndexOf("/change");
              if (iChangePos > 0) {
                sHref = sHref.substr(0, sHref.lastIndexOf("/change"));
                // Get the id
                var lastSlash = sHref.lastIndexOf("/");
                var sId = sHref.substr(lastSlash + 1);
                sHref = sHref.substr(0, lastSlash);
                // Get the model name
                lastSlash = sHref.lastIndexOf("/");
                var sModel = sHref.substr(lastSlash + 1);
                sHref = sHref.substr(0, lastSlash);
                // Find and adapt the history link's content to a current
                var sCurrent = $(".historylink").first().attr("href").replace("/history", "");
                // Create a new place to go to
                sHref = sHref.replace("collection", "copy") + "/?_popup=0&model=" + sModel + "&id=" + sId + "&current=" + sCurrent;
                var sAddNode = "<a class='copy-related' title='Make a copy' href='" + sHref + "'>copy</a>";
                // Append the new node
                $(this).append(sAddNode);
              }
            }
          });
      },

      /**
       * inlineresources_add_closed
       *   Add elements to each instance of the class ["djn-dynamic-form-collection-resource"]
       */
      inlineresources_add_closed : function() {
        // Iterate over all [djn-dynamic-form-collection-resource] objects
        $(".djn-dynamic-form-collection-resource").each(
          function (idxResource, obj) {
            var sHtmlId = "";

            // Get my ID
            sHtmlId = $(this).attr("id");
            // Iterate over all children
            $(this).children().each(function (idx, obj) {
              var lHtml = [], // Html we are producing
                  sId = "",   // ID of this resource
                  sTag = "";  // Tag we are visiting

              sTag = $(this).get(0).tagName.toLowerCase();
              sId = "resource #" + (idxResource + 1);
              // Check what kind of child this is
              switch (sTag) {
                case "h3":
                  // Create a <span> with a button 
                  lHtml.push("<span class='btn btn-primary btn-xs'");
                  lHtml.push("onclick='ru.collbank.toggle_resource(\"" + sHtmlId + "\", " + (idxResource + 1) + ");'");
                  lHtml.push(">");
                  lHtml.push("Show " + sId);
                  lHtml.push("</span>&nbsp;&nbsp;");
                  // Actually add it
                  $(this).children().first().prepend(lHtml.join(' '));
                  break;
                default:
                  // Add the class [collection-resource-closed]
                  $(this).addClass("collection-resource-closed");
                  break;
              }
            });
          });
      },

      /**
       * toggle_resource
       *   Toggle the visibility of this resource
       */
      toggle_resource : function(sHtmlId, iNumber) {
        var elThis;

        // Get to this element
        elThis = $("#" + sHtmlId);
        // Visit the children
        $(elThis).children().each(function (idx, obj) {
          var sTag = "",
              elSpan,
              sId = "";

          sTag = $(this).get(0).tagName.toLowerCase();
          sId = "resource #" + (idx + 1);
          // Check what kind of child this is
          switch (sTag) {
            case "h3": // Change the wording
              elSpan = $(this).find("span").first();
              if ($(elSpan).text().indexOf("Show") < 0) {
                $(elSpan).text("Show " + sId);
              } else {
                $(elSpan).text("Hide " + sId);
              }
              break;
            default:
              // Action depends on which class it has
              if ($(this).hasClass("collection-resource-closed")) {
                // Remove and replace it
                $(this).removeClass("collection-resource-closed");
                $(this).addClass("collection-resource-open");
              } else {
                // Remove and replace it
                $(this).addClass("collection-resource-closed");
                $(this).removeClass("collection-resource-open");
              }
              break;
          }
        });
      }
    };
  }($, ru.config));

  return ru;
}(jQuery, window.ru || {})); // window.ru: see http://stackoverflow.com/questions/21507964/jslint-out-of-scope

