class SalesEntry {
  constructor() {
    this.creditRadioButton = document.querySelector("#sales_entry_credit");
    this.cashRadioButton = document.querySelector("#sales_enrty_cash");
    this.upiRadioButton = document.querySelector("#sales_entry_upi");
    this.balanceAmount = document.querySelector("#balance_amount");
    this.paidAmount = document.querySelector("#paid_amount");
    this.customerSelected = document.querySelector("#customerSelected");

    this.rmcInputBox = $("#rmc");
    this.commissionInputBox = $("#comission");
    this.cooliInputBox = $("#cooli");
    this.totalAmount = $("#total_amount");
    this.paidAmount = $("#paid_amount");
    this.balanceAmount = $("#balance_amount");

    this.bindEvents();
  }

  // Bind events for the SalesEntry
  bindEvents() {
    this.setupAddSalesEntryClickHandler();
    this.setupSalesBagCountKeyupHandler();
    this.isCreditSelectedHandler();
    this.isCustomerSelected();
    this.setupLotNumberChangeHandler();
    this.setupFormSubmitHandler();
    this.lotNoChangeHandler();
    this.setupCalculateAmountHandlers();
  }

  isCustomerSelected() {
    if (this.customerSelected) {
      this.customerSelected.addEventListener("change", (event) => {
        const selectedCustomer = $(event.target).val();
        $.ajax({
          url: "/get_mobile_customer_detail",
          method: "GET",
          async: true,
          data: {
            selectedCustomer: selectedCustomer,
          },
          success: (response) => {
            console.log("AJAX request successful");
            console.log(response);
            // code goes here
            this.addMobileSalesEntryRow(response);
          },
          error: (xhr, status, error) => {
            console.log("AJAX request failed");
            console.log("Status: " + status);
            console.log("Error: " + error);
          },
        });
      });
    }
  }

  addMobileSalesEntryRow(response) {
    this.counter = 0;
    $("#tableWrapper").children("tbody").empty();
    const data = response.data;
    data.forEach((rowGroup) => {
      rowGroup.forEach((item) => {
        console.log(
          `${item.former_name} supplied ${item.qty} units of ${item.item_name} with remarks: ${item.remarks}`
        );

        let select_option =
          '<option  disabled="disabled">Choose Lot No</option>';
        select_option += `<option selected="true" value='${item.id}'>${item.remarks}</option>`;

        let rowHtml = `
                <tr style='margin-top:3%;margin-bottom:3%;' id="${this.counter}_child">
                    <td>
                        <div class='comment-your'>
                            <select class="add_new_sales_custom_select" name="${this.counter}_lot_number" id="${this.counter}_lot_number">
                                ${select_option}
                            </select>
                        </div>
                    </td>
                    <td>
                        <div class='comment-your'>
                            <input type='text' placeholder='item Name' name="${this.counter}_item_name" id="${this.counter}_item_name" value="${item.item_name}" required='' readonly>
                            <input type='text' placeholder='qty' name="${this.counter}_qty" id="${this.counter}_qty" value="${item.qty}" required='' readonly hidden>
                        </div>
                    </td>
                    <td>
                        <div class='comment-your'>
                            <input type='text' placeholder='Bags' class="sales_bag_count number_only" name="${this.counter}_bags" value="${item.total_bags}" id="${this.counter}_bags" required=''>
                        </div>
                    </td>
                    <td>
                        <div class='comment-your'>
                            <input type='text' placeholder='Net Weight' class="decimal_number_only" name="${this.counter}_net_weight" value="${item.net_weight}" id="${this.counter}_net_weight" required=''>
                        </div>
                    </td>
                    <td>
                        <div class='comment-your'>
                            <input type='text' placeholder='Rates' name="${this.counter}_rates" required='' id="${this.counter}_rates" class="calculate_amount decimal_number_only">
                        </div>
                    </td>
                    <td>
                        <div class='comment-your'>
                            <input type='text' placeholder='Amount' class="amount_validation decimal_number_only" name="${this.counter}_amount" id="${this.counter}_amount" required='' readonly>
                        </div>
                    </td>
                    <td>
                        <div class='tog-top-4'>
                            <img class='close_button' src="/static/images/remove.png" onClick="removeElement('${this.counter}_child');"/>
                        </div>
                    </td>
                </tr>
            `;

        $("#tableWrapper").children("tbody").last().append(rowHtml);
        this.counter++;
      });
    });
  }

