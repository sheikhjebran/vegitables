class SalesEntry {
  constructor() {
    this.counter = 0; // Initialize counter
    this.paidAmount = document.getElementById("paid_amount");
    this.balanceAmount = document.getElementById("balance_amount");
    this.bindEvents();
  }

  // Bind events for the SalesEntry
  bindEvents() {
    this.setupAddSalesEntryClickHandler();
    this.setupSalesBagCountKeyupHandler();
    this.isCreditSelectedHandler();
  }

  // Check if Credit is Selected
  isCreditSelectedHandler() {
    const creditRadioButton = document.getElementById("sales_entry_credit");
    if (creditRadioButton) {
      // Add a click event listener to the Credit radio button
      creditRadioButton.addEventListener("click", (event) => {
        this.makePaidZeroAndUpdateBalance(event); // Optional: call your custom logic
      });
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
}

// Initialize the SalesEntry class when the document is ready
document.addEventListener("DOMContentLoaded", () => {
  new SalesEntry();
});
