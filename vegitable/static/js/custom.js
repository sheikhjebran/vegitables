"use strict";

$(document).ready(function () {
  //Sales entry variable
  const rates_input_boxs = $(".calculate_amount");
  const rmc_input_box = $("#rmc");
  const commission_input_box = $("#comission");
  const cooli_input_box = $("#cooli");
  const total_amount = $("#total_amount");
  const amount_validation = $(".amount_validation");
  const paid_amount = $("#paid_amount");
  const balance_amount = $("#balance_amount");

  // Report entry variable
  const report_main_option = $(".report_choice");

  var global_amount = 0;
  var counter = 1;
  var arrival_qty_list = {};
  var global_weight = 0;
  var local_amount = {};
  var local_weight = {};

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

    var amount = parseFloat((rate_value * 2 * net_weight_value) / 100).toFixed(2);

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
    var result = parseFloat(total_amount).toFixed(2) - parseFloat(paid_amount).toFixed(2);
    balance_amount.val(parseFloat(result).toFixed(2));
  });



   $(document).on("change keyup","#shilk_date", function () {
        var selected_date = $(this).val();
        $.ajax({
          url: "/retrieve_shilk",
          method: "GET",
          async: true,
          data: {
            selected_date: selected_date,
          },
          success: function (response) {
            console.log("AJAX request successful");
            update_shilk_form(response.result)
          },
          error: function (xhr, status, error) {
            console.log("AJAX request failed");
            console.log("Status: " + status);
            console.log("Error: " + error);
          },
        });
   });

   function update_shilk_form(result){
    $("#shilk_arrival").val(result["total_bags_sum"]);
    $("#shilk_bags_sold").val(result["bags_sold_sum"]);
    $("#shilk_balance").val(result["balance_bags_sum"]);
    $("#shilk_total_sales").val(result["total_sales"]);
    $("#shilk_cash_bill_amount").val(result["cash_bill_amount"]);
    $("#shilk_collection").val(result["collection"]);
    $("#shilk_credit_bill_amount").val(result["credit_bill_amount"]);
    $("#shilk_expenses").val(result["total_expenditure"]);
    $("#shilk_net_amount").val(result["net_amount"]);
    $("#shilk_phone_pay").val(result["upi_amount"]);
    $("#shilk_patti").val(result["patti_amount"]);
   }


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

  $("#add_arrivel_entry_list").click(function () {
    $("#tableWrapper")
      .children("tbody")
      .last()
      .append(
        `
            <tr style='margin-top:3%;margin-bottom:3%;' id ="` +
          counter +
          `_child">
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Former Name' name ="` +
          counter +
          `_farmer_name" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>

                        <select  name ="` +
          counter +
          `_item_name" id ="` +
          counter +
          `_item_name">
                                    <option value="Onion">Onion</option>
                                    <option selected="true"value="Potato">Potato</option>
                                    <option value="Ginger">Ginger</option>
                                    <option value="Garlic">Garlic</option>
                                </select>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Qty'  id ="` +
          counter +
          `_qty" name ="` +
          counter +
          `_qty" class="qty_validation number_only" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Weight' name ="` +
          counter +
          `_weight" class="decimal_number_only" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Lot Number' name ="` +
          counter +
          `_remark" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' class="decimal_number_only" placeholder='Advance Amount' value="0" name ="` +
          counter +
          `_advance_amount" required=''>
                    </div>
                </td>
                <td>
                    <div class='tog-top-4'>
                        <img class='close_button' src="/static/images/remove.png" name="` +
          counter +
          `"/>
                        </div>
                </td>
            </tr>
            `
      );
    counter = counter + 1;
  });

  $(document).on("keyup", ".qty_validation", function () {
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
    if (total > parseInt($("#total_number_of_bags").val())) {
      alert("Number of bags are more than Arrival bag count !");
      $(this).val("");
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

  $(document).on("keyup", ".sales_bag_count", function () {
    var bag_count = 0;
    var bag_id = $(this).attr("name");

    var res = bag_id.split("_");
    var qty = `#` + res[0] + `_qty`;


    var elements = document.querySelectorAll('.add_new_sales_custom_select');
    elements.forEach(function(element) {
        // Get the 'id' or 'name' attribute of the element
        var idAttr = element.getAttribute('id');     // Same logic can apply to the 'id'
        // Extract the dynamic number part before '_lot_number' in 'name' or 'id'
        var dynamicNumberFromId = idAttr.split('_')[0];     // Extract number from 'id'
        if($(`#`+dynamicNumberFromId+`_lot_number`).val() == $(`#`+res[0]+`_lot_number`).val()){
            bag_count =  bag_count + parseInt($(`#`+dynamicNumberFromId+`_bags`).val());
        }
    });


    if (parseInt(bag_count) > parseInt($(qty).val())) {
      alert($(qty).val() + " : Bags in inventory");
      $(this).val("");
    }
  });

  $(document).on("click", "#add_sales_entry_list", function () {
    var item_goods_list = "";
    ("use strict");

    $.ajax({
      url: "/get_arrival_goods_list",
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
        item_goods_list = data.item_goods_list;
      },
    });

    var select_option =
      '<option selected="true" disabled="disabled">Choose Lot No</option>';
    for (var [key, value] of Object.entries(item_goods_list)) {
      select_option =
        select_option + "<option value='" + key + "'>" + value + "</option>";
    }

    $("#tableWrapper")
      .children("tbody")
      .last()
      .append(
        `
        <tr style='margin-top:3%;margin-bottom:3%;' id ="` +
          counter +
          `_child">
        <td>
            <div class='comment-your'>
                <select class="add_new_sales_custom_select" name="` +
          counter +
          `_lot_number" id ="` +
          counter +
          `_lot_number">
                    ` +
          select_option +
          `
                </select>
                
            </div>
        </td>

        <td>
            <div class='comment-your'>
                <input type='text' placeholder='item Name' name ="` +
          counter +
          `_item_name" id="` +
          counter +
          `_item_name" required='' readonly>
                <input type='text' placeholder='qty' name ="` +
          counter +
          `_qty" id="` +
          counter +
          `_qty" required='' readonly hidden>
            </div>
        </td>
        
        <td>
            <div class='comment-your'>
                <input type='text' placeholder='Bags' class= "sales_bag_count number_only" name ="`+
                counter+
                `_bags" id="`+
                counter+
                `_bags" required=''>
            </div>
        </td>
        <td>
            <div class='comment-your'>
                <input type='text' placeholder='Net Weight' class= "decimal_number_only" name ="` +
          counter +
          `_net_weight" id="` +
          counter +
          `_net_weight" required=''>
            </div>
        </td>
        <td>
            <div class='comment-your'>
                <input type='text' placeholder='Rates' name ="` +
          counter +
          `_rates" required='' id= "` +
          counter +
          `_rates" class="calculate_amount decimal_number_only">
            </div>
        </td>
        <td>
            <div class='comment-your'>
                <input type='text' placeholder='Amount' class= "amount_validation decimal_number_only" name ="` +
          counter +
          `_amount" id= "` +
          counter +
          `_amount" required='' readonly>
            </div>
        </td>
        <td>
            <div class='tog-top-4'>
                <img class='close_button' src="/static/images/remove.png" onClick="removeElement('` +
          counter +
          `_child');"/>
             </div>
        </td>
    </tr>
            `
      );
    counter = counter + 1;
  });

  $(document).on("change", "#patti_entry_date", function () {
    var lorry_list = "";
    ("use strict");

    var element_value = $(this).val();

    $.ajax({
      url: "/get_all_lorry_number/" + element_value,
      dataType: "json",
      data: {},
      type: "GET",
      async: false,
      cache: false,
      timeout: 90000,
      fail: function () {
        lorry_list = "";
      },
      success: function (data) {
        lorry_list = data.lorry_number_list;
      },
    });

    var select_option =
      '<option selected="true" disabled="disabled">Choose Lorry Number</option>';
    for (var index = 0; index < lorry_list.length; index++) {
      select_option =
        select_option +
        "<option value='" +
        lorry_list[index] +
        "'>" +
        lorry_list[index] +
        "</option>";
      console.log(lorry_list[index]);
    }

    $("#patti_lorry_number").children("option").remove();
    $("#patti_lorry_number").append(select_option);
  });

  $(document).on("change", "#patti_lorry_number", function () {
    var patti_farmer_list = "";
    ("use strict");

    var lorry_number_value = $(this).val();
    var patti_date_value = $("#patti_entry_date").val();

    $.ajax({
      url: "/get_all_farmer_name",
      dataType: "json",
      data: {
        lorry_number: lorry_number_value,
        patti_date: patti_date_value,
      },
      type: "GET",
      async: false,
      cache: false,
      timeout: 90000,
      fail: function () {
        patti_farmer_list = "";
      },
      success: function (data) {
        patti_farmer_list = data.farmer_list;
      },
    });

    var select_option =
      '<option selected="true" disabled="disabled">Choose Farmer Name</option>';
    for (var index = 0; index < patti_farmer_list.length; index++) {
      select_option =
        select_option +
        "<option value='" +
        patti_farmer_list[index] +
        "'>" +
        patti_farmer_list[index] +
        "</option>";
      console.log(patti_farmer_list[index]);
    }

    $("#patti_farmer_namer").children("option").remove();
    $("#patti_farmer_namer").append(select_option);
  });

  $(document).on("change", "#patti_farmer_namer", function () {
    var farmer_advance = 0;
    var patti_sales_entry_list = "";

    var patti_farmer_name_value = $(this).val();

    var patti_date_value = $("#patti_entry_date").val();

    var patti_lorry_value = $("#patti_lorry_number").val();

    $.ajax({
      url: "/get_sales_list_for_arrival_item_list",
      dataType: "json",
      data: {
        patti_farmer: patti_farmer_name_value,
        patti_date: patti_date_value,
        patti_lorry: patti_lorry_value,
      },
      type: "GET",
      async: false,
      cache: false,
      timeout: 90000,
      fail: function () {
        farmer_advance = 0;
        patti_sales_entry_list = "";
      },
      success: function (data) {
        patti_sales_entry_list = data.sales_goods_list;
        farmer_advance = data.farmer_advance;
      },
    });

    $("#advance_amount").val(farmer_advance);

    $("#tableWrapper").children("tbody").children("tr").remove();
    $("#total_weight").val(0);
    $("#net_amount").val(0);

        for (var index = 0; index < patti_sales_entry_list.length; index++) {
      $("#tableWrapper")
        .children("tbody")
        .last()
        .append(
          `
                    <tr style='margin-top:3%;margin-bottom:3%;' id ="` +
            counter +
            `_child">
                                    <td>
                                        <div class='comment-your'>
                                            <input type='text' placeholder='item Name' name ="` +
            counter +
            `_item_name" id="` +
            counter +
            `_item_name" value="` +
            patti_sales_entry_list[index]["item_name"] +
            `" required='' readonly>
                                            
                                        </div>
                                    </td>

                                    <td>
                                        <div class='comment-your'>
                                            <input type='text' placeholder='Bag Mark' name ="` +
            counter +
            `_lot_number" id="` +
            counter +
            `_lot_number" value="` +
            patti_sales_entry_list[index]["lot_number"] +
            `" required='' readonly>
                                        </div>
                                    </td>

                                    <td>
                                        <div class='comment-your'>
                                            <input type='text' placeholder='Sold Bag' name ="` +
            counter +
            `_sold_bag" id="` +
            counter +
            `_sold_bagr" value="` +
            patti_sales_entry_list[index]["sold_qty"] +
            `" required='' readonly>
                                        </div>
                                    </td>

                                    <td>
                                        <div class='comment-your'>
                                            <input type='text' placeholder='Balance Bag' name ="` +
            counter +
            `_balance_bag" id="` +
            counter +
            `_balance_bag" value="` +
            patti_sales_entry_list[index]["arrival_qty"] +
            `" required='' readonly>
                                        </div>
                                    </td>
                                    
                                    <td>
                                        <div class='comment-your'>
                                            <input type='text' placeholder='Weight' class= "patti_weight decimal_number_only" name ="` +
            counter +
            `_weight" id ="` +
            counter +
            `_weight" value="` +
            patti_sales_entry_list[index]["net_weight"] +
            `" required=''>
                                        </div>
                                    </td>
                                    <td>
                                        <div class='comment-your'>
                                            <input type='text' placeholder='Rate' class="patti_rate decimal_number_only" name ="` +
            counter +
            `_rate" id="` +
            counter +
            `_rate" value="` +
            patti_sales_entry_list[index]["rates"] +
            `"required=''>
                                        </div>
                                    </td>
                                    <td>
                                        <div class='comment-your'>
                                            <input type='text' placeholder='Amount' class= "patti_amount decimal_number_only" name ="` +
            counter +
            `_amount" required='' id= "` +
            counter +
            `_amount" value="` +
            patti_sales_entry_list[index]["amount"] +
            `">
                                        </div>
                                    </td>
                                </tr>
                                `
        );
      counter = counter + 1;
    }
    calculate_patti_total_weight_and_amount();

  });

  $(document).on("keyup", ".patti_weight", function () {
    var weight_id = $(this).attr("id");
    var weight_value = $(this).val();
    var res = weight_id.split("_");

    var local_patti_weight = 0;
    $(".patti_weight").each(function (index, element) {
      var my_value = parseFloat($(element).val());
      if (Number.isNaN(my_value)) {
        my_value = 0;
      }
      local_patti_weight = local_patti_weight + my_value;
    });
    $("#total_weight").val(local_patti_weight);

    var rate_value = $(`#` + res[0] + `_rate`).val();
    var amount = (rate_value * 2 * weight_value) / 100;

    $(`#` + res[0] + `_amount`).val(amount);

    var advance_amount = $("#advance_amount").val();
    var hamali = $("#hamali").val();
    if (Number.isNaN(hamali) || hamali.value === "") {
      hamali = 0;
    }

    $("#total_weight").val(local_patti_weight);

    var local_patti_amount = 0;
    $(".patti_amount").each(function (index, element) {
      var my_value = parseFloat($(element).val());
      if (Number.isNaN(my_value) || my_value.value === "") {
        my_value = 0;
      }
      local_patti_amount = local_patti_amount + my_value;
    });

    $("#net_amount").val(
      parseFloat(local_patti_amount) - parseFloat(advance_amount)
    ) - parseFloat(hamali);
  });

  $(document).on("keyup", ".patti_rate", function () {
    var rate_id = $(this).attr("id");
    var rate_value = $(this).val();

    var res = rate_id.split("_");

    var local_patti_weight = 0;
    $(".patti_weight").each(function (index, element) {
      var my_value = parseFloat($(element).val());
      if (Number.isNaN(my_value)) {
        my_value = 0;
      }
      local_patti_weight = local_patti_weight + my_value;
    });

    var local_patti_rate = 0;
    $(".patti_rate").each(function (index, element) {
      var my_value = parseFloat($(element).val());
      if (Number.isNaN(my_value)) {
        my_value = 0;
      }
      local_patti_rate = local_patti_rate + my_value;
    });

    var current_weight_single_entry = $(`#` + res[0] + `_weight`).val();
    var amount = (rate_value * 2 * current_weight_single_entry) / 100;

    $(`#` + res[0] + `_amount`).val(amount);

    var advance_amount = $("#advance_amount").val();
    var hamali = $("#hamali").val();

    $("#total_weight").val(local_patti_weight);

    var local_patti_amount = 0;
    $(".patti_amount").each(function (index, element) {
      var my_value = parseFloat($(element).val());
      if (Number.isNaN(my_value)) {
        my_value = 0;
      }
      local_patti_amount = local_patti_amount + my_value;
    });

    $("#net_amount").val(
      parseFloat(local_patti_amount) -
        parseFloat(advance_amount) -
        parseFloat(hamali)
    );
  });

    function calculate_patti_total_weight_and_amount(){
        var local_patti_amount = 0;
        $(".patti_amount").each(function (index, element) {
          var my_value = parseFloat($(element).val());
          if (Number.isNaN(my_value)) {
            my_value = 0;
          }
          local_patti_amount = local_patti_amount + my_value;
        });

        var local_patti_weight = 0;
        $(".patti_weight").each(function (index, element) {
          var my_value = parseFloat($(element).val());
          if (Number.isNaN(my_value)) {
            my_value = 0;
          }
          local_patti_weight = local_patti_weight + my_value;
        });

        var advance_amount = $("#advance_amount").val();
        var hamali = $("#hamali").val();

        $("#total_weight").val(local_patti_weight);
        $("#net_amount").val(
          parseFloat(local_patti_amount) -
            parseFloat(advance_amount) -
            parseFloat(hamali)
        );
    }
  $(document).on("keyup", "#hamali", function () {
    calculate_patti_total_weight_and_amount();
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

    function validate_credit_bill_amount_received(){
        var balance = parseFloat($(".balance_amount").val());
        var amountReceived = parseFloat($(".amount_received").val());
        var discount = parseFloat($(".discount").val());

        // Set discount to 0 if it's empty
        if (isNaN(discount)) {
          discount = 0;
        }

        if(discount+amountReceived>balance){
            $(".amount_received").val("");
            $(".discount").val("");
            alert("Received amount cannot exceed Balance Amount ..!");
        }
    }
   $(document).on("input",".amount_received",function(){
        validate_credit_bill_amount_received();
   });

   $(document).on("input",".discount",function(){
        validate_credit_bill_amount_received();
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
      } else {
        //if (confirm("Would you like to add more item ? ") == true) {
          //e.preventDefault();
          //$("#add_sales_entry_list").trigger("click");
        //} else {
          //text = "You canceled!";
        //}
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
      async: true,
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

  arrival_entry_lorry_number.on(
    "keyup change",
    ValidateLorryEntryOnArrivalEntry
  );
  arrival_entry_date.on("keyup change", ValidateLorryEntryOnArrivalEntry);



    // Customer ledger
  const customer_ledger_table = $(".custom-table-div");
  const search_result_not_found_text = $(".search-result");

  function hide_show_customer_ledger_table(condition){
    if(condition){
        customer_ledger_table.show();
        $(".search-result").hide();
        $(".search-result").removeClass('show').addClass('hidden');

    }else{
        customer_ledger_table.hide();
        $(".search-result").show();
        $(".search-result").removeClass('hidden').addClass('show');
    }
  }

  function update_customer_ledger_table(result){
    $("#tableWrapper").children("tbody").children("tr").remove();
    for (var index = 0; index < result.length; index++) {
        $("#tableWrapper")
          .children("tbody")
          .last()
          .append(`
            <tr>
                    <td><a href="/edit_customer_ledger_entry/`+result[index].id+`">`+result[index].id+`</a></td>
                    <td>`+result[index].name+`</td>
                    <td>`+result[index].contact+`</td>
                    <td>`+result[index].address+`</td>
            </tr>
          `);
    }
  }

  function update_farmer_ledger_table(result){
    $("#tableWrapper").children("tbody").children("tr").remove();
    for (var index = 0; index < result.length; index++) {
        $("#tableWrapper")
          .children("tbody")
          .last()
          .append(`
            <tr>
                    <td><a href="/edit_farmer_ledger_entry/`+result[index].id+`">`+result[index].id+`</a></td>
                    <td>`+result[index].name+`</td>
                    <td>`+result[index].contact+`</td>
                    <td>`+result[index].place+`</td>
            </tr>
          `);
    }
  }

  $(document).on("keyup", ".customer_ledger_search_text", function () {
    var search_text = $(this).val();
    if(search_text.length >= 3){
    $.ajax({
      url: "/search_customer_ledger",
      method: "GET",
      async: true,
      data: {
        search_text: search_text,
      },
      success: function (response) {
        console.log("AJAX request successful");
        hide_show_customer_ledger_table(response.FOUND);
        update_customer_ledger_table(response.result);
      },
      error: function (xhr, status, error) {
        console.log("AJAX request failed");
        console.log("Status: " + status);
        console.log("Error: " + error);
        hide_show_customer_ledger_table(null)
      },
    });
    }
    if(search_text.length<=0){
    $.ajax({
      url: "/default_customer_ledger",
      method: "GET",
      async: true,
      data: {
        search_text: search_text,
      },
      success: function (response) {
        console.log("AJAX request successful");
        hide_show_customer_ledger_table(response.FOUND);
        update_customer_ledger_table(response.result);
      },
      error: function (xhr, status, error) {
        console.log("AJAX request failed");
        console.log("Status: " + status);
        console.log("Error: " + error);
        hide_show_customer_ledger_table(null)
      },
    });
   }

  });

   $(document).on("mouseenter", ".credit_id", function () {
        var text = $(this).attr("value");
        var amount_balance = $(this).attr("amount_balance");
        console.log(text);
        console.log(amount_balance);
        $("#popup").css({
            'display':"block"
        });

        $(".overlay").css({
            'display':"block"
        });
        $(".sales_bill_id").val(text);
        $(".balance_amount").val(amount_balance);
   });

   $(document).on("click", ".popup_close", function () {
        $(".overlay").css({
            'display':"none",
            'position': "fixed"
        });
        $("#popup").css({
            'display':"none"
        });
   });


  $(document).on("keyup", ".farmer_ledger_search_text", function () {
    var search_text = $(this).val();
    if(search_text.length >= 3){
    $.ajax({
      url: "/search_farmer_ledger",
      method: "GET",
      async: true,
      data: {
        search_text: search_text,
      },
      success: function (response) {
        console.log("AJAX request successful");
        hide_show_customer_ledger_table(response.FOUND);
        update_farmer_ledger_table(response.result);
      },
      error: function (xhr, status, error) {
        console.log("AJAX request failed");
        console.log("Status: " + status);
        console.log("Error: " + error);
        hide_show_customer_ledger_table(null)
      },
    });
    }
    if(search_text.length<=0){
    $.ajax({
      url: "/default_farmer_ledger",
      method: "GET",
      async: true,
      data: {
        search_text: search_text,
      },
      success: function (response) {
        console.log("AJAX request successful");
        hide_show_customer_ledger_table(response.FOUND);
        update_farmer_ledger_table(response.result);
      },
      error: function (xhr, status, error) {
        console.log("AJAX request failed");
        console.log("Status: " + status);
        console.log("Error: " + error);
        hide_show_customer_ledger_table(null)
      },
    });


   }

  });

  // Report
  const report_sales_entry_selected = $(".sales_bill_report");

  function update_sales_bill_report_table(result){
      $("#tableWrapper").children("tbody").children("tr").remove();
        for (var index = 0; index < result.length; index++) {
            $("#tableWrapper")
              .children("tbody")
              .last()
              .append(`
                <tr>
                        <td>`+result[index].id+`</td>
                        <td>`+result[index].customer_name+`</td>
                        <td>`+result[index].item_name+`</td>
                        <td>`+result[index].bags+`</td>
                        <td>`+result[index].amount+`</td>
                        <td>`+result[index].balance+`</td>
                        <td>`+result[index].payment_type+`</td>
                </tr>
              `);
        }
    }
  function CheckSalesBill_Report(){
    $.ajax({
      url: "/report_sales_bill",
      method: "GET",
      async: true,
      data: {
        date: $(this).val()
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


   $(document).on("change", ".daily_rmc_date", function () {
        var selected_date = this.value;
        getDailyRmcForSelectedDate(selected_date);
   });

    function getDailyRmcForSelectedDate(selectedDate){
    $.ajax({
      url: "/get_daily_rmc_selected_date",
      method: "GET",
      async: true,
      data: {
        date: selectedDate
      },
      success: function (response) {
        console.log("AJAX request successful");
        update_daily_rmc_container(response);
      },
      error: function (xhr, status, error) {
        console.log("AJAX request failed");
        console.log("Status: " + status);
        console.log("Error: " + error);

      },
    });
  }

  function update_daily_rmc_container(response){
    if(response.FOUND){
        $(".daily_report_container").css("visibility", "show");
        $(".weekly_report_container").css("visibility", "hidden");
        $(".daily_report_table_cash").children("tbody").children("tr").remove();
        $(".daily_report_table_credit").children("tbody").children("tr").remove();

        var data = response.result;
        let tableHTMLCash = "<tbody>";
        let tableHTMLCredit = "<tbody>";
        let cash_counter = 0;
        let credit_counter = 0;

        if(data.length==0){
        $(".daily_report_container").css("visibility", "hidden");
        }else{
        data.forEach(item => {
            if(item.payment_type=="credit"){
            tableHTMLCredit += `
            <tr>
                <td>${item.entry_id}</td>
                <td>${item.bags}/-</td>
                <td>${item.paid_amount}</td>
                <td>${item.rmc}</td>
            </tr>`;
            credit_counter = credit_counter + 1;
            }else{
            tableHTMLCash += `
            <tr>
                <td>${item.entry_id}</td>
                <td>${item.bags}/-</td>
                <td>${item.paid_amount}</td>
                <td>${item.rmc}</td>
            </tr>`;
            cash_counter = cash_counter + 1;
            }
        });
        tableHTMLCash += "</tbody>";
        tableHTMLCredit += "</tbody>";
         $(".daily_report_table_cash").append(tableHTMLCash);
         $('.daily_report_table_credit').append(tableHTMLCredit);
        }

    }else{
        $(".daily_report_container").css("visibility", "hidden");
        $(".daily_report_table_cash").children("tbody").children("tr").remove();
        $(".daily_report_table_credit").children("tbody").children("tr").remove();
    }
  }

    $(document).on("click",".rmc_daily_button",function(){
        $(".daily_report_date").show();
        $(".daily_report_container").show();
        $(".weekly_report_date").hide();
    });
    $(document).on("click",".rmc_weekly_button",function(){
        $(".daily_report_date").hide();
        $(".daily_report_container").hide();
        $(".weekly_report_date").show();
    });

    $(document).on("change", ".weekly_rmc_start_date", function () {
        var start_date = this.value;
        var end_date = $(".weekly_rmc_end_date").val();
        if (end_date == "") {
            console.log("The EndDate value is undefined");
        }else{
            getWeeklyRmcForSelectedDate(start_date, end_date);
        }


   });
   $(document).on("change", ".weekly_rmc_end_date", function () {
        var end_date = this.value;
        var start_date = $(".weekly_rmc_start_date").val();
        if (start_date == "") {
            console.log("The StartDate value is undefined");
        }else{
            getWeeklyRmcForSelectedDate(start_date, end_date);
        }
   });

    function getWeeklyRmcForSelectedDate(start_date=null, end_date=null){
        $.ajax({
              url: "/get_daily_rmc_start_and_end_date",
              method: "GET",
              async: true,
              data: {
                start_date: start_date,
                end_date: end_date
              },
              success: function (response) {
                console.log("AJAX request successful");
                update_weekly_rmc_container(response);
              },
              error: function (xhr, status, error) {
                console.log("AJAX request failed");
                console.log("Status: " + status);
                console.log("Error: " + error);

              },
            });
    }

    function update_weekly_rmc_container(response){
        if(response.FOUND){
            $(".daily_report_container").hide();
            $(".weekly_report_container").show();

            $(".weekly_rmc_report_table").children("tbody").children("tr").remove();

            var data = response.result;
            let tableHTML = "<tbody>";
            data.forEach(item => {
                tableHTML += `
                <tr>
                    <td>${item.Date}</td>
                    <td>${item.Total_Bags}</td>
                    <td>${item.Total_Amount}/-</td>
                    <td>${item.Total_Paid}/-</td>
                    <td>${item.Total_Balance}/-</td>
                    <td>${item.Total_RMC}</td>
                </tr>`;
            });
            tableHTML += "</tbody>";
            $(".weekly_rmc_report_table").append(tableHTML);
        }
    }




// Main code end's here
});

function removeElement(el) {
  console.log(el);

  var element = document.getElementById(el);

  element.remove();
}


// Tool tip Text
document.addEventListener("DOMContentLoaded", function() {
    const tooltipTriggers = document.querySelectorAll(".tooltip-trigger");

    tooltipTriggers.forEach(trigger => {
        trigger.addEventListener("mouseover", showTooltip);
        trigger.addEventListener("mouseout", hideTooltip);
    });

    async function showTooltip(event) {
        const id = event.target.getAttribute("data-tooltip");
        var tableData="";
        try {
            const response = await createTableData(id);
            console.log("Table HTML:", response);
            tableData= response;
            // Here you can use the 'response' to append the table to your desired element in the DOM or perform other operations
        } catch (error) {
            console.error("Error:", error);
            // Handle the error if necessary
        }


        const tooltipContent = document.createElement("div");
        tooltipContent.classList.add("tooltip-content");

        const table = document.createElement("table");
        table.classList.add("tooltip-table");
        table.innerHTML = tableData;

        tooltipContent.appendChild(table);

        const tooltip = document.createElement("div");
        tooltip.classList.add("tooltip");
        tooltip.appendChild(tooltipContent);

        const container = event.target.closest(".tooltip-container");
        container.appendChild(tooltip);
        setTimeout(() => tooltip.classList.add("active"), 10);
    }

    function hideTooltip(event) {
        const tooltip = event.target.closest(".tooltip-container").querySelector(".tooltip");
        if (tooltip) {
            tooltip.classList.remove("active");
            setTimeout(() => tooltip.remove(), 200);
        }
    }

    function getCreditBillEntryList(id) {
        return new Promise(function(resolve, reject) {
            $.ajax({
                url: "/get_credit_bill_entry_list",
                method: "GET",
                async: true,
                data: {
                    id: id
                },
                success: function (response) {
                    console.log("AJAX request successful");
                    console.log(response);
                    resolve(response);
                },
                error: function (xhr, status, error) {
                    console.log("Get Credit Bill Entry request failed");
                    console.log("Status: " + status);
                    console.log("Error: " + error);
                    reject(error);
                },
            });
        });
    }

    async function createTableData(id) {
    try {
            const response = await getCreditBillEntryList(id);
            // Use the response data here
            console.log("Response from AJAX call:", response);
            const creditData = response;
            const data = response;

            let tableHTML = "<thead><tr><th>Payment&nbsp;Date</th><th>Amount</th><th>PaymentMode</th></tr></thead><tbody>";

            data.forEach(item => {
                tableHTML += `<tr><td>${item.date}</td><td>${item.amount}/-</td><td>${item.payment_mode}</td></tr>`;
            });

            tableHTML += "</tbody>";
            return tableHTML;
        } catch (error) {
            console.error("Error from AJAX call:", error);
            throw error; // Re-throw the error so the caller can handle it
        }
    }
});
