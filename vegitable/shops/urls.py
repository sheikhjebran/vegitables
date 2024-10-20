from django.urls import path

from . import views

urlpatterns = [
    # webpage URL
    path('', views.index, name="index"),

    # Dashboard Authentication
    path('authenticate', views.get_authenticate, name="get_authenticate"),
    path('logout', views.logout, name="logout"),

    # dashboard URL
    path('home', views.home, name='home'),
    path('home/prev/<int:page_number>',
         views.home_prev_page, name="home_prev_page"),
    path('home/next/<int:page_number>',
         views.home_next_page, name="home_next_page"),

    # Arrival Entry URL
    path('add_arrival_entry', views.add_new_arrival_entry,
         name='add_new_arrival_entry'),
    path('add_arrival', views.add_arrival, name='add_arrival'),
    path('edit_arrival_entry/<int:arrival_id>',
         views.modify_arrival, name='modify_arrival'),

    # RestAPI
    path('get_arrival_goods_item_name', views.get_arrival_goods_item_name,
         name='get_arrival_goods_item_name'),
    path('get_arrival_goods_list', views.get_arrival_goods_list,
         name='get_arrival_goods_list'),
    path('get_arrival_goods_api', views.get_arrival_goods_api,
         name='get_arrival_goods_api'),
    path('get_arrival_duplicate_validation_api', views.get_arrival_duplicate_validation_api,
         name='get_arrival_duplicate_validation_api'),

    # Profile URL
    path('profile', views.profile, name='profile'),

    # expenditure_entry Entry URL
    path('expenditure_entry', views.expenditure_entry, name='expenditure_entry'),
    path('add_expenditure', views.add_expenditure_entry,
         name='add_expenditure_entry'),
    path('edit_expense/<int:expenditure_id>',
         views.edit_expense, name='edit_expense'),
    path('delete_expense/<int:expenditure_id>',
         views.delete_expense, name='delete_expense'),

    # Sales Entry URL
    path('sales_bill_entry', views.sales_bill_entry, name='sales_bill_entry'),
    path('sales_bill/prev/<int:page_number>',
         views.sales_bill_prev_page, name="sales_bill_prev_page"),
    path('sales_bill/next/<int:page_number>',
         views.sales_bill_next_page, name="sales_bill_next_page"),
    path('navigate_to_add_sales_bill_entry', views.navigate_to_add_sales_bill_entry,
         name='navigate_to_add_sales_bill_entry'),
    path('add_sales_bill', views.modify_sales_bill_entry,
         name='modify_sales_bill_entry'),
    path('edit_sales_bill_entry/<int:sales_id>',
         views.edit_sales_bill_entry, name='edit_sales_bill_entry'),

    # Rest Api for sales entry list
    path('get_sales_list_for_arrival_item_list', views.get_sales_list_for_arrival_item_list,
         name='get_sales_list_for_arrival_item_list'),

    # patti Entry URL
    path('patti_list', views.patti_list, name="patti_list"),
    path('add_new_patti_entry', view=views.add_new_patti_entry,
         name='add_new_patti_entry'),
    path('generate_patti_pdf_bill', view=views.generate_patti_pdf_bill,
         name='generate_patti_pdf_bill'),
    path('edit_patti_entry/<int:patti_id>',
         views.edit_patti_entry, name='edit_patti_entry'),

    # Rest Api for the patti
    path('get_all_lorry_number/<str:lorry_date>', view=views.get_lorry_number_for_date,
         name='get_lorry_number_for_date'),
    path('get_all_farmer_name', view=views.get_all_farmer_name,
         name='get_all_farmer_name'),

    # Report
    path('report', views.report, name='report'),
    path('sales_bill_report', views.sales_bill_report, name='sales_bill_report'),
    path('report_sales_bill', views.report_sales_bill, name='report_sales_bill'),
    path('generate_sales_bill_report', views.generate_sales_bill_report,
         name='generate_sales_bill_report'),
    path('rmc_report', views.rmc_report, name='rmc_report'),

    # Customer Ledger
    path('customer_ledger', views.customer_ledger, name='customer_ledger'),
    path('add_customer_ledger', views.add_customer_ledger,
         name='add_customer_ledger'),
    path('search_customer_ledger', views.search_customer_ledger,
         name='search_customer_ledger'),
    path('default_customer_ledger', views.default_customer_ledger,
         name='default_customer_ledger'),
    path('customer_ledger/prev/<int:page_number>',
         views.customer_ledger_prev_page, name="customer_ledger_prev_page"),
    path('customer_ledger/next/<int:page_number>',
         views.customer_ledger_next_page, name="customer_ledger_next_page"),
    path('edit_customer_ledger/<int:customer_id>',
         views.edit_customer_ledger, name='edit_customer_ledger'),
    path('delete_customer_ledger/<int:customer_id>',
         views.delete_customer_ledger, name='delete_customer_ledger'),

    # Farmer Ledger
    path('farmer_ledger', views.farmer_ledger, name='farmer_ledger'),
    path('add_farmer_ledger', views.add_farmer_ledger, name='add_farmer_ledger'),
    path('search_farmer_ledger', views.search_farmer_ledger,
         name='search_farmer_ledger'),
    path('default_farmer_ledger', views.default_farmer_ledger,
         name='default_farmer_ledger'),
    path('farmer_ledger/prev/<int:page_number>',
         views.farmer_ledger_prev_page, name="farmer_ledger_prev_page"),
    path('farmer_ledger/next/<int:page_number>',
         views.farmer_ledger_next_page, name="farmer_ledger_next_page"),
    path('edit_farmer_ledger/<int:farmer_id>',
         views.edit_farmer_ledger, name='edit_farmer_ledger'),
    path('delete_farmer_ledger/<int:farmer_id>',
         views.delete_farmer_ledger, name='delete_farmer_ledger'),

    # Inventory
    path('inventory', views.inventory, name='inventory'),
    path('inventory/prev/<int:page_number>',
         views.inventory_prev_page, name="inventory_prev_page"),
    path('inventory/next/<int:page_number>',
         views.inventory_next_page, name="inventory_next_page"),

    # Credit Bill Entry
    path('credit_bill_entry', views.credit_bill_entry, name="credit_bill_entry"),
    path('search_credit', views.search_credit, name="search_credit"),
    path('add_credit_bill_amount', views.add_new_credit_bill_entry,
         name="add_new_credit_bill_entry"),
    path('get_credit_bill_entry_list', views.get_credit_bill_entry_list,
         name="get_credit_bill_entry_list"),

    # Shilk Entry
    path('shilk_entry', views.shilk_entry, name="shilk_entry"),
    path('retrieve_shilk', views.retrieve_shilk, name="retrieve_shilk"),

    # RMC
    path('get_daily_rmc_selected_date', views.get_daily_rmc_selected_date,
         name="get_daily_rmc_selected_date"),
    path('get_daily_rmc_start_and_end_date', views.get_daily_rmc_start_and_end_date,
         name="get_daily_rmc_start_and_end_date")
]
