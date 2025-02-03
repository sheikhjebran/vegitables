"use strict";

$(document).ready(function () {
  //Sales entry variable

  $(document).on("click", ".close_button", function () {
    //Get the element name
    var element_name = $(this).attr("name");
    // Delete the child
    $("#" + element_name + "_child").remove();

    var total = 0;

    $(".qty_validation").each(function (index, element) {
      var my_value = parseInt($(element).val());

      if (Number.isNaN(my_value)) {
        my_value = 0;
      }

      total = total + my_value;
    });

    if (total == parseInt($("#total_number_of_bags").val())) {
      $("#save").show();
    } else {
      $("#save").hide();
    }
  });

  // Code to allow only numbers
  $(document).on("input", ".number_only", function () {
    this.value = this.value.replace(/\D/g, "");
  });

  $(document).on("input", ".mobile", function () {
    this.value = this.value.replace(/\D/g, "");
    if (this.value.length > 10) {
      this.value = this.value.slice(0, 10);
    }
  });

  $(document).on("keypress", ".alpha_and_number", function (event) {
    let keyCode = event.which || event.keyCode;

    if (
      !(
        (keyCode >= 48 && keyCode <= 57) || // 0-9
        (keyCode >= 65 && keyCode <= 90) || // A-Z
        (keyCode >= 97 && keyCode <= 122)
      )
    ) {
      // a-z
      event.preventDefault();
    }
  });

  $(document).on("input", ".decimal_number_only", function () {
    var position = this.selectionStart - 1;
    //remove all but number and .
    var fixed = this.value.replace(/[^0-9\.]/g, "");
    if (fixed.charAt(0) === ".")
      //can't start with .
      fixed = fixed.slice(1);

    var pos = fixed.indexOf(".") + 1;
    if (pos >= 0)
      //avoid more than one .
      fixed = fixed.substr(0, pos) + fixed.slice(pos).replace(".", "");

    if (this.value !== fixed) {
      this.value = fixed;
      this.selectionStart = position;
      this.selectionEnd = position;
    }
  });

  $(document).on("submit", "#arrival_entry_form", function (e) {
    var total_bags_count = parseInt($("#total_number_of_bags").val());
    if (total_bags_count <= 0) {
      e.preventDefault();
      alert("Cannot have total bags count ZERO !");
      return false;
    } else {
      var total = 0;
      var ZERO_FLAG = false;
      $(".qty_validation").each(function (index, element) {
        var my_value = parseInt($(element).val());
        if (Number.isNaN(my_value)) {
          my_value = 0;
        }
        if (my_value == 0) {
          ZERO_FLAG = true;
        }
        total = total + my_value;
      });

      if (total == parseInt($("#total_number_of_bags").val()) && total != 0) {
        console.log("Ready to SUBMIT .. !");
      } else {
        e.preventDefault();
        if (ZERO_FLAG == true) {
          alert("Cannt have ZERO as Qty for the item..!");
        } else {
          if (
            total <= parseInt($("#total_number_of_bags").val()) &&
            total != 0
          ) {
            $("#add_arrivel_entry_list").trigger("click");
          }
        }
        return false;
      }
    }
  });

  // Arrival entry lorry validation
  const arrival_entry_lorry_number = $(".arrival_entry_lorry_number");
  const add_arrival_entry_button = $("#add_arrivel_entry_list");
  const arrival_entry_save_button = $("#save");
  const arrival_entry_date = $(".arrival_entry_date");

  function hide_show_arrival_entry_button(condition) {
    if (condition) {
      add_arrival_entry_button.show();
      arrival_entry_save_button.show();
    } else {
      add_arrival_entry_button.hide();
      arrival_entry_save_button.hide();
    }
  }
  function ValidateLorryEntryOnArrivalEntry() {
    $.ajax({
      url: "/get_arrival_duplicate_validation_api",
      method: "GET",
      type: "GET",
      async: true,
      credentials: "same-origin",
      xhrFields: { withCredentials: true },
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
      data: {
        lorry_no: $(".arrival_entry_lorry_number").val(),
        date: $(".arrival_entry_date").val(),
      },
      success: function (response) {
        console.log("AJAX request successful");
        hide_show_arrival_entry_button(response.NOT_FOUND);
      },
      error: function (xhr, status, error) {
        console.log("AJAX request failed");
        console.log("Status: " + status);
        console.log("Error: " + error);
        hide_show_arrival_entry_button(xhr.responseJSON.NOT_FOUND);
      },
    });
  }

  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != "") {
      var cookies = document.cookie.split(";");
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) == name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  arrival_entry_lorry_number.on(
    "keyup change",
    ValidateLorryEntryOnArrivalEntry
  );
  arrival_entry_date.on("keyup change", ValidateLorryEntryOnArrivalEntry);

  // Report
  const report_sales_entry_selected = $(".sales_bill_report");

  function update_sales_bill_report_table(result) {
    $("#tableWrapper").children("tbody").children("tr").remove();
    for (var index = 0; index < result.length; index++) {
      $("#tableWrapper")
        .children("tbody")
        .last()
        .append(
          `
                <tr>
                        <td>` +
            result[index].id +
            `</td>
                        <td>` +
            result[index].customer_name +
            `</td>
                        <td>` +
            result[index].item_name +
            `</td>
                        <td>` +
            result[index].bags +
            `</td>
                        <td>` +
            result[index].amount +
            `</td>
                        <td>` +
            result[index].balance +
            `</td>
                        <td>` +
            result[index].payment_type +
            `</td>
                </tr>
              `
        );
    }
  }
  function CheckSalesBill_Report() {
    $.ajax({
      url: "/report_sales_bill",
      method: "GET",
      async: true,
      data: {
        date: $(this).val(),
      },
      success: function (response) {
        console.log("AJAX request successful");
        update_sales_bill_report_table(response.result);
      },
      error: function (xhr, status, error) {
        console.log("AJAX request failed");
        console.log("Status: " + status);
        console.log("Error: " + error);
      },
    });
  }
  report_sales_entry_selected.on("keyup change", CheckSalesBill_Report);

  // Main code end's here
});

function removeElement(el) {
  console.log(el);

  var element = document.getElementById(el);

  element.remove();
}
