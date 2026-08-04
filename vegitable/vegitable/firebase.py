from django.conf import settings
from django_firebase_orm import initialize_firebase
from firebase_admin import firestore, get_app


def initialize_project_firebase():
    initialize_firebase(
        cred_path=settings.FIREBASE_CREDENTIAL_PATH,
        options=settings.FIREBASE_OPTIONS,
    )
    return get_app()


def get_firestore_client():
    initialize_project_firebase()
    return firestore.client(app=get_app())


def describe_firebase_configuration():
    return {
        'enabled': settings.FIREBASE_ENABLED,
        'auto_init': settings.FIREBASE_AUTO_INIT,
        'mobile_sales_enabled': settings.USE_FIREBASE_MOBILE_SALES,
        'credential_path': settings.FIREBASE_CREDENTIAL_PATH,
        'web_config_path': settings.FIREBASE_WEB_CONFIG_PATH,
        'web_config_project_id': settings.FIREBASE_WEB_CONFIG.get('projectId', ''),
        'project_id': settings.FIREBASE_PROJECT_ID,
    }