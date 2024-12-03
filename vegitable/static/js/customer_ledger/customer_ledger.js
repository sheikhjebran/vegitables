class CustomerLedger {
  constructor() {
    this.customerLedgerTable = $(".custom-table-div");
    this.searchResultNotFoundText = $(".search-result");
    this.tableWrapper = $("#tableWrapper");
    this.searchInput = $(".customer_ledger_search_text");

    this.initializeEventListeners();
  }

  // Method to show or hide the customer ledger table
  toggleCustomerLedgerTable(condition) {
    if (condition) {
      this.customerLedgerTable.show();
      this.searchResultNotFoundText.hide().removeClass("show").addClass("hidden");
    } else {
      this.customerLedgerTable.hide();
      this.searchResultNotFoundText.show().removeClass("hidden").addClass("show");
    }
  }

  // Method to update the table with new results
  updateCustomerLedgerTable(result) {
    this.tableWrapper.children("tbody").children("tr").remove();
    result.forEach((customer) => {
      this.tableWrapper.children("tbody").last().append(`
        <tr>
          <td><a href="/edit_customer_ledger_entry/${customer.id}">${customer.id}</a></td>
          <td>${customer.name}</td>
          <td>${customer.contact}</td>
          <td>${customer.address}</td>
        </tr>
      `);
    });
  }

  // Method to perform an AJAX request
  performAjaxRequest(url, data, callback) {
    $.ajax({
      url: url,
      method: "GET",
      async: true,
      data: data,
      success: (response) => {
        console.log("AJAX request successful");
        this.toggleCustomerLedgerTable(response.FOUND);
        callback(response.result);
      },
      error: (xhr, status, error) => {
        console.log("AJAX request failed");
        console.log("Status: " + status);
        console.log("Error: " + error);
        this.toggleCustomerLedgerTable(null);
      },
    });
  }

  // Method to handle search input change
  handleSearchInputChange() {
    const searchText = this.searchInput.val();

    if (searchText.length >= 3) {
      this.performAjaxRequest("/search_customer_ledger", { search_text: searchText }, (result) => {
        this.updateCustomerLedgerTable(result);
      });
    } else if (searchText.length <= 0) {
      this.performAjaxRequest("/default_customer_ledger", { search_text: searchText }, (result) => {
        this.updateCustomerLedgerTable(result);
      });
    }
  }

  // Method to initialize event listeners
  initializeEventListeners() {
    this.searchInput.on("keyup", () => this.handleSearchInputChange());
  }
}

// Instantiate the class
$(document).ready(() => {
  new CustomerLedger();
});
