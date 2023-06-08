from django.urls import path

from . import views

urlpatterns = [
    # webpage URL
    path('', views.index, name="index"),

    # Dashboard Authentication
    path('authenticate', views.get_authenticate, name="get_authenticate"),
    path('logout', views.logout, name="logout"),
    # Api to get Authenticated
    path('authenticate_api', views.get_authenticate_api, name="get_authenticate_api"),

    # dashboard URL
    path('home', views.home, name='home'),
    path('home/prev/<int:page_number>', views.home_prev_page, name="home_prev_page"),
    path('home/next/<int:page_number>', views.home_next_page, name="home_next_page"),

    # Arrival Entry URL
    path('add_arrival_entry', views.add_new_arrival_entry, name='add_new_arrival_entry'),
    path('add_arrival', views.add_arrival, name='add_arrival'),
    path('edit_arrival_entry/<int:arrival_id>', views.modify_arrival, name='modify_arrival'),
    # RestAPI
    path('get_arrival_goods_iteam_name', views.get_arrival_goods_iteam_name, name='get_arrival_goods_iteam_name'),
    path('get_arrival_goods_list', views.get_arrival_goods_list, name='get_arrival_goods_list'),
    path('get_arrival_goods_api', views.get_arrival_goods_api, name='get_arrival_goods_api'),
    path('get_arrival_duplicate_validation_api', views.get_arrival_duplicate_validation_api,
         name='get_arrival_duplicate_validation_api'),

    # Profile URL
    path('profile', views.profile, name='profile'),

    # Misc Entry URL
    path('misc_entry', views.misc_entry, name='misc_entry'),
    path('misc/prev/<int:page_number>', views.misc_prev_page, name="misc_prev_page"),
    path('misc/next/<int:page_number>', views.misc_next_page, name="misc_next_page"),
    path('add_misc_entry', views.add_new_misc_entry, name='add_new_misc_entry'),
    path('add_misc', views.add_misc_entry, name='add_misc_entry'),
    path('edit_misc_entry/<int:misc_id>', views.edit_misc_entry, name='edit_misc_entry'),
    path('misc_total_iframe', views.total_amount_misc_entry, name='total_amount_misc_entry'),

    # Sales Entry URL
    path('sales_bill_entry', views.sales_bill_entry, name='sales_bill_entry'),
    path('sales_bill/prev/<int:page_number>', views.sales_bill_prev_page, name="sales_bill_prev_page"),
    path('sales_bill/next/<int:page_number>', views.sales_bill_next_page, name="sales_bill_next_page"),
    path('navigate_to_add_sales_bill_entry', views.navigate_to_add_sales_bill_entry,
         name='navigate_to_add_sales_bill_entry'),
    path('add_sales_bill', views.modify_sales_bill_entry, name='modify_sales_bill_entry'),
    path('edit_sales_bill_entry/<int:sales_id>', views.edit_sales_bill_entry, name='edit_sales_bill_entry'),

    # Rest Api for sales entry list
    path('get_sales_list_for_arrival_iteam_list', views.get_sales_list_for_arrival_iteam_list,
         name='get_sales_list_for_arrival_iteam_list'),

    # patti Entry URL
    path('patti_list', views.patti_list, name="patti_list"),
    path('add_new_patti_entry', view=views.add_new_patti_entry, name='add_new_patti_entry'),
    path('generate_patti_pdf_bill', view=views.generate_patti_pdf_bill, name='generate_patti_pdf_bill'),
    path('edit_patti_entry/<int:patti_id>', views.edit_patti_entry, name='edit_patti_entry'),

    # Rest Api for the patti
    path('get_all_lorry_number/<str:lorry_date>', view=views.get_lorry_number_for_date,
         name='get_lorry_number_for_date'),
    path('get_all_farmer_name', view=views.get_all_farmer_name, name='get_all_farmer_name'),

    # Report
    path('report', views.report, name='report'),

    # Customer Ledger
    path('customer_ledger', views.customer_ledger, name='customer_ledger'),
    path('add_customer_ledger', views.add_customer_ledger, name='add_customer_ledger'),
    path('search_customer_ledger', views.search_customer_ledger, name='search_customer_ledger'),
    path('customer_ledger/prev/<int:page_number>', views.customer_ledger_prev_page, name="customer_ledger_prev_page"),
    path('customer_ledger/next/<int:page_number>', views.customer_ledger_next_page, name="customer_ledger_next_page"),
]
