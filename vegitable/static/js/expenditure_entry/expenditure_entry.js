// expenditure.js

class ExpenditureSearch {
    constructor() {
        this.searchButton = document.getElementById('search_date');
        this.tableBody = document.querySelector('#tableWrapper tbody');
        this.init();
    }

    // Initialize event listeners
    init() {
        this.searchButton.addEventListener('change', this.handleDateChange.bind(this));
    }

    // Handle the date change event
    handleDateChange() {
        const selectedDate = this.searchButton.value;

        if (selectedDate) {
            this.fetchData(selectedDate);
        }
    }

    // Fetch data from the server using AJAX
    fetchData(date) {
        $.ajax({
            url: '/fetch_expenditures/',  // Replace with the URL to your Django view
            method: 'GET',
            data: { search_date: date },
            success: (response) => {
                this.displayResults(response);
            },
            error: (error) => {
                console.error('Error fetching data:', error);
            }
        });
    }

    // Display the results dynamically in the table
    displayResults(data) {
        // Clear previous results
        this.tableBody.innerHTML = '';

        if (data.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="5">No results found for the selected date.</td>';
            this.tableBody.appendChild(row);
            return;
        }

        // Populate the table with the new data
        data.forEach((item, index) => {
            const row = document.createElement('tr');

            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${item.date}</td>
                <td>${item.expense_type}</td>
                <td>${item.amount}</td>
                <td>${item.remark}</td>
                <td>
                    <input
                        type="button"
                        value="Edit"
                        class="edit_button"
                        onclick="location.href = '/edit_expense/${item.id}';"
                    />&nbsp;
                    <input
                        type="button"
                        value="Delete"
                        class="delete_button"
                        onclick="location.href = '/delete_expense/${item.id}';"
                    />
                </td>
            `;

            this.tableBody.appendChild(row);
        });
    }
}


// Initialize the ExpenditureSearch class
document.addEventListener('DOMContentLoaded', () => {
    new ExpenditureSearch();
});
