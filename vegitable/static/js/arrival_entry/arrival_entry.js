class ArrivalEntryManager {
  constructor() {
    this.counter = 1;
    this.tableWrapper = document.getElementById("tableWrapper");
    this.addButton = document.getElementById("add_arrivel_entry_list");
    this.totalBagsInput = document.getElementById("total_number_of_bags");
    this.saveButton = document.getElementById("save");

    this.initialize();
  }

  // Initialize event listeners
  initialize() {
    if (this.addButton) {
      this.addButton.addEventListener("click", () => this.addEntryRow());
    }

    // Delegate keyup events for quantity validation
    document.addEventListener("keyup", (event) => {
      if (event.target.classList.contains("qty_validation")) {
        this.validateQuantities(event.target);
      }
    });
  }

  // Create a new entry row
  addEntryRow() {
    const tbody = this.tableWrapper.querySelector("tbody:last-child");
    if (!tbody) {
      console.error("No tbody found in the table wrapper");
      return;
    }

    const newRow = document.createElement("tr");
    newRow.style.marginTop = "3%";
    newRow.style.marginBottom = "3%";
    newRow.id = `${this.counter}_child`;
    newRow.innerHTML = this.generateRowContent();

    tbody.appendChild(newRow);
    this.counter++;
  }

  // Generate the HTML content for a new row
  generateRowContent() {
    return `
      <td>
        <div class='comment-your'>
          <input type='text' placeholder='Farmer Name' name="${this.counter}_farmer_name" required=''>
        </div>
      </td>
      <td>
        <div class='comment-your'>
          <select name="${this.counter}_item_name" id="${this.counter}_item_name">
            <option value="Onion">Onion</option>
            <option selected="true" value="Potato">Potato</option>
            <option value="Ginger">Ginger</option>
            <option value="Garlic">Garlic</option>
          </select>
        </div>
      </td>
      <td>
        <div class='comment-your'>
          <input type='text' placeholder='Qty' id="${this.counter}_qty" name="${this.counter}_qty" class="qty_validation number_only" required=''>
        </div>
      </td>
      <td>
        <div class='comment-your'>
          <input type='text' placeholder='Weight' name="${this.counter}_weight" class="decimal_number_only" required=''>
        </div>
      </td>
      <td>
        <div class='comment-your'>
          <input type='text' placeholder='Lot Number' name="${this.counter}_remark" required=''>
        </div>
      </td>
      <td>
        <div class='comment-your'>
          <input type='text' class="decimal_number_only" placeholder='Advance Amount' value="0" name="${this.counter}_advance_amount" required=''>
        </div>
      </td>
      <td>
        <div class='tog-top-4'>
          <img class='close_button' src="/static/images/remove.png" name="${this.counter}"/>
        </div>
      </td>
    `;
  }

  // Validate total quantities
  validateQuantities(target) {
    let total = 0;
    const totalBags = parseInt(this.totalBagsInput?.value || 0);

    // Calculate total quantities
    document.querySelectorAll(".qty_validation").forEach((element) => {
      const value = parseInt(element.value) || 0;
      total += value;
    });

    // Show or hide save button
    if (total === totalBags) {
      this.saveButton?.classList.remove("hidden");
    } else {
      this.saveButton?.classList.add("hidden");
    }

    // Alert and reset if total exceeds
    if (total > totalBags) {
      alert("Number of bags are more than Arrival bag count!");
      target.value = "";
    }
  }
}

// Usage
document.addEventListener("DOMContentLoaded", () => {
  new ArrivalEntryManager();
});
