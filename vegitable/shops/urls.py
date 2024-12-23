from django.urls import path

from . import views
from .shop_views import (
    arrival_view,
    patti_view,
    settings_view,
    expenditure_view,
    shilk_view,
    credit_bill_view,
    farmer_ledger_view,
    customer_ledger_view)
from .shop_views.mobile import login

urlpatterns = [
    # webpage URL
    path('', views.index, name="index"),

    # Dashboard Authentication
    path('authenticate', arrival_view.get_authenticate, name="get_authenticate"),
    path('logout', views.logout, name="logout"),

    # dashboard URL
    path('home', arrival_view.home, name='home'),
    path('home/prev/<int:page_number>',
         arrival_view.home_prev_page, name="home_prev_page"),
    path('home/next/<int:page_number>',
         arrival_view.home_next_page, name="home_next_page"),

    # Arrival Entry URL
    path('add_arrival_entry', arrival_view.add_new_arrival_entry,
         name='add_new_arrival_entry'),
    path('add_arrival', arrival_view.add_arrival, name='add_arrival'),
    path('edit_arrival_entry/<int:arrival_id>',
         arrival_view.modify_arrival, name='modify_arrival'),

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
    path('expenditure_entry', expenditure_view.expenditure_entry,
         name='expenditure_entry'),
    path('add_expenditure', expenditure_view.add_expenditure_entry,
         name='add_expenditure_entry'),
    path('edit_expense/<int:expenditure_id>',
         expenditure_view.edit_expense, name='edit_expense'),
    path('delete_expense/<int:expenditure_id>',
         expenditure_view.delete_expense, name='delete_expense'),
    path('fetch_expenditures/', expenditure_view.fetch_expenditures,
         name='fetch_expenditures'),

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
    path('patti_list', patti_view.patti_list, name="patti_list"),
    path('add_new_patti_entry', view=patti_view.add_new_patti_entry,
         name='add_new_patti_entry'),
    path('generate_patti_pdf_bill', view=patti_view.generate_patti_pdf_bill,
         name='generate_patti_pdf_bill'),
    path('edit_patti_entry/<int:patti_id>',
         patti_view.edit_patti_entry, name='edit_patti_entry'),


    # Rest Api for the patti
    path('get_all_lorry_number/<str:lorry_date>', view=views.get_lorry_number_for_date,
         name='get_lorry_number_for_date'),
    path('get_all_farmer_name', view=views.get_all_farmer_name,
         name='get_all_farmer_name'),

    # Report
    path('report', views.report, name='report'),
    path('sales_bill_report', views.sales_bill_report,
         name='sales_bill_report'),
    path('report_sales_bill', views.report_sales_bill,
         name='report_sales_bill'),
    path('generate_sales_bill_report', views.generate_sales_bill_report,
         name='generate_sales_bill_report'),
    path('rmc_report', views.rmc_report, name='rmc_report'),

    # Customer Ledger
    path('customer_ledger', customer_ledger_view.customer_ledger,
         name='customer_ledger'),
    path('add_customer_ledger', customer_ledger_view.add_customer_ledger,
         name='add_customer_ledger'),
    path('search_customer_ledger', customer_ledger_view.search_customer_ledger,
         name='search_customer_ledger'),
    path('default_customer_ledger', customer_ledger_view.default_customer_ledger,
         name='default_customer_ledger'),
    path('customer_ledger/prev/<int:page_number>',
         customer_ledger_view.customer_ledger_prev_page, name="customer_ledger_prev_page"),
    path('customer_ledger/next/<int:page_number>',
         customer_ledger_view.customer_ledger_next_page, name="customer_ledger_next_page"),
    path('edit_customer_ledger/<int:customer_id>',
         customer_ledger_view.edit_customer_ledger, name='edit_customer_ledger'),
    path('delete_customer_ledger/<int:customer_id>',
         customer_ledger_view.delete_customer_ledger, name='delete_customer_ledger'),

    # Farmer Ledger
    path('farmer_ledger', farmer_ledger_view.farmer_ledger, name='farmer_ledger'),
    path('add_farmer_ledger', farmer_ledger_view.add_farmer_ledger,
         name='add_farmer_ledger'),
    path('search_farmer_ledger', farmer_ledger_view.search_farmer_ledger,
         name='search_farmer_ledger'),
    path('default_farmer_ledger', farmer_ledger_view.default_farmer_ledger,
         name='default_farmer_ledger'),
    path('farmer_ledger/prev/<int:page_number>',
         farmer_ledger_view.farmer_ledger_prev_page, name="farmer_ledger_prev_page"),
    path('farmer_ledger/next/<int:page_number>',
         farmer_ledger_view.farmer_ledger_next_page, name="farmer_ledger_next_page"),
    path('edit_farmer_ledger/<int:farmer_id>',
         farmer_ledger_view.edit_farmer_ledger, name='edit_farmer_ledger'),
    path('delete_farmer_ledger/<int:farmer_id>',
         farmer_ledger_view.delete_farmer_ledger, name='delete_farmer_ledger'),

    # Inventory
    path('inventory', views.inventory, name='inventory'),
    path('inventory/prev/<int:page_number>',
         views.inventory_prev_page, name="inventory_prev_page"),
    path('inventory/next/<int:page_number>',
         views.inventory_next_page, name="inventory_next_page"),

    # Credit Bill Entry
    path('credit_bill_entry', credit_bill_view.credit_bill_entry,
         name="credit_bill_entry"),
    path('search_credit', credit_bill_view.search_credit, name="search_credit"),
    path('add_credit_bill_amount', credit_bill_view.add_new_credit_bill_entry,
         name="add_new_credit_bill_entry"),
    path('get_credit_bill_entry_list', credit_bill_view.get_credit_bill_entry_list,
         name="get_credit_bill_entry_list"),

    # Shilk Entry
    path('shilk_entry', shilk_view.shilk_entry, name="shilk_entry"),
    path('retrieve_shilk', shilk_view.retrieve_shilk, name="retrieve_shilk"),

    # RMC
    path('get_daily_rmc_selected_date', views.get_daily_rmc_selected_date,
         name="get_daily_rmc_selected_date"),
    path('get_daily_rmc_start_and_end_date', views.get_daily_rmc_start_and_end_date,
         name="get_daily_rmc_start_and_end_date"),

    # Settings
    path('settings', settings_view.navigate_to_settings, name="settings"),
    path('update_prefix', settings_view.update_prefix, name="update_prefix"),


    # flutter login
    path('login', login.UserLoginView.as_view(), name='login')

]
