class TooltipManager {
  constructor() {
    this.initTooltipTriggers();
  }

  initTooltipTriggers() {
    document.addEventListener("mouseover", (event) => {
      if (event.target.classList.contains("tooltip-trigger")) {
        this.showTooltip(event);
      }
    });

    document.addEventListener("mouseout", (event) => {
      if (event.target.classList.contains("tooltip-trigger")) {
        this.hideTooltip(event);
      }
    });
  }

  async showTooltip(event) {
    const id = event.target.getAttribute("data-tooltip");
    let tableData = "";

    try {
      tableData = await this.createTableData(id);
      console.log("Table HTML:", tableData);
    } catch (error) {
      console.error("Error creating table data:", error);
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
    if (container) {
      container.appendChild(tooltip);
      setTimeout(() => tooltip.classList.add("active"), 10);
    }
  }

  hideTooltip(event) {
    const container = event.target.closest(".tooltip-container");
    const tooltip = container ? container.querySelector(".tooltip") : null;
    if (tooltip) {
      tooltip.classList.remove("active");
      setTimeout(() => tooltip.remove(), 200);
    }
  }

  getCreditBillEntryList(id) {
    return new Promise((resolve, reject) => {
      $.ajax({
        url: "/get_credit_bill_entry_list",
        method: "GET",
        async: true,
        data: { id: id },
        success: function (response) {
          console.log("AJAX request successful:", response);
          resolve(response);
        },
        error: function (xhr, status, error) {
          console.error("Get Credit Bill Entry request failed:", status, error);
          reject(error);
        },
      });
    });
  }

  async createTableData(id) {
    try {
      const response = await this.getCreditBillEntryList(id);
      console.log("Response from AJAX call:", response);

      let tableHTML =
        "<thead><tr><th>Payment&nbsp;Date</th><th>Amount</th><th>Payment Mode</th></tr></thead><tbody>";
      response.forEach((item) => {
        tableHTML += `<tr><td>${item.date}</td><td>${item.amount}/-</td><td>${item.payment_mode}</td></tr>`;
      });
      tableHTML += "</tbody>";

      return tableHTML;
    } catch (error) {
      console.error("Error fetching table data:", error);
      throw error;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  new TooltipManager();
});