  // Check if Credit is Selected
  isCreditSelectedHandler() {
    if (this.creditRadioButton) {
      // Add a click event listener to the Credit radio button
      this.creditRadioButton.addEventListener("click", (event) => {
        this.makePaidZeroAndUpdateBalance(event);
      });
    } else {
      console.error("Credit radio button not found!");
    }
  }

  // Update Paid and Balance Amount when Credit is selected
  makePaidZeroAndUpdateBalance(event) {
    if (this.balanceAmount && this.paidAmount) {
      this.balanceAmount.value = this.paidAmount.value;
      this.paidAmount.value = 0;
    } else {
      console.error("Paid or Balance Amount fields are missing!");
    }
  }

  // Setup the click event handler for adding a sales entry
  setupAddSalesEntryClickHandler() {
    $(document).on("click", "#add_sales_entry_list", () => {
      this.addSalesEntryRow();
    });
  }

  // Setup the keyup event handler for .sales_bag_count
  setupSalesBagCountKeyupHandler() {
    $(document).on("keyup", ".sales_bag_count", function () {
      let bag_count = 0;
      const bag_id = $(this).attr("name");

      const res = bag_id.split("_");
      const qtySelector = `#${res[0]}_qty`;

      const elements = document.querySelectorAll(
        ".add_new_sales_custom_select"
      );
      elements.forEach((element) => {
        const idAttr = element.getAttribute("id");
        const dynamicNumberFromId = idAttr.split("_")[0];
        if (
          $(`#${dynamicNumberFromId}_lot_number`).val() ===
          $(`#${res[0]}_lot_number`).val()
        ) {
          const bagsValue =
            parseInt($(`#${dynamicNumberFromId}_bags`).val()) || 0;
          bag_count += bagsValue;
        }
      });

      const qtyValue = parseInt($(qtySelector).val()) || 0;
      if (bag_count > qtyValue) {
        alert(`${qtyValue} : Bags in inventory`);
        $(this).val(""); // Clear the input
      }
    });
  }

  // Setup the change event handler for lot number selection
  setupLotNumberChangeHandler() {
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
  }

  // Add a sales entry row to the table
  addSalesEntryRow() {
    let item_goods_list = "";

    $.ajax({
      url: "/get_arrival_goods_list",
      dataType: "json",
      data: {},
      type: "GET",
      async: false,
      cache: false,
      timeout: 90000,
      fail: () => {
        item_goods_list = "";
      },
      success: (data) => {
        item_goods_list = data.item_goods_list;
      },
    });

    let select_option =
      '<option selected="true" disabled="disabled">Choose Lot No</option>';
    for (let [key, value] of Object.entries(item_goods_list)) {
      select_option += `<option value='${key}'>${value}</option>`;
    }
    this.counter = 0; // Initialize counter
    let rowHtml = `
            <tr style='margin-top:3%;margin-bottom:3%;' id="${this.counter}_child">
                <td>
                    <div class='comment-your'>
                        <select class="add_new_sales_custom_select" name="${this.counter}_lot_number" id="${this.counter}_lot_number">
                            ${select_option}
                        </select>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='item Name' name="${this.counter}_item_name" id="${this.counter}_item_name" required='' readonly>
                        <input type='text' placeholder='qty' name="${this.counter}_qty" id="${this.counter}_qty" required='' readonly hidden>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Bags' class="sales_bag_count number_only" name="${this.counter}_bags" id="${this.counter}_bags" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Net Weight' class="decimal_number_only" name="${this.counter}_net_weight" id="${this.counter}_net_weight" required=''>
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Rates' name="${this.counter}_rates" required='' id="${this.counter}_rates" class="calculate_amount decimal_number_only">
                    </div>
                </td>
                <td>
                    <div class='comment-your'>
                        <input type='text' placeholder='Amount' class="amount_validation decimal_number_only" name="${this.counter}_amount" id="${this.counter}_amount" required='' readonly>
                    </div>
                </td>
                <td>
                    <div class='tog-top-4'>
                        <img class='close_button' src="/static/images/remove.png" onClick="removeElement('${this.counter}_child');"/>
                    </div>
                </td>
            </tr>
        `;

    $("#tableWrapper").children("tbody").last().append(rowHtml);
    this.counter++;
  }

