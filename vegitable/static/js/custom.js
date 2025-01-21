"use strict";

$(document).ready(function () {
  //Sales entry variable
  const rmc_input_box = $("#rmc");
  const commission_input_box = $("#comission");
  const cooli_input_box = $("#cooli");
  const total_amount = $("#total_amount");
  const paid_amount = $("#paid_amount");
  const balance_amount = $("#balance_amount");

  //logic to calculate rmc , commission, cooli
  $(document).on("keyup change", ".calculate_amount", function () {
    var rate_id = $(this).attr("id");
    var rate_value = $(this).val();
    Calculate_Rmc_Commission_Cooli(rate_id, rate_value);
  });

  $(document).on("keyup change", "#cooli", function () {
    Calculate_Cooli();
  });

  function get_total_amount_from_sales_entry_form() {
    var local_total_amount = 0;
    $(".amount_validation").each(function (index, element) {
      var my_value = parseFloat($(element).val());
      if (Number.isNaN(my_value)) {
        my_value = 0;
      }
      local_total_amount =
        parseFloat(local_total_amount) + parseFloat(my_value);
    });
    return local_total_amount;
  }
  function Calculate_Rmc_Commission_Cooli(rate_id, rate_value) {
    var rate_id = rate_id;
    var rate_value = rate_value;
    var res = rate_id.split("_");
    var net_weight = `#` + res[0] + `_net_weight`;
    var net_weight_value = $(net_weight).val();

    var amount = parseFloat((rate_value * 2 * net_weight_value) / 100).toFixed(
      2
    );

    $(`#` + res[0] + `_amount`).val(amount);

    var global_amount = parseFloat(
      get_total_amount_from_sales_entry_form()
    ).toFixed(2);

    rmc_input_box.val(parseFloat(global_amount * 0.006).toFixed(2));
    commission_input_box.val(parseFloat(global_amount * 0.05).toFixed(2));

    var rmc_value = parseFloat(rmc_input_box.val()).toFixed(2);
    var comission_value = parseFloat(commission_input_box.val()).toFixed(2);
    var cooli_value = parseFloat(cooli_input_box.val()).toFixed(2);
    if (cooli_value.length <= 0 || isNaN(cooli_value)) {
      cooli_value = 0;
    }

    var final_value =
      parseFloat(rmc_value) +
      parseFloat(comission_value) +
      parseFloat(cooli_value) +
      parseFloat(global_amount);

    total_amount.val(parseFloat(final_value).toFixed(2));
    paid_amount.val(parseFloat(final_value).toFixed(2));
    balance_amount.val(0);
  }

  function Calculate_Cooli() {
    var global_amount = parseFloat(
      get_total_amount_from_sales_entry_form()
    ).toFixed(2);

    rmc_input_box.val(parseFloat(global_amount * 0.006).toFixed(2));
    commission_input_box.val(parseFloat(global_amount * 0.05).toFixed(2));

    var rmc_value = parseFloat(rmc_input_box.val()).toFixed(2);
    var comission_value = parseFloat(commission_input_box.val()).toFixed(2);
    var cooli_value = parseFloat(cooli_input_box.val()).toFixed(2);
    if (cooli_value.length <= 0 || isNaN(cooli_value)) {
      cooli_value = 0;
    }

    var final_value =
      parseFloat(rmc_value) +
      parseFloat(comission_value) +
      parseFloat(cooli_value) +
      parseFloat(global_amount);

    total_amount.val(parseFloat(final_value).toFixed(2));
    paid_amount.val(parseFloat(final_value).toFixed(2));
    balance_amount.val(0);
  }

  $(document).on("keyup change,", "#paid_amount", function () {
    var paid_amount = $(this).val();
    var total_amount = $("#total_amount").val();
    var result =
      parseFloat(total_amount).toFixed(2) - parseFloat(paid_amount).toFixed(2);
    balance_amount.val(parseFloat(result).toFixed(2));
  });

  $(document).on("change", ".add_new_sales_custom_select", function () {
    var lot_number_Id = $(this).attr("id");
    var selected_lot = $(this).val();

    var res = lot_number_Id.split("_");
    var item_name = `#` + res[0] + `_item_name`;
    var item_qty = `#` + res[0] + `_qty`;
    var item_list = "";

    $.ajax({
      url: "/get_arrival_goods_item_name",
      dataType: "json",
      data: {
        selected_lot: selected_lot,
      },
      type: "GET",
      async: false,
      cache: false,
      timeout: 90000,
      success: function (data) {
        item_list = data.item_name_list;
      },
      error: function () {
        console.log("error");
      },
    });

    for (var [key, value] of Object.entries(item_list)) {
      $(item_name).val(key);
      $(item_qty).val(value);
    }
  });

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

  $(document).on("submit", "#sales_entry_form", function (e) {
    var item_goods_list = "";
    ("use strict");

    $.ajax({
      url: "/get_arrival_goods_api",
      dataType: "json",
      data: {},
      type: "GET",
      async: false,
      cache: false,
      timeout: 90000,
      fail: function () {
        item_goods_list = "";
      },
      success: function (data) {
        item_goods_list = data;
      },
    });

    var balance_qty = 0;
    for (var [key, value] of Object.entries(item_goods_list)) {
      balance_qty = balance_qty + value;
    }

    var bag_total = 0;
    var ZERO_FLAG = false;
    $(".sales_bag_count").each(function (index, element) {
      var my_value = parseInt($(element).val());
      if (Number.isNaN(my_value)) {
        my_value = 0;
      }
      if (my_value == 0) {
        ZERO_FLAG = true;
      }
      bag_total = bag_total + my_value;
    });

    if (ZERO_FLAG == true) {
      alert("Cannot have ZERO as Qty for the item..!");
    } else {
      if (balance_qty - bag_total <= 0) {
        console.log("Ready to SUBMIT .. !");
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
