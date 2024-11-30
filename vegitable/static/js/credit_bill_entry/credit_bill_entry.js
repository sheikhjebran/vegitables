class CreditBillManager {
    constructor() {
        this.form = $("#search_credit_record");
        this.tableBody = $("#tableWrapper");
        this.initEventListeners();
    }

    initEventListeners() {
        this.handleFormSubmission();
        this.handlePopupClose();
        this.handleCreditIdClick();
        this.creditAmountEntered();
        this.discountApplied();
        this.showPopUp();
        this.searchCreditRecord();
    }

    creditAmountEntered() {
     $(document).on("input", ".amount_received", () => {
            this.validate_credit_bill_amount_received()
        });
    }

    discountApplied() {
        $(document).on("input", ".discount", () => {
            this.validate_credit_bill_amount_received()
        });
    }

    validate_credit_bill_amount_received(){
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

    searchCreditRecord() {
        this.form.on("submit", (e) => {
            e.preventDefault();
            let formData = this.form.serialize();
            $.ajax({
                url: this.form.attr("action"), // Use the form's action attribute
                type: "GET",
                data: formData,
                headers: {
                    "X-CSRFToken": $("input[name='csrfmiddlewaretoken']").val() // CSRF token
                },
                success: (response) => {
                    if (response.success) {
                        // Update the table body with the new data
                        this.tableBody.html(response.html);
                    } else {
                        alert("Submission failed: " + response.message);
                    }
                },
                error: (xhr, status, error) => {
                    alert("An error occurred: " + error);
                }
            });

        });
    }

    handleFormSubmission() {
        const self = this; // Reference to the current instance
        $("#popup-table").on("submit", function (e) {
            e.preventDefault(); // Prevent the default form submission
            const formData = $(this).serialize();
            // Send the AJAX POST request
            $.ajax({
                url: $(this).attr("action"), // Use the form's action attribute
                type: "POST",
                data: formData,
                headers: {
                    "X-CSRFToken": $("input[name='csrfmiddlewaretoken']").val() // CSRF token
                },
                success: function (response) {
                    self.handleSuccess(response);
                    self.tableBody.html(response.html);
                },
                error: function (xhr, status, error) {
                    self.handleError(xhr, status, error);
                }
            });
        });
    }

    handlePopupClose() {
        $(".popup_close").on("click", () => {
            this.closePopup();
        });
    }

    handleCreditIdClick() {
        $(".credit_id").on("click", (e) => {
            const balance = $(e.currentTarget).attr("amount_balance");
            const billId = $(e.currentTarget).attr("value");
            this.populatePopup(balance, billId);
            this.openPopup();
        });
    }

    populatePopup(balance, billId) {
        $(".balance_amount").val(balance);
        $(".sales_bill_id").val(billId);
    }

    openPopup() {
        $(".overlay").show();
    }

    closePopup() {
        $(".overlay").hide();
    }

    handleSuccess(response) {
        this.closePopup();
        this.searchCreditRecord();
    }

    handleError(xhr, status, error) {
        alert("An error occurred: " + error);
    }

    showPopUp() {
     $(document).on("mouseenter", ".credit_id", function () {
        var text = $(this).attr("value");
        var amount_balance = $(this).attr("amount_balance");
        $("#popup").css({
            'display':"block"
        });

        $(".overlay").css({
            'display':"block"
        });
        $(".sales_bill_id").val(text);
        $(".balance_amount").val(amount_balance);
   });
    }

}


$(document).ready(() => {
    new CreditBillManager();
});