  lotNoChangeHandler() {
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
  }

  setupFormSubmitHandler() {
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
  }

  setupCalculateAmountHandlers() {
    $(document).on("keyup change", ".calculate_amount", (event) => {
      var rate_id = $(event.target).attr("id");
      var rate_value = $(event.target).val();
      this.calculateRmcCommissionCooli(rate_id, rate_value);
    });

    $(document).on("keyup change", "#cooli", () => {
      this.calculateCooli();
    });

    $(document).on("keyup change", "#paid_amount", () => {
      var paid_amount = this.paidAmount.val();
      var total_amount = this.totalAmount.val();
      var result =
        parseFloat(total_amount).toFixed(2) -
        parseFloat(paid_amount).toFixed(2);
      this.balanceAmount.val(parseFloat(result).toFixed(2));
    });
  }
  calculateRmcCommissionCooli(rate_id, rate_value) {
    var res = rate_id.split("_");
    var net_weight = `#${res[0]}_net_weight`;
    var net_weight_value = $(net_weight).val();

    var amount = parseFloat((rate_value * 2 * net_weight_value) / 100).toFixed(
      2
    );
    $(`#${res[0]}_amount`).val(amount);

    var global_amount = parseFloat(
      this.getTotalAmountFromSalesEntryForm()
    ).toFixed(2);

    this.rmcInputBox.val(parseFloat(global_amount * 0.006).toFixed(2));
    this.commissionInputBox.val(parseFloat(global_amount * 0.05).toFixed(2));

    var rmc_value = parseFloat(this.rmcInputBox.val()).toFixed(2);
    var comission_value = parseFloat(this.commissionInputBox.val()).toFixed(2);
    var cooli_value = parseFloat(this.cooliInputBox.val()).toFixed(2);
    if (cooli_value.length <= 0 || isNaN(cooli_value)) {
      cooli_value = 0;
    }

    var final_value =
      parseFloat(rmc_value) +
      parseFloat(comission_value) +
      parseFloat(cooli_value) +
      parseFloat(global_amount);

    this.totalAmount.val(parseFloat(final_value).toFixed(2));
    this.paidAmount.val(parseFloat(final_value).toFixed(2));
    this.balanceAmount.val(0);
  }

  calculateCooli() {
    var global_amount = parseFloat(
      this.getTotalAmountFromSalesEntryForm()
    ).toFixed(2);

    this.rmcInputBox.val(parseFloat(global_amount * 0.006).toFixed(2));
    this.commissionInputBox.val(parseFloat(global_amount * 0.05).toFixed(2));

    var rmc_value = parseFloat(this.rmcInputBox.val()).toFixed(2);
    var comission_value = parseFloat(this.commissionInputBox.val()).toFixed(2);
    var cooli_value = parseFloat(this.cooliInputBox.val()).toFixed(2);
    if (cooli_value.length <= 0 || isNaN(cooli_value)) {
      cooli_value = 0;
    }

    var final_value =
      parseFloat(rmc_value) +
      parseFloat(comission_value) +
      parseFloat(cooli_value) +
      parseFloat(global_amount);

    this.totalAmount.val(parseFloat(final_value).toFixed(2));
    this.paidAmount.val(parseFloat(final_value).toFixed(2));
    this.balanceAmount.val(0);
  }

  getTotalAmountFromSalesEntryForm() {
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
}

document.addEventListener("DOMContentLoaded", () => {
  new SalesEntry();
});
