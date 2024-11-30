class ShilkManager {
  constructor() {
    this.initializeEventListeners();
  }

  initializeEventListeners() {
    $(document).on("change keyup", "#shilk_date", (event) => {
      const selectedDate = $(event.currentTarget).val();
      this.retrieveShilkData(selectedDate);
    });
  }

  retrieveShilkData(selectedDate) {
    $.ajax({
      url: "/retrieve_shilk",
      method: "GET",
      async: true,
      data: { selected_date: selectedDate },
      success: (response) => {
        console.log("AJAX request successful");
        this.updateShilkForm(response.result);
      },
      error: (xhr, status, error) => {
        console.error("AJAX request failed");
        console.error("Status: " + status);
        console.error("Error: " + error);
      },
    });
  }

  updateShilkForm(result) {
    this.setValue("#shilk_arrival", result["total_bags_sum"]);
    this.setValue("#shilk_bags_sold", result["bags_sold_sum"]);
    this.setValue("#shilk_balance", result["balance_bags_sum"]);
    this.setValue("#shilk_total_sales", result["total_sales"]);
    this.setValue("#shilk_cash_bill_amount", result["cash_bill_amount"]);
    this.setValue("#shilk_collection", result["collection"]);
    this.setValue("#shilk_credit_bill_amount", result["credit_bill_amount"]);
    this.setValue("#shilk_expenses", result["total_expenditure"]);
    this.setValue("#shilk_net_amount", result["net_amount"]);
    this.setValue("#shilk_phone_pay", result["upi_amount"]);
    this.setValue("#shilk_patti", result["patti_amount"]);
    this.setValue("#shilk_cash_balance", result["cash_balance"]);
  }

  setValue(selector, value) {
    $(selector).val(value);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  new ShilkManager();
});
