# Release checklist

1. Review the diff for secrets, private samples, and generated data.
2. Run the frontend production build and API offline and HTTP checks.
3. Run the Docker smoke check using disposable data.
4. Test a text upload, binary upload, cited query, and unavailable provider.
5. Confirm environment documentation matches the application.
6. Record user-visible changes and any data migration or index rebuild steps.
7. Create a version tag only after checks pass, recording the exact commit and known limitations.

Do not describe unrun checks as passing. Preserve backups before changing persistent data formats.
