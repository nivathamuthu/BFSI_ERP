from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from claims.models import Claim
from compliance.models import ComplianceReport, ComplianceRule
from core.constants import PolicyType, UserRole
from core.models import User
from customers.models import Customer
from documents.models import Document
from finance.models import Invoice, Transaction
from finance.services import customer_outstanding
from identity.models import IdentityVerificationRequest
from identity.services import verify_identity
from policies.models import Policy
from underwriting.models import UnderwritingRequest

PDF_BYTES = b"%PDF-1.1\n1 0 obj<< /Type /Catalog >>endobj\ntrailer<<>>\n%%EOF\n"

DEMO_USERS = (
    ("admin", "admin@bfsi-erp.local", "OpsLead123!", UserRole.ADMIN, True),
    ("underwriter", "underwriter@bfsi-erp.local", "RiskDesk123!", UserRole.UNDERWRITER, False),
    ("adjuster", "adjuster@bfsi-erp.local", "ClaimsDesk123!", UserRole.CLAIMS_ADJUSTER, False),
)


class Command(BaseCommand):
    help = "Load a small insurance book so the API has a story to click through."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete previously seeded customers and their records, then load them again.",
        )

    def handle(self, *args, **options):
        if Customer.objects.exists() and not options["reset"]:
            self.stdout.write(self.style.WARNING("Demo data already exists. Re-run with --reset to reload it."))
            return

        with transaction.atomic():
            if options["reset"]:
                self._wipe()
            self._users()
            self._book()

    def _wipe(self):
        for document in Document.objects.all():
            if document.file:
                document.file.delete(save=False)
        Document.objects.all().delete()
        Claim.objects.all().delete()
        Transaction.objects.all().delete()
        Invoice.objects.all().delete()
        Policy.objects.all().delete()
        UnderwritingRequest.objects.all().delete()
        IdentityVerificationRequest.objects.all().delete()
        ComplianceReport.objects.all().delete()
        ComplianceRule.objects.all().delete()
        Customer.objects.all().delete()

    def _users(self):
        for username, email, password, role, is_superuser in DEMO_USERS:
            user, _created = User.objects.get_or_create(username=username, defaults={"email": email, "role": role})
            user.email = email
            user.role = role
            user.is_superuser = is_superuser
            user.set_password(password)
            user.save()

    def _book(self):
        today = timezone.localdate()
        asha = Customer.objects.create(
            name="Asha Rao",
            email="asha.rao@example.com",
            phone="+919876543210",
            address="12 MG Road, Bengaluru",
        )
        rohan = Customer.objects.create(
            name="Rohan Mehta",
            email="rohan.mehta@example.com",
            phone="+919800011122",
            address="44 Linking Road, Mumbai",
        )

        asha_uw = UnderwritingRequest.objects.create(
            customer=asha,
            policy_type=PolicyType.HEALTH,
            details="Age 34, non-smoker, no hospitalization in the last three years.",
            status=UnderwritingRequest.Status.APPROVED,
        )
        UnderwritingRequest.objects.create(
            customer=rohan,
            policy_type=PolicyType.MOTOR,
            details="Private car, 2019 model, one at-fault claim five years ago. Waiting on garage report.",
            status=UnderwritingRequest.Status.SUBMITTED,
        )

        asha_policy = Policy.objects.create(
            customer=asha,
            underwriting_request=asha_uw,
            type=PolicyType.HEALTH,
            start_date=today - timedelta(days=200),
            end_date=today + timedelta(days=160),
            premium_amount="12000.00",
            status=Policy.Status.ACTIVE,
        )
        Policy.objects.create(
            customer=rohan,
            type=PolicyType.MOTOR,
            start_date=today + timedelta(days=14),
            end_date=today + timedelta(days=379),
            premium_amount="8400.00",
            status=Policy.Status.DRAFT,
        )

        Claim.objects.create(
            policy=asha_policy,
            claimant_name=asha.name,
            claim_date=today - timedelta(days=20),
            description="Two-day hospital stay for a covered procedure.",
            amount="8000.00",
            status=Claim.Status.UNDER_REVIEW,
        )
        Claim.objects.create(
            policy=asha_policy,
            claimant_name="Ravi Rao",
            claim_date=asha_policy.start_date - timedelta(days=15),
            description="High-value claim filed in another person's name, outside the policy period.",
            amount="250000.00",
            status=Claim.Status.INTAKE,
        )

        invoice = Invoice.objects.create(
            customer=asha,
            policy=asha_policy,
            amount="12000.00",
            due_date=today + timedelta(days=20),
            status=Invoice.Status.ISSUED,
        )
        Invoice.objects.create(
            customer=rohan,
            amount="8400.00",
            due_date=today - timedelta(days=15),
            status=Invoice.Status.OVERDUE,
        )
        Transaction.objects.create(
            customer=asha,
            invoice=invoice,
            type=Transaction.Type.PAYMENT,
            amount="2000.00",
            date=today - timedelta(days=5),
            description="Part payment of Asha Rao's health premium.",
        )

        decision, detail = verify_identity("passport", "P1234567")
        IdentityVerificationRequest.objects.create(
            customer=asha,
            document_type=IdentityVerificationRequest.DocumentType.PASSPORT,
            document_number="P1234567",
            status=decision,
            provider="mock",
            result_detail=detail,
        )

        rule = ComplianceRule.objects.create(
            name="KYC before bind",
            description="Do not move a policy to active until identity verification is verified.",
            status=ComplianceRule.Status.ACTIVE,
        )
        ComplianceReport.objects.create(
            rule=rule,
            report_date=today,
            status=ComplianceReport.Status.SUBMITTED,
            details="Asha Rao's passport was accepted by the mock identity check before the health policy was bound.",
        )

        schedule = Document(
            name="Asha Rao health schedule",
            type=Document.DocType.POLICY,
            policy=asha_policy,
            content_type="application/pdf",
            size=len(PDF_BYTES),
        )
        schedule.file.save("asha-health-schedule.pdf", ContentFile(PDF_BYTES), save=True)

        balance = customer_outstanding(asha)
        self.stdout.write(self.style.SUCCESS("Demo book loaded."))
        self.stdout.write("Logins:")
        self.stdout.write("  admin / OpsLead123!          (every desk)")
        self.stdout.write("  underwriter / RiskDesk123!   (customers, underwriting, policies, identity)")
        self.stdout.write("  adjuster / ClaimsDesk123!    (customers, claims, documents)")
        self.stdout.write(
            f"Asha Rao outstanding balance: {balance['outstanding_balance']} "
            f"(open invoices {balance['open_invoice_total']} - payments {balance['payment_total']})"
        )
        self.stdout.write("Open http://127.0.0.1:8000/api/docs/ after runserver.")
