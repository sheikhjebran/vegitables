class FarmerLedger {
  constructor(tableWrapperSelector, searchInputSelector) {
    this.tableWrapper = $("#tableWrapper");
    this.searchInput = $(".farmer_ledger_search_text");
    this.init();
  }

  // Initialize the event listeners
  init() {
    this.searchInput.on("keyup", (event) => {
      this.handleSearch(event);
    });
  }

  // Handle the search functionality
  handleSearch(event) {
    const searchText = $(event.target).val();
    if (searchText.length >= 3) {
      this.searchFarmerLedger(searchText);
    } else if (searchText.length === 0) {
      this.loadDefaultFarmerLedger();
    }
  }

  // Perform the AJAX request for searching the farmer ledger
  searchFarmerLedger(searchText) {
    $.ajax({
      url: "/search_farmer_ledger",
      method: "GET",
      async: true,
      data: {
        search_text: searchText,
      },
      success: (response) => {
        console.log("AJAX request successful");
        this.updateTable(response.result);
        this.toggleTableVisibility(response.FOUND);
      },
      error: (xhr, status, error) => {
        console.log("AJAX request failed");
        console.log("Status: " + status);
        console.log("Error: " + error);
        this.toggleTableVisibility(null);
      },
    });
  }

  // Perform the AJAX request for loading the default farmer ledger
  loadDefaultFarmerLedger() {
    $.ajax({
      url: "/default_farmer_ledger",
      method: "GET",
      async: true,
      data: {},
      success: (response) => {
        console.log("AJAX request successful");
        this.updateTable(response.result);
        this.toggleTableVisibility(response.FOUND);
      },
      error: (xhr, status, error) => {
        console.log("AJAX request failed");
        console.log("Status: " + status);
        console.log("Error: " + error);
        this.toggleTableVisibility(null);
      },
    });
  }

  // Update the table with the new data
  updateTable(result) {
    this.tableWrapper.children("tbody").children("tr").remove();
    result.forEach((entry) => {
      this.tableWrapper.children("tbody").last().append(`
          <tr>
            <td><a href="/edit_farmer_ledger_entry/${entry.id}">${entry.id}</a></td>
            <td>${entry.name}</td>
            <td>${entry.contact}</td>
            <td>${entry.place}</td>
          </tr>
        `);
    });
  }

  // Show or hide the table based on the search result
  toggleTableVisibility(isVisible) {
    if (isVisible) {
      this.tableWrapper.show();
    } else {
      this.tableWrapper.hide();
    }
  }
}

// Initialize the SalesEntry class when the document is ready
document.addEventListener("DOMContentLoaded", () => {
  new FarmerLedger();
});
