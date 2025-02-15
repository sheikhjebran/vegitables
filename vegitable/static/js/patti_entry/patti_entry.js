class PattiHandler {
  constructor() {
    this.counter = 0;
    this.initEvents();
  }

  initEvents() {
    $(document).on(
      "change",
      "#patti_lorry_number",
      this.handleLorryChange.bind(this)
    );
    $(document).on(
      "change",
      "#patti_farmer_namer",
      this.handleFarmerChange.bind(this)
    );
    $(document).on(
      "keyup",
      ".patti_weight",
      this.handleWeightChange.bind(this)
    );
    $(document).on("keyup", ".patti_rate", this.handleRateChange.bind(this));
    $(document).on(
      "keyup",
      "#hamali",
      this.calculateTotalWeightAndAmount.bind(this)
    );
  }

  async fetchData(url, data) {
    try {
      const response = await $.ajax({
        url,
        dataType: "json",
        data,
        type: "GET",
        cache: false,
        timeout: 90000,
      });
      return response;
    } catch (error) {
      console.error("Error fetching data from", url, error);
      return null;
    }
  }

  async handleLorryChange() {
    const lorryNumber = $("#patti_lorry_number").val();
    const data = await this.fetchData("/get_all_farmer_name", {
      lorry_number: lorryNumber,
    });

    const farmerList = data?.farmer_list || [];
    const selectOptions = [
      `<option selected="true" disabled="disabled">Choose Farmer Name</option>`,
      ...farmerList.map(
        (farmer) => `<option value="${farmer}">${farmer}</option>`
      ),
    ].join("");

    $("#patti_farmer_namer").html(selectOptions);
  }

  async handleFarmerChange() {
    const farmerName = $("#patti_farmer_namer").val();
    const lorryNumber = $("#patti_lorry_number").val();
    const data = await this.fetchData("/get_sales_list_for_arrival_item_list", {
      patti_farmer: farmerName,
      patti_lorry: lorryNumber,
    });

    const salesList = data?.sales_goods_list || [];
    const farmerAdvance = data?.l || 0;
    $("#advance_amount").val(farmerAdvance);

    this.renderSalesEntries(salesList);
    this.calculateTotalWeightAndAmount();
  }

  renderSalesEntries(salesList) {
    const tableBody = document
      .getElementById("tableWrapper")
      .querySelector("tbody");
    tableBody.innerHTML = "";
    this.counter = 0;
    salesList.forEach((item) => {
      const row = document.createElement("tr");
      row.style.margin = "3% 0";
      row.id = `${this.counter}_child`;

      row.innerHTML = `
        <td>
          <div class="comment-your">
            <input type='text' placeholder='Item Name' name='${this.counter}_item_name' id='${this.counter}_item_name' value='${item.item_name}' required readonly>
          </div>
        </td>
        <td>
          <div class="comment-your">
          <input type='text' placeholder='Bag Mark' name='${this.counter}_lot_number' id='${this.counter}_lot_number' value='${item.lot_number}' required readonly>
          </div>
        </td>
        <td>
          <div class="comment-your">
            <input type='text' placeholder='Sold Bag' name='${this.counter}_sold_bag' id='${this.counter}_sold_bag' value='${item.sold_qty}' required readonly>
          </div>
        </td>
        <td>
          <div class="comment-your">
            <input type='text' placeholder='Balance Bag' name='${this.counter}_balance_bag' id='${this.counter}_balance_bag' value='${item.arrival_qty}' required readonly>
            
          </div>
        </td>
        <td>
          <div class="comment-your">
            <input type='text' placeholder='Weight' class='patti_weight decimal_number_only' name='${this.counter}_weight' id='${this.counter}_weight' value='${item.net_weight}' required>
          </div>
        </td>
        <td>
          <div class="comment-your">
            <input type='text' placeholder='Rate' class='patti_rate decimal_number_only' name='${this.counter}_rate' id='${this.counter}_rate' value='${item.rates}' required>
          </div>  
          </td>
        <td>
          <div class="comment-your">
            <input type='text' placeholder='Amount' class='patti_amount decimal_number_only' name='${this.counter}_amount' id='${this.counter}_amount' value='${item.amount}' required>
          </div>
        </td>
      `;

      tableBody.appendChild(row);
      this.counter++;
    });
  }

  handleWeightChange(event) {
    const weightId = $(event.target).attr("id");
    const weightValue = parseFloat($(event.target).val()) || 0;
    const [rowId] = weightId.split("_");

    const rateValue = parseFloat($(`#${rowId}_rate`).val()) || 0;
    const amount = (rateValue * 2 * weightValue) / 100;

    $(`#${rowId}_amount`).val(amount);
    this.calculateTotalWeightAndAmount();
  }

  handleRateChange(event) {
    const rateId = $(event.target).attr("id");
    const rateValue = parseFloat($(event.target).val()) || 0;
    const [rowId] = rateId.split("_");

    const weightValue = parseFloat($(`#${rowId}_weight`).val()) || 0;
    const amount = (rateValue * 2 * weightValue) / 100;

    $(`#${rowId}_amount`).val(amount);
    this.calculateTotalWeightAndAmount();
  }

  calculateTotalWeightAndAmount() {
    let totalWeight = 0;
    let totalAmount = 0;

    $(".patti_weight").each((_, element) => {
      totalWeight += parseFloat($(element).val()) || 0;
    });

    $(".patti_amount").each((_, element) => {
      totalAmount += parseFloat($(element).val()) || 0;
    });

    const advanceAmount = parseFloat($("#advance_amount").val()) || 0;
    const hamali = parseFloat($("#hamali").val()) || 0;

    $("#total_weight").val(totalWeight);
    $("#net_amount").val(totalAmount - advanceAmount - hamali);
  }
}

// Initialize the handler
$(document).ready(() => {
  new PattiHandler();
});
