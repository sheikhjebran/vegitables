class RmcReportManager {
  constructor() {
    this.initEventListeners();
  }

  initEventListeners() {
    $(document).on("click", ".rmc_daily_button", () => this.showDailyReport());
    $(document).on("click", ".rmc_weekly_button", () =>
      this.showWeeklyReport()
    );

    $(document).on("change", ".daily_rmc_date", (event) =>
      this.getDailyRmcForSelectedDate(event.target.value)
    );

    $(document).on("change", ".weekly_rmc_start_date", (event) =>
      this.onWeeklyStartDateChange(event.target.value)
    );

    $(document).on("change", ".weekly_rmc_end_date", (event) =>
      this.onWeeklyEndDateChange(event.target.value)
    );
    $(document).on("click", ".print_rmc_report", () => this.generateReport());
  }

  showDailyReport() {
    $(".daily_report_date").show();
    $(".daily_report_container").show();
    $(".weekly_report_date").hide();
  }

  showWeeklyReport() {
    $(".daily_report_date").hide();
    $(".daily_report_container").hide();
    $(".weekly_report_date").show();
  }

  getDailyRmcForSelectedDate(selectedDate) {
    $.ajax({
      url: "/get_daily_rmc_selected_date",
      method: "GET",
      async: true,
      data: { date: selectedDate },

      success: (response) => {
        console.log("AJAX request successful");
        this.updateDailyRmcContainer(response);
      },
      error: (xhr, status, error) => {
        console.error("AJAX request failed");
        console.error(`Status: ${status}`);
        console.error(`Error: ${error}`);
      },
    });
  }

  generateReport() {
    if ($(".daily_report_date").is(":visible")) {
      const selectedDate = $(".daily_rmc_date").val();
      $.ajax({
        url: "/print_rmc_daily_report",
        method: "GET",
        data: { date: selectedDate },
        xhrFields: {
          responseType: "blob",
        },
        success: (response) => {
          var blob = new Blob([response], { type: "application/pdf" });
          var url = window.URL.createObjectURL(blob);
          var newWindow = window.open(url);
          if (newWindow) {
            newWindow.focus();
          } else {
            alert("Please allow popups for this website");
          }
        },
        error: (xhr, status, error) => {
          console.error("AJAX request failed");
          console.error(`Status: ${status}`);
          console.error(`Error: ${error}`);
        },
      });
    } else if ($(".daily_report_date").is(":hidden")) {
      const endDate = $(".weekly_rmc_end_date").val();
      const startDate = $(".weekly_rmc_start_date").val();
      $.ajax({
        url: "/print_rmc_weekly_report",
        method: "GET",
        data: { start_date: startDate, end_date: endDate },
        success: (response) => {
          console.log("AJAX request successful");
          //this.updateDailyRmcContainer(response);
        },
        error: (xhr, status, error) => {
          console.error("AJAX request failed");
          console.error(`Status: ${status}`);
          console.error(`Error: ${error}`);
        },
      });
    }
  }

  updateDailyRmcContainer(response) {
    if (response.FOUND) {
      $(".daily_report_container").css("visibility", "visible");
      $(".weekly_report_container").css("visibility", "hidden");
      $(".daily_report_table_cash tbody").empty();
      $(".daily_report_table_credit tbody").empty();

      const data = response.result;
      if (data.length === 0) {
        $(".daily_report_container").css("visibility", "hidden");
      } else {
        let tableHTMLCash = "<tbody>";
        let tableHTMLCredit = "<tbody>";

        data.forEach((item) => {
          const row = `
              <tr>
                  <td>${item.entry_id}</td>
                  <td>${item.bags}/-</td>
                  <td>${item.paid_amount}</td>
                  <td>${item.rmc}</td>
              </tr>`;
          if (item.payment_type === "credit") {
            tableHTMLCredit += row;
          } else {
            tableHTMLCash += row;
          }
        });

        tableHTMLCash += "</tbody>";
        tableHTMLCredit += "</tbody>";

        $(".daily_report_table_cash").append(tableHTMLCash);
        $(".daily_report_table_credit").append(tableHTMLCredit);
      }
    } else {
      $(".daily_report_container").css("visibility", "hidden");
      $(".daily_report_table_cash tbody").empty();
      $(".daily_report_table_credit tbody").empty();
    }
  }

  onWeeklyStartDateChange(startDate) {
    const endDate = $(".weekly_rmc_end_date").val();
    if (!endDate) {
      console.warn("The EndDate value is undefined");
    } else {
      this.getWeeklyRmcForSelectedDate(startDate, endDate);
    }
  }

  onWeeklyEndDateChange(endDate) {
    const startDate = $(".weekly_rmc_start_date").val();
    if (!startDate) {
      console.warn("The StartDate value is undefined");
    } else {
      this.getWeeklyRmcForSelectedDate(startDate, endDate);
    }
  }

  getWeeklyRmcForSelectedDate(startDate, endDate) {
    $.ajax({
      url: "/get_daily_rmc_start_and_end_date",
      method: "GET",
      async: true,
      data: { start_date: startDate, end_date: endDate },
      success: (response) => {
        console.log("AJAX request successful");
        this.updateWeeklyRmcContainer(response);
      },
      error: (xhr, status, error) => {
        console.error("AJAX request failed");
        console.error(`Status: ${status}`);
        console.error(`Error: ${error}`);
      },
    });
  }

  updateWeeklyRmcContainer(response) {
    if (response.FOUND) {
      $(".daily_report_container").hide();
      $(".weekly_report_container").show();
      $(".weekly_rmc_report_table tbody").empty();

      const data = response.result;
      let tableHTML = "<tbody>";

      data.forEach((item) => {
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
}

// Initialize the RmcReportManager
$(document).ready(() => {
  new RmcReportManager();
});
