from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from vegitable.firebase import (
    describe_firebase_configuration,
    get_firestore_client,
    initialize_project_firebase,
)


class Command(BaseCommand):
    help = 'Initialize Firebase and perform a basic Firestore connectivity check.'

    def handle(self, *args, **options):
        configuration = describe_firebase_configuration()
        try:
            app = initialize_project_firebase()
            client = get_firestore_client()
            first_collection = next(client.collections(), None)
        except StopIteration:
            first_collection = None
            client = get_firestore_client()
            app = initialize_project_firebase()
        except Exception as exc:
            if configuration['web_config_project_id'] and not configuration['credential_path']:
                raise CommandError(
                    'Firebase web config was found, but backend admin credentials are still missing. '
                    'The repo-root firebase.json provides project metadata only. '
                    'Add a Firebase service account JSON file and set FIREBASE_CREDENTIAL_PATH in vegitable/.env, '
                    'or configure Google Application Default Credentials for this machine, then rerun check_firebase.'
                ) from exc
            raise CommandError(str(exc)) from exc

        project_id = getattr(client, 'project', None) or getattr(app, 'project_id', None) or 'unknown'
        credential_source = settings.FIREBASE_CREDENTIAL_PATH or 'application default credentials'

        self.stdout.write(self.style.SUCCESS(
            f"Firebase initialized successfully for project '{project_id}'."
        ))
        self.stdout.write(
            f'FIREBASE_ENABLED={settings.FIREBASE_ENABLED} FIREBASE_AUTO_INIT={settings.FIREBASE_AUTO_INIT}'
        )
        self.stdout.write(f"FIREBASE_WEB_CONFIG_PATH={configuration['web_config_path']}")
        self.stdout.write(f'Credential source: {credential_source}')
        if first_collection is None:
            self.stdout.write('Collection listing succeeded; no collections were found.')
        else:
            self.stdout.write(f'First collection: {first_collection.id}')