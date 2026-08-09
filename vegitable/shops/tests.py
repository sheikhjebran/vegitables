from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings

from shops.models import CustomerLedger, FarmerLedger, Shop
from shops.repositories.customer_ledger_repository import CustomerLedgerRepository
from shops.repositories.farmer_ledger_repository import FarmerLedgerRepository
from shops.shop_views import credit_bill_view, customer_ledger_view, patti_view


def _attach_session(request):
	middleware = SessionMiddleware(lambda req: None)
	middleware.process_request(request)
	request.session.save()


class ShopIsolationViewTests(TestCase):
	def setUp(self):
		self.factory = RequestFactory()
		self.user = User.objects.create_user(username='viewer', password='pass1234')

	@patch('shops.shop_views.customer_ledger_view.customer_ledger_repository.get_by_id')
	@patch('shops.shop_views.customer_ledger_view._load_shop_metadata')
	def test_edit_customer_ledger_rejects_cross_shop_record(self, mock_load_shop_metadata, mock_get_by_id):
		mock_load_shop_metadata.return_value = SimpleNamespace(pk=1)
		mock_get_by_id.return_value = SimpleNamespace(id='abc', shop_id=2)

		request = self.factory.get('/edit_customer_ledger/abc')
		request.user = self.user
		_attach_session(request)

		response = customer_ledger_view.edit_customer_ledger(request, 'abc')

		self.assertEqual(response.status_code, 403)

	@patch('shops.shop_views.customer_ledger_view.customer_ledger_repository.get_by_id')
	@patch('shops.shop_views.customer_ledger_view.customer_ledger_repository.delete')
	@patch('shops.shop_views.customer_ledger_view._load_shop_metadata')
	def test_delete_customer_ledger_rejects_cross_shop_record(self, mock_load_shop_metadata, mock_delete, mock_get_by_id):
		mock_load_shop_metadata.return_value = SimpleNamespace(pk=1)
		mock_get_by_id.return_value = SimpleNamespace(id='abc', shop_id=2)

		request = self.factory.get('/delete_customer_ledger/abc')
		request.user = self.user
		_attach_session(request)

		response = customer_ledger_view.delete_customer_ledger(request, 'abc')

		self.assertEqual(response.status_code, 403)
		mock_delete.assert_not_called()

	@patch('shops.shop_views.credit_bill_view._credit_workflow_requires_firebase', return_value=True)
	@patch('shops.shop_views.credit_bill_view.sales_bill_repository.get_by_id')
	@patch('shops.shop_views.credit_bill_view._load_shop_metadata')
	def test_add_credit_bill_rejects_cross_shop_sales_bill(self, mock_load_shop_metadata, mock_get_sales, _mock_workflow):
		mock_load_shop_metadata.return_value = SimpleNamespace(pk=1)
		mock_get_sales.return_value = SimpleNamespace(
			id='sales-1',
			shop_id=2,
			sales_bill_id='SB1',
			payment_type='credit',
			customer_name='Cust',
			date='2026-01-01',
			rmc=0.0,
			commission=0.0,
			cooli=0.0,
			total_amount=100.0,
			paid_amount=0.0,
			balance_amount=100.0,
			empty_data=False,
			items=[],
		)

		request = self.factory.post('/add_credit_bill_amount', data={
			'credit_bill_balance_amount': '100',
			'credit_bill_sales_bill_id': 'sales-1',
			'credit_bill_payment_option': 'cash',
			'credit_bill_amount_received': '10',
			'credit_bill_discount': '0',
		})
		request.user = self.user
		_attach_session(request)

		response = credit_bill_view.add_new_credit_bill_entry(request)

		self.assertEqual(response.status_code, 403)

	@patch('shops.shop_views.patti_view.sales_bill_repository.using_firebase', return_value=True)
	@patch('shops.shop_views.patti_view.arrival_repository.using_firebase', return_value=True)
	@patch('shops.shop_views.patti_view.arrival_repository.get_by_id')
	@patch('shops.shop_views.patti_view._load_shop_metadata')
	def test_patti_sales_lookup_rejects_cross_shop_arrival(
		self,
		mock_load_shop_metadata,
		mock_get_arrival,
		_mock_arrival_enabled,
		_mock_sales_enabled,
	):
		mock_load_shop_metadata.return_value = SimpleNamespace(pk=1)
		mock_get_arrival.return_value = SimpleNamespace(id='arr-1', shop_id=2, goods=[])

		request = self.factory.get('/get_sales_list_for_arrival_item_list', data={
			'patti_lorry': 'arr-1',
			'patti_farmer': 'farmer-a',
		})
		request.user = self.user
		_attach_session(request)

		response = patti_view.get_sales_list_for_arrival_item_list(request)

		self.assertEqual(response.status_code, 403)


@override_settings(FIREBASE_ENABLED=False, USE_FIREBASE_CUSTOMER_LEDGER=False, USE_FIREBASE_FARMER_LEDGER=False)
class LedgerDuplicateScopeTests(TestCase):
	def setUp(self):
		owner1 = User.objects.create_user(username='owner1', password='pass1234')
		owner2 = User.objects.create_user(username='owner2', password='pass1234')
		self.shop1 = Shop.objects.create(shop_name='Shop 1', shop_location='Loc 1', shop_address='Addr 1', shop_owner=owner1)
		self.shop2 = Shop.objects.create(shop_name='Shop 2', shop_location='Loc 2', shop_address='Addr 2', shop_owner=owner2)

	def test_customer_duplicate_check_is_scoped_per_shop(self):
		CustomerLedger.objects.create(shop=self.shop1, name='A', contact='9999', address='X')
		repository = CustomerLedgerRepository()

		self.assertTrue(repository.exists_by_contact(shop_id=self.shop1.id, contact='9999'))
		self.assertFalse(repository.exists_by_contact(shop_id=self.shop2.id, contact='9999'))

	def test_farmer_duplicate_check_is_scoped_per_shop(self):
		FarmerLedger.objects.create(shop=self.shop1, name='B', contact='8888', place='Y')
		repository = FarmerLedgerRepository()

		self.assertTrue(repository.exists_by_contact(shop_id=self.shop1.id, contact='8888'))
		self.assertFalse(repository.exists_by_contact(shop_id=self.shop2.id, contact='8888'))
